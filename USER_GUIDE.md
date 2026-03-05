# Ads Tweaker - User Guide

## Quick Start

1. Open http://127.0.0.1:15503 in your browser
2. Choose a tab: Captions, Images, or Videos
3. Fill in the required fields
4. Click generate button
5. View and download your results

## Tab Behavior

### 🔄 Input Reset on Tab Switch

**Important**: When you switch between tabs, all input fields reset to default values.

**Example**:
```
You're on Caption tab with:
  - Offer: "My Product"
  - Audience: "Young adults"
  
You switch to Image tab →
  
All fields are now empty/default:
  - Offer: (empty)
  - Audience: (empty)
  - Platform: IG (default)
  - Tone: friendly (default)
```

**Why?** This ensures each tab starts fresh, preventing confusion and ensuring you provide the right context for each generation type.

## Tabs Overview

### 📝 Captions Tab

Generate AI-powered social media captions.

**Required Fields**:
- What are you promoting? (min 10 characters)
- Who is this for? (min 3 characters)

**Optional Fields**:
- Platform (Instagram/LinkedIn/TikTok)
- Tone (Friendly/Formal/Bold/Funny/Luxury)
- Language (Indonesian/English/Bilingual)
- Price/Promo
- CTA Preference

**Output**:
- Opening hooks (best + variations)
- Main caption
- Short caption
- CTA options
- Hashtags (10 for Instagram)
- Reply pack (5 responses)

**Actions**:
- Copy individual sections
- Copy full pack
- Regenerate

---

### 🖼️ Images Tab

Generate social media cover images.

**Required Fields**:
- What are you promoting?
- Who is this for?

**Image Settings**:
- Aspect Ratio (1:1, 4:5, 9:16, 16:9)
- Layout Style (4 options)
- Mode (Simple/Creative)

**Optional**:
- Brand Image Upload
- Brand Name (logo text)
- Color Palette (up to 4 colors)
- Custom Headline
- Custom Subheadline

**Output**:
- Generated image
- Download button
- Select for editing

**Features**:
- Edit existing images (change tone, layout, colors)
- View history
- Version management

---

### 🎥 Videos Tab

Generate short-form video ads.

**Required Fields**:
- What are you promoting?
- Who is this for?

**Video Settings**:
- Duration (2-10 seconds)
- Format (Shorts 9:16 / Landscape 16:9)
- Resolution (720p/1080p)
- Mode (Simple/Creative)
- Shot Type (Single/Multi)
- Audio (On/Off)

**Optional**:
- Reference URLs (images/videos)
- Logo Text
- Color Palette

**Output**:
- Video player
- Download button
- Processing status

**Note**: Video generation takes 1-3 minutes.

---

## Common Actions

### Reset Form
Each tab has a "Reset all" button that:
- Clears all input fields
- Resets to default values
- Does NOT clear generated outputs

### Clear Outputs
Each tab has a "Clear outputs" button that:
- Removes all generated results
- Does NOT clear input fields

### Copy to Clipboard
Click any "Copy" button to:
- Copy text to clipboard
- See "Copied!" confirmation
- Get toast notification

### Download Files
- Images: Click "Download" on any image card
- Videos: Click "Download MP4" button

## Tips & Best Practices

### For Better Captions
✅ Be specific about your product/service
✅ Clearly define your target audience
✅ Include price/promo if available
✅ Choose appropriate tone for your brand

### For Better Images
✅ Upload your brand logo for consistency
✅ Choose colors that match your brand
✅ Use Simple mode for clean, readable designs
✅ Use Creative mode for eye-catching visuals
✅ Try different layouts to see what works

### For Better Videos
✅ Keep duration short (5-7 seconds optimal)
✅ Use reference images for style guidance
✅ Enable audio for more engaging content
✅ Multi-shot works better for storytelling
✅ Single-shot works better for product focus

## Keyboard Shortcuts

- `Tab` - Navigate between form fields
- `Enter` - Submit form (when in text input)
- `Ctrl+C` / `Cmd+C` - Copy selected text

## Troubleshooting

### "Cannot GET /tab/..." Error
- Refresh the page
- Check if server is running
- Clear browser cache

### Generation Failed
- Check your internet connection
- Verify API key in .env file
- Try again (temporary API issue)

### Inputs Not Resetting
- This is expected behavior
- Inputs reset when switching tabs
- Use "Reset all" button to clear manually

### Video Taking Too Long
- Video generation takes 1-3 minutes
- Don't close the tab while processing
- Check video history if page was closed

## Browser Support

✅ Chrome (recommended)
✅ Firefox
✅ Safari
✅ Edge

## Need Help?

- Check STRUCTURE.md for technical details
- Check INPUT_BEHAVIOR.md for tab behavior
- Check CHANGELOG.md for recent changes
