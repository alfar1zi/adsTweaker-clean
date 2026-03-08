# main.py (FULL FINAL)
# CaptionForge backend: Caption + Image/Cover + Video (semi R2V optional refs)
#
# Endpoints:
# - UI:           GET  /
# - Caption:      POST /generate
# - Image:        POST /image/generate
#                POST /image/edit
#                GET  /image/history?limit=12
#                GET  /image/history/{asset_id}
# - Video:        POST /video/generate
#                GET  /video/status/{task_id}?asset_id=&variant_id=
#                GET  /video/history?limit=12
#                GET  /video/history/{asset_id}
# - Files:        GET  /files/{asset_id}/{variant_id}.png
#                GET  /files/{asset_id}/{variant_id}.mp4
# - Brand upload: POST /brand/upload
#                GET  /brand/{brand_image_id}
# - Video ref:    POST /video/ref/upload (optional demo-only)
#                GET  /video/ref/{ref_filename}
# - Compat alias: GET  /history, /history/{asset_id}  (maps to image history)
#
# Install:
#   pip install fastapi uvicorn httpx python-dotenv pydantic
#
# .env:
#   DASHSCOPE_API_KEY=sk-...
#   DASHSCOPE_MODEL=qwen-plus
#   DASHSCOPE_WAN_IMAGE_MODEL=wan2.6-image
#   DASHSCOPE_VIDEO_MODEL=wan2.6-r2v-flash
#   TEMPERATURE=0.8
#   MAX_TOKENS=1100
#   CACHE_TTL_SECONDS=300
#   DATA_DIR=./data
#
# Run:
#   python -m uvicorn main:app --reload --port 8000

from __future__ import annotations

import os
import json
import time
import uuid
import hashlib
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# =========================
# ENV + CONFIG
# =========================
load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
if not API_KEY or not API_KEY.startswith("sk-"):
    raise RuntimeError("DASHSCOPE_API_KEY missing/invalid. Put it in .env or set in CMD session.")

# Chat (OpenAI compatible)
CHAT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
CHAT_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-plus")

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1100"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# DashScope native async (Wan image + video)
DASH_BASE = "https://dashscope-intl.aliyuncs.com/api/v1"
TASK_URL = f"{DASH_BASE}/tasks"

WAN_IMAGE_CREATE_URL = f"{DASH_BASE}/services/aigc/image-generation/generation"
WAN_IMAGE_MODEL = os.getenv("DASHSCOPE_WAN_IMAGE_MODEL", "wan2.6-image")

VIDEO_CREATE_URL = f"{DASH_BASE}/services/aigc/video-generation/video-synthesis"
VIDEO_MODEL = os.getenv("DASHSCOPE_VIDEO_MODEL", "wan2.6-r2v-flash")

DEFAULT_VIDEO_REF_URL = os.getenv(
    "DEFAULT_VIDEO_REF_URL",
    "https://picsum.photos/seed/captionforge/640/360.jpg"
)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
ASSETS_DIR = DATA_DIR / "assets"
UPLOADS_DIR = DATA_DIR / "uploads"
VIDEO_REFS_DIR = DATA_DIR / "video_refs"
INDEX_PATH = Path(__file__).with_name("index.html")

for p in [DATA_DIR, ASSETS_DIR, UPLOADS_DIR, VIDEO_REFS_DIR]:
    p.mkdir(parents=True, exist_ok=True)


# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="CaptionForge", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# =========================
# REQUEST MODELS
# =========================
class CaptionReq(BaseModel):
    offer: str = Field(..., min_length=10, max_length=1400)
    audience: str = Field(..., min_length=3, max_length=240)
    tone: str = Field("friendly", max_length=40)
    platform: str = Field("IG", max_length=40)      # IG | LinkedIn | TikTok
    language: str = Field("id", max_length=20)      # id | en | bilingual
    price_promo: str = Field("", max_length=220)
    cta_preference: str = Field("", max_length=40)  # "" | DM | link | comment


class ImageReq(BaseModel):
    offer: str = Field(..., min_length=10, max_length=1400)
    audience: str = Field(..., min_length=3, max_length=240)
    platform_style: str = Field("IG", max_length=40)   # IG | LinkedIn | TikTok
    tone: str = Field("friendly", max_length=40)
    language: str = Field("id", max_length=20)         # id | en
    aspect_ratio: str = Field("1:1", max_length=10)    # 1:1 | 4:5 | 9:16 | 16:9
    mode: str = Field("simple", max_length=20)         # simple | creative
    headline: str = Field("", max_length=80)
    subheadline: str = Field("", max_length=120)

    palette_hex: str = Field("", max_length=160)       # "#111111,#FFFFFF,#279CF5,#F97316"
    layout_id: str = Field("L1", max_length=10)        # L1..L4
    include_logo: bool = False
    logo_text: str = Field("", max_length=30)
    brand_image_id: str = Field("", max_length=80)     # optional uploaded id (stored local)


