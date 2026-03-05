# CaptionForge - Clean UI Structure

## File Organization

### Main Files
- `index.html` - Main shell/wrapper with header and tab navigation
- `main.py` - FastAPI backend server
- `.env` - Environment configuration

### Tab Pages (Loaded Dynamically)
- `caption.html` - Caption generation tab
- `image.html` - Image generation tab  
- `video.html` - Video generation tab

### Static Assets (`/static/`)
- `styles.css` - All CSS styling (design system, components, animations)
- `shared.js` - Shared JavaScript utilities and state management
- `starfield.js` - Animated starfield background

### Data Directories
- `data/assets/` - Generated images and videos
- `data/uploads/` - Uploaded brand images
- `data/video_refs/` - Video reference files

## Architecture

### Frontend Structure

```
index.html (Shell)
├── Header
├── Tab Navigation
├── Progress Bar
└── Tab Content Container (Dynamic)
    ├── caption.html (loaded on demand)
    ├── image.html (loaded on demand)
    └── video.html (loaded on demand)
```

### JavaScript Organization

**shared.js** contains:
- Global state management (selectedAssetId, brandImageId, palette, etc.)
- Core input reset function (resetCoreInputs - resets to defaults when switching tabs)
- Utility functions (escapeHtml, showToast, copyToClipboard)
- Progress bar controls (startProgress, endProgress)
- Status message helpers (setOk, setBad, setMuted)
- Tab switching logic (switchTab with caching and auto-reset)

**Tab-specific scripts** (embedded in each tab HTML):
- Caption tab: Caption generation and rendering
- Image tab: Image generation, editing, history, palette management
- Video tab: Video generation, polling, history

### CSS Organization

**styles.css** contains:
- Design system variables (colors, spacing, shadows)
- Base styles (body, typography, layout)
- Component styles (buttons, cards, forms, tabs)
- Utility classes (spacing, display, text)
- Animations (fadeIn, fadeInUp, spin)
- Responsive breakpoints

### Backend Structure

**main.py** endpoints:
- `GET /` - Serve index.html
- `GET /tab/{filename}` - Serve tab HTML files
- `GET /static/*` - Serve static assets
- `POST /generate` - Generate captions
- `POST /image/generate` - Generate images
- `POST /image/edit` - Edit existing images
- `GET /image/history` - Get image history
- `POST /video/generate` - Generate videos
- `GET /video/status/{task_id}` - Poll video status
- `GET /video/history` - Get video history
- `POST /brand/upload` - Upload brand images
- `GET /files/{asset_id}/{variant_id}.*` - Serve generated files

## Key Features

### Tab System
- Dynamic loading with caching
- Smooth transitions
- Core inputs reset to defaults when switching tabs
- Script execution after HTML injection

### State Management
- Global window state for cross-tab data (images, videos, brand assets)
- Core inputs reset to defaults when switching tabs
- Asset selection tracking
- Brand image and palette management

### Progress Indication
- Sticky progress bar
- Indeterminate animation
- Status messages (success/error/info)
- Button disable during operations

### Visual Design
- Dark theme with gradient accents
- Animated starfield background
- Smooth transitions and hover effects
- Responsive grid layouts
- Toast notifications

## Development

### Running the Server
```bash
python -m uvicorn main:app --reload --port 15503
```

### File Locations
- HTML files: Root directory
- Static assets: `/static/` directory
- Generated files: `/data/` directory
- Environment config: `.env` file

### Adding New Features
1. Add CSS to `static/styles.css`
2. Add shared JS to `static/shared.js`
3. Add tab-specific code to respective tab HTML
4. Add backend endpoints to `main.py`

## Benefits of This Structure

✅ **Separation of Concerns**
- HTML structure separate from styling and behavior
- Each tab is self-contained
- Shared code is centralized

✅ **Maintainability**
- Easy to find and edit specific components
- CSS changes don't require HTML edits
- JavaScript utilities are reusable

✅ **Performance**
- Tabs loaded on demand
- Caching prevents redundant requests
- Static assets served efficiently

✅ **Scalability**
- Easy to add new tabs
- Simple to extend functionality
- Clear file organization

✅ **Developer Experience**
- Clean, readable code structure
- Logical file organization
- Easy to understand flow
