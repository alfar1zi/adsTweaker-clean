# Input Behavior - Tab Switching

## Current Behavior (After Update)

### When Switching Tabs
✅ **Inputs are RESET to default values**

```
User on Caption Tab:
  offer: "SwiftNote AI - meeting notes app"
  audience: "busy professionals"
  platform: "IG"
  tone: "friendly"
  
User clicks "Images" tab →
  
User on Image Tab:
  offer: "" ← RESET (empty)
  audience: "" ← RESET (empty)
  platform: "IG" ← DEFAULT
  tone: "friendly" ← DEFAULT
```

### Why This Change?

1. **Prevents Confusion**: Each tab is independent, users don't wonder why fields are pre-filled
2. **Fresh Start**: Users can focus on the specific task for that tab
3. **Clear Intent**: Explicit input for each generation type
4. **Better UX**: No unexpected behavior from previous tab

### Default Values Per Field

| Field | Default Value | Type |
|-------|--------------|------|
| `offer` | `""` (empty) | Text |
| `audience` | `""` (empty) | Text |
| `platform` | `"IG"` | Select |
| `tone` | `"friendly"` | Select |
| `language` | `"id"` | Select |
| `price_promo` | `""` (empty) | Text |
| `cta_preference` | `""` (auto) | Select |

### User Flow Example

#### Scenario: User wants to generate caption, then image

1. **Caption Tab**
   - User fills: offer, audience, platform, tone
   - Clicks "Generate caption pack"
   - Gets caption results ✓

2. **Switch to Image Tab**
   - All inputs reset to defaults
   - User fills: offer, audience (can be different from caption)
   - Configures image settings (aspect ratio, layout, etc.)
   - Clicks "Generate (Simple)"
   - Gets image results ✓

3. **Switch back to Caption Tab**
   - All inputs reset again
   - Previous caption results still visible in output area
   - User can generate new caption with fresh inputs

### What Persists Across Tabs?

✅ **These DO persist:**
- Generated outputs (captions, images, videos)
- History data
- Brand image uploads
- Selected assets (for editing)
- Palette colors
- Output display

❌ **These DO NOT persist:**
- Core input fields (offer, audience, etc.)
- Form selections (platform, tone, language)
- Advanced options (price_promo, cta_preference)

### Reset Button Behavior

Each tab has a "Reset all" button that:
- Clears all input fields
- Resets selects to default values
- Does NOT clear generated outputs
- Shows "Form reset" confirmation

### Technical Implementation

```javascript
// Called automatically when switching tabs
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
```

### Tab Switching Sequence

```
1. User clicks tab button
   ↓
2. Update active tab styling
   ↓
3. Load tab HTML (from cache or fetch)
   ↓
4. Inject HTML into container
   ↓
5. Execute embedded scripts
   ↓
6. Call resetCoreInputs() ← AUTO RESET
   ↓
7. Tab ready with default values
```

### Comparison: Before vs After

#### Before (Persisted)
```
Caption Tab: offer="Product A", audience="Students"
  ↓ switch to Image
Image Tab: offer="Product A", audience="Students" ← PERSISTED
```

**Problem**: User might not notice and generate image with wrong context

#### After (Reset)
```
Caption Tab: offer="Product A", audience="Students"
  ↓ switch to Image
Image Tab: offer="", audience="" ← RESET
```

**Benefit**: User must explicitly fill inputs, ensuring correct context

### Edge Cases Handled

1. **Rapid Tab Switching**: Reset happens each time, no race conditions
2. **Browser Back/Forward**: Tab state maintained correctly
3. **Page Refresh**: All tabs start fresh (expected behavior)
4. **Multiple Windows**: Each window independent (expected behavior)

### Future Considerations

If users request input persistence in the future, we could:
- Add a "Remember inputs" checkbox
- Store per-tab state separately
- Add "Copy from Caption" button in other tabs
- Implement localStorage persistence

For now, the reset behavior provides the cleanest UX.