class ImageEditReq(BaseModel):
    asset_id: str = Field(..., min_length=6, max_length=80)
    variant_id: str = Field(..., min_length=6, max_length=80)  # base variant

    tone: str = ""
    language: str = ""
    aspect_ratio: str = ""
    mode: str = ""
    headline: str = ""
    subheadline: str = ""
    palette_hex: str = ""
    layout_id: str = ""
    include_logo: Optional[bool] = None
    logo_text: str = ""
    brand_image_id: str = ""


class VideoReq(BaseModel):
    offer: str = Field(..., min_length=10, max_length=1400)
    audience: str = Field(..., min_length=3, max_length=240)

    platform_style: str = Field("IG", max_length=40)    # IG | LinkedIn | TikTok
    tone: str = Field("friendly", max_length=40)
    language: str = Field("en", max_length=10)          # id | en (video single language)

    format: str = Field("shorts", max_length=20)        # shorts | landscape
    resolution: str = Field("720p", max_length=10)      # 720p | 1080p
    duration_s: int = Field(5, ge=2, le=10)

    mode: str = Field("simple", max_length=20)          # simple | creative
    shot_type: str = Field("multi", max_length=10)      # single | multi
    audio: bool = True

    # Optional references (public URLs only are reliable for the model)
    reference_urls: List[str] = Field(default_factory=list)
    negative_prompt: str = Field("no watermark, no gibberish text, no distorted logo, no extra text", max_length=240)
    palette_hex: str = Field("", max_length=160)
    logo_text: str = Field("", max_length=30)


# =========================
# PROMPTS: CAPTION
# =========================
CAPTION_SYSTEM = """You are an elite direct-response copywriter who writes like a human creator, not an ad.
Output MUST be valid JSON only. No markdown. No backticks. No extra keys.

Rules:
- Simple, clear language. Short sentences. Specific details.
- No fake guarantees. No invented stats.
- Emojis allowed but controlled (max 3 total).
- reply_pack must be an array of 5 separate strings (no \\n).
- Hashtags: IG=exactly 10. LinkedIn/TikTok=[].
"""

def build_caption_user_prompt(req: CaptionReq) -> str:
    plat = req.platform.strip().upper()
    lang = req.language.strip().lower()
    if lang not in ("id", "en", "bilingual"):
        lang = "id"

    promo = req.price_promo.strip()
    promo_rule = f"Promo provided (use exactly): {promo}" if promo else "No promo. Do NOT invent price/discount/deadline."

    cta_pref = req.cta_preference.strip()
    cta_hint = f"CTA preference: {cta_pref}." if cta_pref else "CTA preference: none."

    tag_rule = "Hashtags: EXACTLY 10 (6 global + 4 niche)." if plat == "IG" else "Hashtags: []"

    lang_rule = {
        "id": "Write Indonesian.",
        "en": "Write English.",
        "bilingual": "Return bilingual JSON with keys id and en.",
    }[lang]

    return f"""
TASK: Create a caption pack without sounding like an ad.

INPUT:
- Offer: {req.offer}
- Audience: {req.audience}
- Platform: {req.platform}
- Tone: {req.tone}
- {promo_rule}
- {cta_hint}

Constraints:
- reply_pack: 5 items, each one line, no \\n inside items.
- {tag_rule}

{lang_rule}

Return JSON only with schema:
(A) Single language:
{{
  "platform":"IG|LinkedIn|TikTok",
  "opening_best":"...",
  "opening_options":{{"Relatable":"...","Reframe":"...","Action":"..."}},
  "main_caption":"...",
  "short_caption":"...",
  "cta_options":{{"Soft":"...","Medium":"...","Strong":"..."}},
  "hashtags":[...],
  "reply_pack":["...","...","...","...","..."]
}}

(B) Bilingual:
{{"id":<A>,"en":<A>}}
""".strip()


# =========================
# PROMPTS: IMAGE SPEC + IMAGE PROMPT
# =========================
SPEC_SYSTEM = """You are a creative director for social ads.
Output MUST be valid JSON only. No markdown. No extra text.

Return schema:
{
  "headline":"...",
  "subheadline":"...",
  "cta":"...",
  "badge":"...",
  "palette_hex":["#111111","#FFFFFF","#279CF5"],
  "layout_notes":"...",
  "style_keywords":["...","...","..."]
}

Rules:
- Headline max 6 words. Subheadline max 14 words. CTA max 3 words. Badge max 3 words.
- Must look like real graphic design ad, not AI art.
- Language must match request.
"""

