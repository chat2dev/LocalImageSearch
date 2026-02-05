# LocalImageSearch - Web UI

A Next.js-based web interface for searching and browsing images indexed by the LocalImageSearch system.

## Features

- **Bilingual Support**: Chinese/English interface
- **Tag Cloud**: Browse images by popular tags (configurable TOP 20/100)
- **Multi-tag Filtering**: AND-based filtering using inverted index
- **Full-text Search**: Search across tags and descriptions
- **Responsive Grid**: Image gallery with pagination
- **Image Viewer**: Modal viewer with fullscreen support
- **Configurable Display**: Adjustable tag limits and images per page

## Prerequisites

- Node.js >= 18.17.0
- npm or yarn
- LocalImageSearch database at `../data/image_tags.db` (or configure path in `lib/db.ts`)

## Installation

```bash
cd ui
npm install
```

## Configuration

Edit `lib/config.ts` to adjust display settings:

```typescript
export const CONFIG = {
  tagApiLimit: 100,           // API returns TOP 100 tags
  tagCloudLimit: 20,          // Default display 20 tags
  tagCloudExpandedLimit: 100, // Max 100 when expanded
  imagesPerPage: 20,          // 20 images per page
} as const;
```

## Database Path

The UI stores the database in the user's home directory at `~/.LocalImageSearch/data/image_tags.db`. This location is automatically created if it doesn't exist.

The path is configured in `lib/db.ts`:

```typescript
const DATA_DIR = path.join(os.homedir(), '.LocalImageSearch', 'data');
const DB_PATH = path.join(DATA_DIR, 'image_tags.db');
```

To use a different location, modify these constants in `lib/db.ts`.

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Production Build

```bash
npm run build
npm start
```

## API Routes

The UI provides three API endpoints:

- `GET /api/tags?limit=100` - Get top N tags by count
- `GET /api/images?query=...&tags=...&page=0&limit=20` - Search images
- `GET /api/img?path=...` - Serve image files

## Architecture

```
ui/
├── app/
│   ├── api/              # API route handlers
│   │   ├── images/       # Image search endpoint
│   │   ├── img/          # Image serving endpoint
│   │   └── tags/         # Tag listing endpoint
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Main UI component
├── lib/
│   ├── config.ts         # Configuration
│   ├── db.ts             # Database queries
│   └── i18n.ts           # Translations
└── *.config.*            # Build configuration
```

## Database Schema

The UI expects these tables in the SQLite database:

- `image_tags` - Main data (image_path, tags, description, etc.)
- `tag_index` - Inverted index (tag → image_id mapping)
- `image_fts` - FTS5 full-text search table

## Security

Image serving is restricted to whitelisted directories (configured in `app/api/img/route.ts`):

```typescript
// Configure via environment variables or use defaults
const DEFAULT_ALLOWED_DIRS = [
  path.join(os.homedir(), 'Downloads'),
  path.join(os.homedir(), '.LocalImageSearch'),
  '/tmp',
];

const ALLOWED_DIRS = process.env.ALLOWED_IMAGE_DIRS
  ? process.env.ALLOWED_IMAGE_DIRS.split(':')
  : DEFAULT_ALLOWED_DIRS;
```

Adjust this list based on your image storage locations.

## Troubleshooting

**Images not displaying (403 errors)**:
- Check that image paths are in the ALLOWED_DIRS whitelist
- For relative paths, verify BASE_DIR in `app/api/img/route.ts`

**Database not found**:
- Verify DB_PATH in `lib/db.ts`
- Ensure the database file exists and has correct permissions

**Build errors**:
- Run `npm install` to install all dependencies
- Check Node.js version (>= 18.17.0)
