# Changelog - LocalImageSearch Project Integration

## 2026-02-05 (Update) - Database Path Migration

### Changes
- **Database Location**: Moved to user home directory `~/.LocalImageSearch/data/image_tags.db`
- **Auto-creation**: Directory is automatically created if it doesn't exist
- **Benefits**:
  - Follows Unix conventions for user data (hidden directory in home)
  - Easier to backup and maintain
  - Independent of project location
  - Better multi-user support

### Updated Files
- `ui/lib/db.ts` - Added `os` and `fs` imports, dynamic path construction
- `ui/README.md` - Updated database path documentation
- `README.md` - Added database location note

### Migration
Database copied from:
- **Old**: `<project-scripts-tag>/data/image_tags.db`
- **New**: `~/.LocalImageSearch/data/image_tags.db`

---

## 2026-02-05 - Web UI Integration

### Overview
Successfully integrated the Next.js web UI from `feat/ui/web` branch into the main repository.

### Changes

#### 1. **Web UI (ui/ directory)**
- **Location**: `<project-root>/ui/`
- **Features**:
  - Bilingual interface (Chinese/English)
  - Tag cloud with configurable display (TOP 20/100 tags)
  - Multi-tag AND filtering using inverted index
  - Full-text search across tags and descriptions
  - Responsive image grid with pagination (20 images/page)
  - Modal image viewer with fullscreen support
  - Configurable display limits via `lib/config.ts`

#### 2. **API Endpoints**
- `GET /api/tags?limit=N` - Retrieve top N tags by count
- `GET /api/images?query=...&tags=...&page=N&limit=M` - Search images
- `GET /api/img?path=...` - Serve image files with security whitelist

#### 3. **Database Integration**
- **Database Path**: `~/.LocalImageSearch/data/image_tags.db` (migrated to user home directory)
- **Tables Used**:
  - `image_tags` - Main data (147 images)
  - `tag_index` - Inverted index (1208 entries)
  - `image_fts*` - FTS5 full-text search

#### 4. **Configuration**
```typescript
// ui/lib/config.ts
export const CONFIG = {
  tagApiLimit: 100,           // API returns TOP 100 tags
  tagCloudLimit: 20,          // Default display 20 tags
  tagCloudExpandedLimit: 100, // Max 100 when expanded
  imagesPerPage: 20,          // 20 images per page
};
```

#### 5. **Security**
Image serving restricted to whitelisted directories:
- `~/Downloads`
- `~/.LocalImageSearch`
- `/tmp`

#### 6. **Docker Integration**
Added `ui` service to `docker-compose.yml`:
```yaml
services:
  ui:
    build: ./ui
    ports:
      - "3000:3000"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - app
```

### Git Commits

**Main branch (LocalImageSearch):**
- `ac7ebb8` - feat: add UI service to docker-compose
- `8662dd4` - docs: update README with web UI documentation
- `4037c40` - feat: add Next.js web UI for image search

**feat/ui/web branch (project-ui-web):**
- `00ea11d` - feat: add image search UI with Next.js

### Testing Results

#### Web UI Tests (Port 3001)
- ✅ Tags API: Returns TOP 5 tags correctly
  ```json
  [
    {"tag":"黑色背景","count":13},
    {"tag":"无内容","count":11},
    {"tag":"空白","count":11},
    {"tag":"黑色","count":10},
    {"tag":"空白画面","count":9}
  ]
  ```

- ✅ Images API: Returns paginated results (147 total images)
- ✅ Build: Successfully compiled without errors
- ✅ Dependencies: 152 packages installed, 0 vulnerabilities

#### Python Backend Tests
- ✅ Database structure verified (show_table_structure.py)
- ✅ All required tables present:
  - image_tags ✓
  - tag_index ✓ (1208 entries)
  - image_fts* ✓ (FTS5 tables)

### Documentation Updates

#### README.md
Added Web UI section with:
- Feature list
- Quick start guide
- Configuration instructions
- Link to detailed ui/README.md

#### ui/README.md
Created comprehensive documentation including:
- Prerequisites and installation
- Configuration guide
- Development and production builds
- API route documentation
- Architecture overview
- Database schema requirements
- Security configuration
- Troubleshooting guide

### Project Structure

```
LocalImageSearch/
├── ui/                       # Next.js web interface (NEW)
│   ├── app/                  # Next.js app directory
│   │   ├── api/              # API routes
│   │   │   ├── images/       # Image search
│   │   │   ├── img/          # Image serving
│   │   │   └── tags/         # Tag listing
│   │   ├── globals.css       # Global styles
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Main UI
│   ├── lib/                  # Frontend utilities
│   │   ├── config.ts         # Configuration
│   │   ├── db.ts             # Database queries
│   │   └── i18n.ts           # Translations
│   ├── .gitignore            # Node/Next.js ignores
│   ├── README.md             # UI documentation
│   └── *.config.*            # Build configs
├── src/                      # Python backend (existing)
├── doc/                      # Documentation
├── data/                     # Database storage
├── docker-compose.yml        # Updated with UI service
└── README.md                 # Updated with UI docs
```

### Repository Information

- **Main Repository**: LocalImageSearch
- **Location**: `<project-root>/`
- **Branch**: main
- **UI Branch**: feat/ui/web (merged into main/ui/)
- **Backend Branch**: feat/scripts/index (pending - at project-scripts-index/)

### How to Use

#### Development
```bash
# Install dependencies
cd ui
npm install

# Start dev server
npm run dev
# Opens on http://localhost:3000 (or 3001 if 3000 is busy)
```

#### Production
```bash
cd ui
npm run build
npm start
```

#### Docker
```bash
docker-compose up ui
```

### Known Issues / Notes

1. **Database Path**: UI currently hardcoded to use database at:
   `<old-project-dir>/data/image_tags.db`
   - Adjust in `ui/lib/db.ts` for different setups

2. **Image Paths**: Ensure image paths in database are accessible from whitelisted directories

3. **Port Conflicts**: Dev server uses port 3000 by default, automatically tries 3001 if busy

### Next Steps (Optional)

1. Consider integrating the FastAPI backend from `project-scripts-index` for semantic search
2. Add authentication for production deployment
3. Implement image upload functionality
4. Add batch tagging interface
5. Create admin panel for tag management

### Summary Statistics

- **Files Added**: 18 (ui directory)
- **API Endpoints**: 3
- **Supported Languages**: 2 (Chinese, English)
- **Database Tables**: 3 (image_tags, tag_index, image_fts)
- **Total Images**: 147
- **Tag Index Entries**: 1,208
- **Build Size**: 91.9 kB (First Load JS)
- **Dependencies**: 152 packages

---

**Generated**: 2026-02-05
**By**: Claude Code Assistant