def build_spec_prompt(req: ImageReq) -> str:
    lang = req.language.strip().lower()
    if lang not in ("id", "en"):
        lang = "id"

    mode = req.mode.strip().lower()
    if mode not in ("simple", "creative"):
        mode = "simple"

    base_style = {
        "IG": "modern social ad, bold typography, clean spacing, high readability",
        "LINKEDIN": "professional, minimal, editorial, trustworthy",
        "TIKTOK": "high-contrast, punchy, large type, trend-friendly but clean",
    }.get(req.platform_style.upper(), "modern social ad")

    creativity = "Add a clever visual metaphor, still readable." if mode == "creative" else "Keep it simple, direct, very readable."
    pal = f"Use this palette: {req.palette_hex}" if req.palette_hex.strip() else "Choose a clean 2-3 color palette."

    forced = ""
    if req.headline.strip() or req.subheadline.strip():
        forced += "User provided text. Respect exactly.\n"
        if req.headline.strip():
            forced += f"- Headline exactly: {req.headline.strip()}\n"
        if req.subheadline.strip():
            forced += f"- Subheadline exactly: {req.subheadline.strip()}\n"

    return f"""
Make design spec for a cover ad.

Offer: {req.offer}
Audience: {req.audience}
Platform: {req.platform_style}
Tone: {req.tone}
Language: {lang}
Aspect ratio: {req.aspect_ratio}
Layout id: {req.layout_id}

Style base: {base_style}
Creativity: {creativity}
Palette: {pal}

{forced}

Return JSON only.
""".strip()

def build_image_prompt(req: ImageReq, spec: Dict[str, Any]) -> str:
    layout_map = {
        "L1": "headline top-left, subheadline below, CTA bottom-right",
        "L2": "headline centered, subheadline below, CTA bottom center",
        "L3": "split layout: text left, abstract graphic right, CTA below text",
        "L4": "badge top-right, headline center, CTA bottom-left",
    }
    layout_notes = layout_map.get(req.layout_id, "clean hierarchy layout")

    headline = spec.get("headline", "")
    sub = spec.get("subheadline", "")
    cta = spec.get("cta", "")
    badge = spec.get("badge", "")
    palette = spec.get("palette_hex") or []
    pal_text = ", ".join(palette) if isinstance(palette, list) else ""

    style_line = "Minimal, conversion-focused, very readable." if req.mode == "simple" else "More creative composition, still very readable."

    return f"""
Create a social media cover ad image (graphic design).

Must look like a real designed ad. Not AI art.
Use flat/vector shapes, subtle gradients, soft shadows. Avoid surreal photos.
No watermark. No gibberish.

Text (place exactly):
- Headline: "{headline}"
- Subheadline: "{sub}"
- CTA: "{cta}"
- Badge: "{badge}"

Layout:
- {layout_notes}
- Notes: {spec.get("layout_notes","")}

Branding:
- Palette: {pal_text}
- If include_logo true: small logo text "{req.logo_text}" in a corner.

Context:
- Offer: {req.offer}
- Audience: {req.audience}
- Tone: {req.tone}
- Platform style: {req.platform_style}
- {style_line}

Output: final ad cover image only.
""".strip()


# =========================
# PROMPTS: VIDEO
# =========================
def build_video_prompt(req: VideoReq) -> str:
    base_style = {
        "IG": "social ad style, clean design, readable typography, conversion-focused",
        "TIKTOK": "short-form ad, fast pacing, bold framing, readable",
        "LINKEDIN": "professional product video, clean, trustworthy",
    }.get(req.platform_style.upper(), "social ad style")

    creative = "Use a clever visual metaphor, but keep it brand-safe and readable." if req.mode == "creative" else \
               "Keep it simple, direct, and product-first."

    shot = "multi-shot narrative (2–4 shots), smooth transitions" if req.shot_type == "multi" else \
           "single shot, steady camera, minimal motion"

    palette = req.palette_hex.strip()
    palette_line = f"Palette hint: {palette}." if palette else "Palette: clean, high-contrast, 2–3 colors."

    logo_line = f"Include subtle logo text '{req.logo_text.strip()}' in a corner." if req.logo_text.strip() else \
                "No explicit logo unless provided."

    lang_line = "Use Indonesian on-screen text." if req.language == "id" else "Use English on-screen text."

    return f"""
Create a short marketing video for a product/service.

Goal: looks like a real ad video. Not AI-art vibe. No weird text.

Context:
- Offer: {req.offer}
- Audience: {req.audience}
- Tone: {req.tone}
- Platform style: {req.platform_style}
- {lang_line}

Direction:
- {base_style}
- {creative}
- {shot}
- {palette_line}
- {logo_line}

Hard rules:
- No watermark.
- No gibberish text.
- No distorted logos.
- Show value clearly in the first 2 seconds.
- End with a soft CTA visual (e.g., "Try it", "Learn more", "DM us") without fake urgency.
""".strip()


# =========================
# STORAGE HELPERS
# =========================
def _now_ms() -> int:
    return int(time.time() * 1000)

def _asset_dir(asset_id: str) -> Path:
    p = ASSETS_DIR / asset_id
    p.mkdir(parents=True, exist_ok=True)
    return p

