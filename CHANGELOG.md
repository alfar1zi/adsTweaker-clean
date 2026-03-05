# Changelog

## [2.0.0] - UI Restructure & Input Reset Behavior

### Changed
- **Input Behavior**: Core inputs (offer, audience, platform, tone, language, price_promo, cta_preference) now reset to default values when switching between tabs
- **Previous Behavior**: Inputs were persisted across tabs
- **New Behavior**: Each tab starts with fresh/default values

### Restructured
- **Separated CSS**: Moved all styles from inline `<style>` to `/static/styles.css`
- **Separated JavaScript**: 
  - Shared utilities moved to `/static/shared.js`
  - Starfield animation moved to `/static/starfield.js`
- **Cleaner index.html**: Now only contains structure, no inline styles or large scripts

### File Structure
```
/
├── index.html              # Main shell (header + tabs)
├── caption.html            # Caption tab content
├── image.html              # Image tab content
├── video.html              # Video tab content
├── main.py                 # Backend server
├── .env                    # Configuration
└── static/
    ├── styles.css          # All CSS styling
    ├── shared.js           # Shared utilities & state
    └── starfield.js        # Background animation
```

### Benefits
1. **Better UX**: Users get fresh start on each tab, preventing confusion
2. **Cleaner Code**: Separation of concerns (HTML/CSS/JS)
3. **Easier Maintenance**: Find and edit specific components easily
4. **Better Performance**: Static files cached by browser
5. **Scalability**: Easy to add new tabs or features

### Technical Details

#### Input Reset Function
```javascript
function resetCoreInputs() {
  // Resets all core inputs to default values
  // Called automatically when switching tabs
}
```

#### Default Values
- `offer`: "" (empty)
- `audience`: "" (empty)
- `platform`: "IG" (Instagram)
- `tone`: "friendly"
- `language`: "id" (Indonesian)
- `price_promo`: "" (empty)
- `cta_preference`: "" (empty/auto)

#### Tab Switching Flow
1. User clicks tab button
2. Tab content loaded (from cache or server)
3. HTML injected into container
4. Scripts executed
5. **Inputs automatically reset to defaults** ← NEW
6. Tab becomes active

### Migration Notes
- No breaking changes to backend API
- Frontend behavior change only
- Users will notice inputs don't persist between tabs
- This is intentional for better UX

### Files Modified
- `static/shared.js` - Removed persistence, added reset function
- `caption.html` - Removed coreInputState reference
- `image.html` - Removed coreInputState reference
- `video.html` - Removed coreInputState reference
- `STRUCTURE.md` - Updated documentation

---

## [1.0.0] - Initial Release

### Features
- Caption generation with AI
- Image generation with customization
- Video generation with polling
- Brand image upload
- History tracking
- Multi-language support (Indonesian/English)
- Dark theme UI with starfield background
