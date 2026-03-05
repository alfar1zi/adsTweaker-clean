/* =========================
   Shared State (on window)
========================= */
window.selectedAssetId = null;
window.selectedVariantId = null;
window.brandImageId = "";
window.palette = ["#6366f1"];
window.currentVideoTask = null;
window.lastCaptionData = null;
window.lastImageSettings = null;

/* =========================
   Shared Utilities
========================= */
function escapeHtml(str) {
  return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '\u2713' : '\u2715'}</span>
    <span>${escapeHtml(message)}</span>
  `;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'fadeOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btnElement.textContent;
    btnElement.textContent = 'Copied!';
    btnElement.classList.add('copied');
    showToast('Copied to clipboard');
    setTimeout(() => {
      btnElement.textContent = original;
      btnElement.classList.remove('copied');
    }, 1500);
  });
}

function setOk(msg) { 
  const el = document.getElementById("status");
  if (el) el.innerHTML = `<span class="ok">${msg}</span>`; 
}
function setBad(msg) { 
  const el = document.getElementById("status");
  if (el) el.innerHTML = `<span class="bad">${msg}</span>`; 
}
function setMuted(msg) { 
  const el = document.getElementById("status");
  if (el) el.innerHTML = `<span class="muted">${msg}</span>`; 
}

function setButtonsDisabled(disabled) {
  document.querySelectorAll("button, .btn").forEach(b => { b.disabled = disabled; });
}

function startProgress(label) {
  const p = document.getElementById("prog");
  const pl = document.getElementById("progLabel");
  p.classList.remove("done");
  p.classList.add("show");
  pl.classList.remove("hidden");
  if (label) pl.textContent = label;
  setButtonsDisabled(true);
}

function endProgress(ok, label) {
  const p = document.getElementById("prog");
  const pl = document.getElementById("progLabel");
  p.classList.add("done");
  setButtonsDisabled(false);
  if (label) {
    if (ok) setOk(label); else setBad(label);
  }
  setTimeout(() => { 
    p.classList.remove("show"); 
    p.classList.remove("done"); 
    pl.classList.add("hidden");
  }, 600);
}

/* =========================
   Core Input Reset (per tab)
========================= */
function resetCoreInputs() {
  const ids = ["offer","audience","platform","tone","language","price_promo","cta_preference"];
  for (const id of ids) {
    const el = document.getElementById(id);
    if (el) {
      // Reset to default values
      if (id === "offer" || id === "audience" || id === "price_promo") {
        el.value = "";
      } else if (id === "platform") {
        el.value = "IG";
      } else if (id === "tone") {
        el.value = "friendly";
      } else if (id === "language") {
        el.value = "id";
      } else if (id === "cta_preference") {
        el.value = "";
      }
    }
  }
}

/* =========================
   Tab Loading
========================= */
const tabCache = {};
let currentTab = null;

async function switchTab(name) {
  if (currentTab === name) return;

  // Prevent tab switching if buttons are disabled (generation in progress)
  const anyButtonDisabled = document.querySelector("button:disabled, .btn:disabled");
  if (anyButtonDisabled) {
    showToast("Please wait for the current operation to complete", "error");
    return;
  }

  // Update tab button states
  const panels = ["caption","image","video"];
  for (const p of panels) {
    document.getElementById("tab-"+p).classList.remove("active");
  }
  document.getElementById("tab-"+name).classList.add("active");

  const container = document.getElementById("tabContent");

  // Fetch or use cache
  if (!tabCache[name]) {
    container.innerHTML = '<div class="loadingCard"><div class="spinner-lg" style="margin:0 auto;"></div><div class="muted mt-3">Loading...</div></div>';
    try {
      const res = await fetch(`/tab/${name}.html`);
      tabCache[name] = await res.text();
    } catch (e) {
      container.innerHTML = '<div class="outCard"><div class="bad">Failed to load tab</div></div>';
      return;
    }
  }

  // Inject HTML
  container.innerHTML = tabCache[name];

  // Execute script blocks (innerHTML doesn't execute them)
  container.querySelectorAll('script').forEach(oldScript => {
    const newScript = document.createElement('script');
    newScript.textContent = oldScript.textContent;
    oldScript.replaceWith(newScript);
  });

  // Reset inputs to default values when switching tabs
  setTimeout(() => {
    resetCoreInputs();
  }, 50);

  currentTab = name;
}

// Tab event listeners
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById("tab-caption").addEventListener("click", () => switchTab("caption"));
  document.getElementById("tab-image").addEventListener("click", () => switchTab("image"));
  document.getElementById("tab-video").addEventListener("click", () => switchTab("video"));
});