def _image_meta_path(asset_id: str) -> Path:
    return _asset_dir(asset_id) / "meta.json"

def _video_meta_path(asset_id: str) -> Path:
    return _asset_dir(asset_id) / "video_meta.json"

def _read_json(p: Path, fallback: Dict[str, Any]) -> Dict[str, Any]:
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def _write_json(p: Path, obj: Dict[str, Any]) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def _add_variant(meta_path: Path, base_meta: Dict[str, Any], variant: Dict[str, Any]) -> None:
    meta = _read_json(meta_path, base_meta)
    meta["variants"].append(variant)
    meta["variants"] = sorted(meta["variants"], key=lambda x: x.get("created_at", 0), reverse=True)
    _write_json(meta_path, meta)

def _list_assets_by_meta(filename: str, limit: int = 12) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for d in ASSETS_DIR.iterdir():
        if not d.is_dir():
            continue
        mp = d / filename
        if not mp.exists():
            continue
        meta = _read_json(mp, {})
        if not meta:
            continue
        items.append({
            "asset_id": meta.get("asset_id", d.name),
            "created_at": meta.get("created_at", 0),
            "latest": (meta.get("variants", [])[:1] if isinstance(meta.get("variants"), list) else []),
        })
    items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return items[:limit]


# =========================
# JSON + VALIDATION HELPERS (CAPTION)
# =========================
_caption_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

def _cache_key_caption(req: CaptionReq) -> str:
    s = "|".join([
        req.offer.strip(),
        req.audience.strip(),
        req.tone.strip(),
        req.platform.strip(),
        req.language.strip(),
        req.price_promo.strip(),
        req.cta_preference.strip(),
    ])
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _cache_get_caption(key: str) -> Optional[Dict[str, Any]]:
    item = _caption_cache.get(key)
    if not item:
        return None
    exp, val = item
    if time.time() > exp:
        _caption_cache.pop(key, None)
        return None
    return val

def _cache_set_caption(key: str, val: Dict[str, Any]) -> None:
    _caption_cache[key] = (time.time() + CACHE_TTL_SECONDS, val)

def _extract_json(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start:end+1])
        raise ValueError("Model returned non-JSON output.")

def _reply_pack_fix(obj: Dict[str, Any]) -> None:
    rp = obj.get("reply_pack")
    if isinstance(rp, list):
        fixed: List[str] = []
        for item in rp:
            s = str(item or "").replace("\r", "").replace("\\n", "\n")
            parts = [x.strip(" -•\t").strip() for x in s.split("\n") if x.strip()]
            fixed.extend(parts)
        obj["reply_pack"] = fixed[:5]
        return
    s = str(rp or "").replace("\r", "").replace("\\n", "\n")
    parts = [x.strip(" -•\t").strip() for x in s.split("\n") if x.strip()]
    obj["reply_pack"] = parts[:5]

def _validate_caption_pack_single(obj: Dict[str, Any], platform: str) -> Dict[str, Any]:
    need = ["platform", "opening_best", "opening_options", "main_caption", "short_caption", "cta_options", "reply_pack"]
    for k in need:
        if k not in obj:
            raise ValueError(f"Missing key: {k}")

    _reply_pack_fix(obj)
    rp = obj.get("reply_pack", [])
    if not isinstance(rp, list) or len(rp) != 5:
        raise ValueError("reply_pack must be exactly 5 items")

    for i, x in enumerate(rp):
        if "\n" in str(x) or "\\n" in str(x):
            raise ValueError(f"reply_pack[{i}] contains newline")

    plat = platform.strip().upper()
    if plat == "IG":
        tags = obj.get("hashtags", [])
        if not isinstance(tags, list) or len(tags) != 10:
            raise ValueError("hashtags must be exactly 10 for IG")
    else:
        obj["hashtags"] = []

    obj["platform"] = platform
    return obj


# =========================
# NETWORK CALLS
# =========================
async def _call_chat(system: str, user_prompt: str) -> httpx.Response:
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        return await client.post(f"{CHAT_BASE_URL}/chat/completions", json=payload, headers=headers)

async def _task_poll(task_id: str, timeout_s: int = 420, interval_s: float = 2.0) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}"}
    deadline = time.time() + timeout_s
    async with httpx.AsyncClient(timeout=60) as client:
        while time.time() < deadline:
            r = await client.get(f"{TASK_URL}/{task_id}", headers=headers)
            if r.status_code != 200:
                return {"error_status": r.status_code, "error_body": r.text}
            j = r.json()
            status = j.get("output", {}).get("task_status")
            if status == "SUCCEEDED":
                return j
            if status == "FAILED":
                return {"error_status": "FAILED", "error_body": j}
            await asyncio.sleep(interval_s)
    return {"error_status": "TIMEOUT", "error_body": f"Timed out waiting task {task_id}"}


# =========================
# IMAGE (WAN ASYNC)
# =========================
def aspect_to_wan_size(aspect: str) -> str:
    a = (aspect or "").strip()
    if a == "1:1":
        return "1024*1024"
    if a == "4:5":
        return "1024*1280"
    if a == "9:16":
        return "960*1706"
    if a == "16:9":
        return "1280*720"
    return "1024*1024"

async def wan_image_create_task(prompt: str, size: str, n: int = 1) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": WAN_IMAGE_MODEL,
        "input": {
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ]
        },
        "parameters": {
            "n": n,
            "size": size,
            "watermark": False,
            "prompt_extend": True,
            # key: allow pure text prompt without providing images
            "enable_interleave": True,
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(WAN_IMAGE_CREATE_URL, headers=headers, json=payload)
        if r.status_code != 200:
            return {"error_status": r.status_code, "error_body": r.text}
        return r.json()

def extract_wan_images(task_result: Dict[str, Any]) -> List[str]:
    images: List[str] = []
    try:
        choices = task_result.get("output", {}).get("choices", [])
        if not choices:
            return images
        content = choices[0].get("message", {}).get("content", [])
        if not isinstance(content, list):
            return images
        for item in content:
            if isinstance(item, dict) and item.get("type") == "image" and item.get("image"):
                images.append(item["image"])
    except Exception:
        pass
    return images


# =========================
# VIDEO (WAN ASYNC)
# =========================
def format_to_size(fmt: str, res: str) -> str:
    fmt = (fmt or "").lower().strip()
    res = (res or "").lower().strip()
    if fmt not in ("shorts", "landscape"):
        fmt = "shorts"
    if res not in ("720p", "1080p"):
        res = "720p"
    if fmt == "shorts":
        return "720*1280" if res == "720p" else "1080*1920"
    return "1280*720" if res == "720p" else "1920*1080"

def clamp_urls(urls: List[str], max_total: int = 5) -> List[str]:
    out: List[str] = []
    for u in urls or []:
        s = str(u or "").strip()
        if not s:
            continue
        if s not in out:
            out.append(s)
        if len(out) >= max_total:
            break
    return out

async def wan_video_create_task(req: VideoReq, size: str, references: List[str]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    input_obj: Dict[str, Any] = {
        "prompt": build_video_prompt(req),
        "negative_prompt": req.negative_prompt.strip(),
    }
    # semi R2V: attach refs only if you have public URLs
    if references:
        input_obj["reference_urls"] = references

        # Only some models accept reference_video_urls. wan2.6-r2v-flash forbids it.
        m = (VIDEO_MODEL or "").lower()
        if "r2v-flash" not in m:
            input_obj["reference_video_urls"] = references

    payload = {
        "model": VIDEO_MODEL,
        "input": input_obj,
        "parameters": {
            "size": size,
            "resolution": "1080P" if req.resolution.lower() == "1080p" else "720P",
            "duration": int(req.duration_s),
            "prompt_extend": True,
            "shot_type": "multi" if req.shot_type == "multi" else "single",
            "watermark": False,
            "audio": bool(req.audio),
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(VIDEO_CREATE_URL, headers=headers, json=payload)
        if r.status_code != 200:
            return {"error_status": r.status_code, "error_body": r.text}
        return r.json()

def extract_video_urls(task_result: Dict[str, Any]) -> List[str]:
    urls: List[str] = []

    # 1) content list style
    try:
        choices = task_result.get("output", {}).get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "video" and item.get("video"):
                        urls.append(item["video"])
    except Exception:
        pass

    # 2) video_results style
    if not urls:
        try:
            for item in task_result.get("output", {}).get("video_results", []):
                u = item.get("url")
                if u:
                    urls.append(u)
        except Exception:
            pass

    # 3) output.video_url style (YOUR CASE)
    if not urls:
        try:
            u = task_result.get("output", {}).get("video_url")
            if u:
                urls.append(u)
        except Exception:
            pass

    return urls

# =========================
# ROUTES: UI + FILES
# =========================
@app.get("/", response_class=HTMLResponse)
async def home():
    if INDEX_PATH.exists():
        return INDEX_PATH.read_text(encoding="utf-8")
    return "<h1>index.html not found</h1><p>Put index.html in the same folder as main.py</p>"

@app.get("/tab/{filename}")
async def serve_tab(filename: str):
    allowed = {"caption.html", "image.html", "video.html"}
    if filename not in allowed:
        return HTMLResponse("<p>Not found</p>", status_code=404)
    # Try current directory first, then same directory as main.py
    fp = Path(filename)
    if not fp.exists():
        fp = Path(__file__).with_name(filename)
    if fp.exists():
        return HTMLResponse(fp.read_text(encoding="utf-8"))
    return HTMLResponse(f"<p>{filename} not found</p>", status_code=404)

@app.get("/files/{asset_id}/{variant_id}.png")
async def get_image_file(asset_id: str, variant_id: str):
    fp = _asset_dir(asset_id) / f"{variant_id}.png"
    if not fp.exists():
        return {"error": "file_not_found"}
    return FileResponse(fp, media_type="image/png")

@app.get("/files/{asset_id}/{variant_id}.mp4")
async def get_video_file(asset_id: str, variant_id: str):
    fp = _asset_dir(asset_id) / f"{variant_id}.mp4"
    if not fp.exists():
        return {"error": "file_not_found"}
    return FileResponse(fp, media_type="video/mp4")


# =========================
# ROUTES: CAPTION
# =========================
@app.post("/generate")
async def generate_caption(req: CaptionReq):
    key = _cache_key_caption(req)
    cached = _cache_get_caption(key)
    if cached:
        return {"cached": True, **cached}

    prompt = build_caption_user_prompt(req)
    r = await _call_chat(CAPTION_SYSTEM, prompt)
    if r.status_code != 200:
        return {"error_status": r.status_code, "error_body": r.text}

    raw = r.json()["choices"][0]["message"]["content"]

    def parse_validate(raw_text: str) -> Dict[str, Any]:
        obj = _extract_json(raw_text)
        lang = req.language.strip().lower()
        if lang == "bilingual":
            if "id" not in obj or "en" not in obj:
                raise ValueError("Bilingual requires keys id and en.")
            obj["id"] = _validate_caption_pack_single(obj["id"], req.platform)
            obj["en"] = _validate_caption_pack_single(obj["en"], req.platform)
            return obj
        return _validate_caption_pack_single(obj, req.platform)

    try:
        parsed = parse_validate(raw)
    except Exception:
        retry_prompt = prompt + "\n\nFINAL: JSON only. reply_pack must be 5 separate strings."
        r2 = await _call_chat(CAPTION_SYSTEM, retry_prompt)
        if r2.status_code != 200:
            return {"error_status": r2.status_code, "error_body": r2.text}
        raw2 = r2.json()["choices"][0]["message"]["content"]
        try:
            parsed = parse_validate(raw2)
        except Exception as e2:
            return {"error_status": "bad_json", "error_body": str(e2), "raw": raw2[:2000]}

    _cache_set_caption(key, parsed)
    return {"cached": False, **parsed}


# =========================
# ROUTES: BRAND IMAGE UPLOAD (optional)
# =========================
@app.post("/brand/upload")
async def brand_upload(file: UploadFile = File(...)):
    brand_id = uuid.uuid4().hex[:12]
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        ext = ".png"
    fp = UPLOADS_DIR / f"{brand_id}{ext}"
    fp.write_bytes(await file.read())
    return {"brand_image_id": brand_id, "filename": fp.name}

@app.get("/brand/{brand_image_id}")
async def brand_get(brand_image_id: str):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        fp = UPLOADS_DIR / f"{brand_image_id}{ext}"
        if fp.exists():
            mt = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "image/webp"
            return FileResponse(fp, media_type=mt)
    return {"error": "not_found"}


# =========================
# ROUTES: IMAGE GENERATE + EDIT + HISTORY
# =========================
@app.post("/image/generate")
async def image_generate(req: ImageReq):
    asset_id = uuid.uuid4().hex[:10]
    variant_id = uuid.uuid4().hex[:10]

    # 1) spec
    spec_prompt = build_spec_prompt(req)
    r = await _call_chat(SPEC_SYSTEM, spec_prompt)
    if r.status_code != 200:
        return {"error_status": r.status_code, "error_body": r.text}

    spec_raw = r.json()["choices"][0]["message"]["content"]
    try:
        spec = _extract_json(spec_raw)
    except Exception as e:
        return {"error_status": "bad_json", "error_body": str(e), "raw": spec_raw[:1200]}

    # 2) image generation
    img_prompt = build_image_prompt(req, spec)
    size = aspect_to_wan_size(req.aspect_ratio)

    created = await wan_image_create_task(prompt=img_prompt, size=size, n=1)
    if created.get("error_status"):
        return created

    task_id = created.get("output", {}).get("task_id")
    if not task_id:
        return {"error_status": "no_task_id", "error_body": created}

    result = await _task_poll(task_id, timeout_s=300, interval_s=2.0)
    if result.get("error_status"):
        return result

    urls = extract_wan_images(result)
    if not urls:
        return {"error_status": "no_images", "error_body": result}

    img_url = urls[0]
    async with httpx.AsyncClient(timeout=120) as client:
        dl = await client.get(img_url)
    if dl.status_code != 200:
        return {"error_status": "download_failed", "error_body": dl.text[:400]}

    fp = _asset_dir(asset_id) / f"{variant_id}.png"
    fp.write_bytes(dl.content)

    variant = {
        "variant_id": variant_id,
        "created_at": _now_ms(),
        "req": req.model_dump(),
        "spec": spec,
        "task_id": task_id,
        "wan_image_urls": urls,
        "file": f"/files/{asset_id}/{variant_id}.png",
    }
    _add_variant(
        _image_meta_path(asset_id),
        {"asset_id": asset_id, "created_at": _now_ms(), "variants": []},
        variant,
    )

    return {"asset_id": asset_id, "variant_id": variant_id, "file_url": variant["file"], "spec": spec}

@app.post("/image/edit")
async def image_edit(req: ImageEditReq):
    meta = _read_json(_image_meta_path(req.asset_id), {"asset_id": req.asset_id, "created_at": 0, "variants": []})
    base_var = None
    for v in meta.get("variants", []):
        if v.get("variant_id") == req.variant_id:
            base_var = v
            break
    if not base_var:
        return {"error_status": "base_variant_not_found"}

    base_req = base_var.get("req", {})
    new_req = dict(base_req)

    def oset(field: str, val: Any):
        if val is None:
            return
        if isinstance(val, str):
            if val.strip() == "":
                return
            new_req[field] = val.strip()
        else:
            new_req[field] = val

    oset("tone", req.tone)
    oset("language", req.language)
    oset("aspect_ratio", req.aspect_ratio)
    oset("mode", req.mode)
    oset("headline", req.headline)
    oset("subheadline", req.subheadline)
    oset("palette_hex", req.palette_hex)
    oset("layout_id", req.layout_id)
    if req.include_logo is not None:
        new_req["include_logo"] = bool(req.include_logo)
    oset("logo_text", req.logo_text)
    oset("brand_image_id", req.brand_image_id)

    try:
        img_req = ImageReq(**new_req)
    except Exception as e:
        return {"error_status": "invalid_request", "detail": str(e)}

    spec_prompt = build_spec_prompt(img_req)
    r = await _call_chat(SPEC_SYSTEM, spec_prompt)
    if r.status_code != 200:
        return {"error_status": r.status_code, "error_body": r.text}

    spec_raw = r.json()["choices"][0]["message"]["content"]
    try:
        spec = _extract_json(spec_raw)
    except Exception as e:
        return {"error_status": "bad_json", "error_body": str(e), "raw": spec_raw[:1200]}

    img_prompt = build_image_prompt(img_req, spec)
    size = aspect_to_wan_size(img_req.aspect_ratio)

    created = await wan_image_create_task(prompt=img_prompt, size=size, n=1)
    if created.get("error_status"):
        return created

    task_id = created.get("output", {}).get("task_id")
    if not task_id:
        return {"error_status": "no_task_id", "error_body": created}

    result = await _task_poll(task_id, timeout_s=300, interval_s=2.0)
    if result.get("error_status"):
        return result

    urls = extract_wan_images(result)
    if not urls:
        return {"error_status": "no_images", "error_body": result}

    img_url = urls[0]
    async with httpx.AsyncClient(timeout=120) as client:
        dl = await client.get(img_url)
    if dl.status_code != 200:
        return {"error_status": "download_failed", "error_body": dl.text[:400]}

    new_variant_id = uuid.uuid4().hex[:10]
    fp = _asset_dir(req.asset_id) / f"{new_variant_id}.png"
    fp.write_bytes(dl.content)

    variant = {
        "variant_id": new_variant_id,
        "created_at": _now_ms(),
        "base_variant_id": req.variant_id,
        "req": img_req.model_dump(),
        "spec": spec,
        "task_id": task_id,
        "wan_image_urls": urls,
        "file": f"/files/{req.asset_id}/{new_variant_id}.png",
    }
    _add_variant(
        _image_meta_path(req.asset_id),
        {"asset_id": req.asset_id, "created_at": meta.get("created_at", 0) or _now_ms(), "variants": []},
        variant,
    )

    return {"asset_id": req.asset_id, "variant_id": new_variant_id, "file_url": variant["file"], "spec": spec}

@app.get("/image/history")
async def image_history(limit: int = 12):
    return {"items": _list_assets_by_meta("meta.json", limit=limit)}

@app.get("/image/history/{asset_id}")
async def image_history_asset(asset_id: str):
    meta = _read_json(_image_meta_path(asset_id), {"asset_id": asset_id, "created_at": 0, "variants": []})
    out = {"asset_id": meta.get("asset_id", asset_id), "created_at": meta.get("created_at", 0), "variants": []}
    for v in meta.get("variants", []):
        out["variants"].append({
            "variant_id": v.get("variant_id"),
            "created_at": v.get("created_at"),
            "file_url": v.get("file"),
            "req": v.get("req", {}),
            "spec": v.get("spec", {}),
            "base_variant_id": v.get("base_variant_id", ""),
        })
    return out

# Compatibility aliases (in case UI still calls /history)
@app.get("/history")
async def compat_history(limit: int = 12):
    return await image_history(limit=limit)

@app.get("/history/{asset_id}")
async def compat_history_asset(asset_id: str):
    return await image_history_asset(asset_id)


# =========================
# ROUTES: VIDEO GENERATE + STATUS + HISTORY
# =========================
@app.post("/video/generate")
async def video_generate(req: VideoReq):
    asset_id = uuid.uuid4().hex[:10]
    variant_id = uuid.uuid4().hex[:10]

    refs = clamp_urls(req.reference_urls, 5)
    if not refs:
        refs = [DEFAULT_VIDEO_REF_URL]

    size = format_to_size(req.format, req.resolution)

    created = await wan_video_create_task(req=req, size=size, references=refs)
    if created.get("error_status"):
        return created

    task_id = created.get("output", {}).get("task_id") or created.get("output", {}).get("taskId")
    if not task_id:
        return {"error_status": "no_task_id", "error_body": created}

    return {
        "asset_id": asset_id,
        "variant_id": variant_id,
        "task_id": task_id,
        "status": "PENDING",
        "poll_url": f"/video/status/{task_id}?asset_id={asset_id}&variant_id={variant_id}",
    }

@app.get("/video/status/{task_id}")
async def video_status(task_id: str, asset_id: str, variant_id: str):
    result = await _task_poll(task_id, timeout_s=420, interval_s=2.0)
    if result.get("error_status"):
        return result

    urls = extract_video_urls(result)
    if not urls:
        return {"error_status": "no_videos", "error_body": result}

    video_url = urls[0]
    async with httpx.AsyncClient(timeout=180) as client:
        dl = await client.get(video_url)
    if dl.status_code != 200:
        return {"error_status": "download_failed", "error_body": dl.text[:400]}

    fp = _asset_dir(asset_id) / f"{variant_id}.mp4"
    fp.write_bytes(dl.content)

    # ✅ save to history ONLY when success
    variant = {
        "variant_id": variant_id,
        "created_at": _now_ms(),
        "status": "SUCCEEDED",
        "task_id": task_id,
        "file": f"/files/{asset_id}/{variant_id}.mp4",
        "remote_urls": urls,
    }
    _add_variant(
        _video_meta_path(asset_id),
        {"asset_id": asset_id, "created_at": _now_ms(), "variants": []},
        variant,
    )

    return {
        "asset_id": asset_id,
        "variant_id": variant_id,
        "task_id": task_id,
        "status": "SUCCEEDED",
        "file_url": f"/files/{asset_id}/{variant_id}.mp4",
        "remote_urls": urls,
    }

@app.get("/video/history")
async def video_history(limit: int = 12):
    return {"items": _list_assets_by_meta("video_meta.json", limit=limit)}

@app.get("/video/history/{asset_id}")
async def video_history_asset(asset_id: str):
    meta = _read_json(_video_meta_path(asset_id), {"asset_id": asset_id, "created_at": 0, "variants": []})
    out = {"asset_id": meta.get("asset_id", asset_id), "created_at": meta.get("created_at", 0), "variants": []}
    for v in meta.get("variants", []):
        out["variants"].append({
            "variant_id": v.get("variant_id"),
            "created_at": v.get("created_at"),
            "status": v.get("status", ""),
            "task_id": v.get("task_id", ""),
            "file_url": v.get("file", ""),
            "req": v.get("req", {}),
            "remote_urls": v.get("remote_urls", []),
        })
    return out


# =========================
# OPTIONAL: VIDEO REF UPLOAD (DEMO)
# =========================
@app.post("/video/ref/upload")
async def video_ref_upload(file: UploadFile = File(...)):
    ref_id = uuid.uuid4().hex[:12]
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".m4v"):
        ext = ".png"
    fp = VIDEO_REFS_DIR / f"{ref_id}{ext}"
    fp.write_bytes(await file.read())
    # NOTE: Model usually needs public URL. This is local-only unless you tunnel your server.
    return {"ref_id": ref_id, "filename": fp.name, "ref_url": f"/video/ref/{ref_id}{ext}"}

@app.get("/video/ref/{ref_filename}")
async def video_ref_get(ref_filename: str):
    fp = VIDEO_REFS_DIR / ref_filename
    if not fp.exists():
        return {"error": "not_found"}
    ext = fp.suffix.lower()
    if ext == ".png":
        mt = "image/png"
    elif ext in (".jpg", ".jpeg"):
        mt = "image/jpeg"
    elif ext == ".webp":
        mt = "image/webp"
    else:
        mt = "video/mp4"
    return FileResponse(fp, media_type=mt)

@app.get("/health")
async def health():
    return {"ok": True}

# =========================
# DEBUG (safe)
# =========================
@app.get("/debug-key")
async def debug_key():
    k = os.getenv("DASHSCOPE_API_KEY", "")
    return {"prefix": k[:6], "len": len(k)}