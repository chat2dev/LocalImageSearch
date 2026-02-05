# Web UI Design Document

**LocalImageSearch - Web Interface Architecture**

This document describes the architecture, design patterns, and implementation details of the Next.js-based web interface.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Component Design](#4-component-design)
5. [API Layer](#5-api-layer)
6. [Database Integration](#6-database-integration)
7. [State Management](#7-state-management)
8. [Internationalization](#8-internationalization)
9. [Security](#9-security)
10. [Performance](#10-performance)

---

## 1. Overview

### 1.1 Goals

Provide a modern, user-friendly web interface for browsing and searching tagged images with:

- Bilingual support (Chinese/English)
- Responsive design for desktop and mobile
- Real-time search with multiple filter options
- Efficient pagination and lazy loading
- Secure image serving

### 1.2 Design Principles

| Principle | Description |
|-----------|-------------|
| **Server-Side First** | Use Next.js App Router with server components for SEO and performance |
| **Type Safety** | Leverage TypeScript for type checking and IDE support |
| **Minimal Client JS** | Use server components where possible, client components only when needed |
| **Configurable** | Centralized configuration for easy customization |
| **Secure** | Whitelist-based image serving to prevent path traversal attacks |

---

## 2. Architecture

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Tag Cloud    │  │ Search Bar   │  │ Image Grid   │          │
│  │ (Client)     │  │ (Client)     │  │ (Server)     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │ fetch()          │ fetch()          │ fetch()
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Server (Port 3000)                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routes Layer                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │ /api/tags    │  │ /api/images  │  │ /api/img     │    │  │
│  │  │ (Tag List)   │  │ (Search)     │  │ (Image File) │    │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │  │
│  └─────────┼──────────────────┼──────────────────┼───────────┘  │
│            │                  │                  │              │
│  ┌─────────┼──────────────────┼──────────────────┼───────────┐  │
│  │         │  Database Access Layer              │           │  │
│  │         │                  │                  │           │  │
│  │  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐    │  │
│  │  │ getAllTags() │  │searchImages()│  │ File System  │    │  │
│  │  │              │  │              │  │ (with check) │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  SQLite Database     │
                    │  ~/.LocalImageSearch │
                    │      /data/          │
                    │  image_tags.db       │
                    └──────────────────────┘
```

### 2.2 Directory Structure

```
ui/
├── app/                      # Next.js 14 App Router
│   ├── api/                  # API route handlers
│   │   ├── images/
│   │   │   └── route.ts      # GET /api/images - Search endpoint
│   │   ├── img/
│   │   │   └── route.ts      # GET /api/img - Image file serving
│   │   └── tags/
│   │       └── route.ts      # GET /api/tags - Tag listing
│   ├── globals.css           # Global styles (Tailwind)
│   ├── layout.tsx            # Root layout with metadata
│   └── page.tsx              # Main page (server + client components)
│
├── lib/                      # Core utilities
│   ├── config.ts             # Configuration constants
│   ├── db.ts                 # Database access layer
│   └── i18n.ts               # Translations
│
└── *.config.*                # Build configuration files
```

---

## 3. Technology Stack

### 3.1 Core Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.2+ | React framework with App Router |
| **React** | 18.3+ | UI library with Server Components |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Tailwind CSS** | 3.x | Utility-first CSS framework |
| **better-sqlite3** | 11.x | SQLite3 bindings for Node.js |

### 3.2 Key Features Used

- **Next.js App Router**: File-based routing with server components
- **Server Components**: Default for better performance
- **Client Components**: For interactive UI (search, tag selection)
- **API Routes**: RESTful endpoints with TypeScript
- **Tailwind CSS**: Responsive utility classes

---

## 4. Component Design

### 4.1 Page Structure

```typescript
// app/page.tsx (Hybrid: Server + Client)
export default function HomePage() {
  return (
    <>
      <Header />           {/* Server Component */}
      <SearchUI />         {/* Client Component (interactive) */}
      <ImageGrid />        {/* Server Component (data fetching) */}
    </>
  );
}
```

### 4.2 Component Hierarchy

```
HomePage (Server Component)
│
├── LanguageToggle (Client Component)
│   └── useState for language selection
│
├── SearchBar (Client Component)
│   ├── useState for search query
│   └── onChange handlers
│
├── TagCloud (Client Component)
│   ├── useState for selected tags
│   ├── Tag Pills (interactive)
│   └── Show More/Less toggle
│
├── ImageGrid (Client Component)
│   ├── useEffect for data fetching
│   ├── Infinite scroll detection
│   └── Image Cards
│       └── onClick → Modal
│
└── ImageModal (Client Component)
    ├── Image viewer
    ├── Metadata display
    └── Keyboard navigation
```

### 4.3 Client vs Server Components

**Server Components** (Default):
- Static content rendering
- SEO-friendly metadata
- Direct database access

**Client Components** (`'use client'`):
- Interactive UI elements
- State management (useState, useEffect)
- Event handlers (onClick, onChange)

---

## 5. API Layer

### 5.1 API Endpoints

#### GET /api/tags

**Purpose**: Retrieve top N tags by image count

**Query Parameters**:
```typescript
{
  limit?: number  // Default: CONFIG.tagApiLimit (100)
}
```

**Response**:
```typescript
Array<{
  tag: string;
  count: number;
}>
```

**Example**:
```bash
GET /api/tags?limit=20
# Returns top 20 tags by count
```

#### GET /api/images

**Purpose**: Search images with filters

**Query Parameters**:
```typescript
{
  tags?: string;      // Comma-separated tags (AND filter)
  query?: string;     // Full-text search query
  page?: number;      // Page number (1-indexed)
  limit?: number;     // Images per page
}
```

**Response**:
```typescript
{
  images: Array<ImageData>;
  total: number;
}
```

**Example**:
```bash
GET /api/images?tags=风景,自然&query=山&page=1&limit=20
# Returns images with tags "风景" AND "自然" containing "山"
```

#### GET /api/img

**Purpose**: Serve image files securely

**Query Parameters**:
```typescript
{
  path: string;  // Image file path (absolute or relative)
}
```

**Response**: Binary image data (JPEG/PNG/etc.)

**Security**:
- Path whitelist validation
- No directory traversal
- Relative path resolution

---

## 6. Database Integration

### 6.1 Database Configuration

```typescript
// lib/db.ts
const DATA_DIR = path.join(os.homedir(), '.LocalImageSearch', 'data');
const DB_PATH = path.join(DATA_DIR, 'image_tags.db');
```

**Benefits**:
- User home directory location (`~/.LocalImageSearch/data/`)
- Auto-creation of directory if missing
- Better multi-user support
- Independent of project location

### 6.2 Database Schema

The UI expects these tables:

**image_tags** (Main data):
```sql
CREATE TABLE image_tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_unique_id TEXT,
  image_path TEXT,
  tags TEXT,                    -- Comma-separated tags
  description TEXT,
  model_name TEXT,
  generated_at TIMESTAMP,
  status TEXT DEFAULT 'success',
  language TEXT DEFAULT 'en'
  -- ... more fields
);
```

**tag_index** (Inverted index):
```sql
CREATE TABLE tag_index (
  image_id INTEGER,
  tag TEXT,
  PRIMARY KEY (image_id, tag)
);
```

**image_fts** (Full-text search):
```sql
CREATE VIRTUAL TABLE image_fts USING fts5(
  image_id,
  tags,
  description
);
```

### 6.3 Query Patterns

**Tag Cloud Query**:
```typescript
SELECT tag, COUNT(*) as count
FROM tag_index
GROUP BY tag
ORDER BY count DESC
LIMIT ?;
```

**Multi-tag AND Search**:
```typescript
SELECT * FROM image_tags
WHERE id IN (
  SELECT image_id FROM tag_index
  WHERE tag IN (?, ?, ?)
  GROUP BY image_id
  HAVING COUNT(DISTINCT tag) = 3  -- AND logic
)
ORDER BY generated_at DESC
LIMIT ? OFFSET ?;
```

**Full-text Search**:
```typescript
SELECT * FROM image_tags
WHERE (
  id IN (SELECT image_id FROM tag_index WHERE tag LIKE ?)
  OR description LIKE ?
)
LIMIT ? OFFSET ?;
```

---

## 7. State Management

### 7.1 Client State

The UI uses React hooks for state management:

```typescript
// Main state variables
const [language, setLanguage] = useState<'zh' | 'en'>('zh');
const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
const [searchQuery, setSearchQuery] = useState('');
const [images, setImages] = useState<ImageData[]>([]);
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);
const [showModal, setShowModal] = useState(false);
const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
```

### 7.2 Data Flow

```
User Action → State Update → API Call → Response → State Update → Re-render
```

**Example: Tag Selection**
```typescript
// 1. User clicks tag
onClick={() => {
  const newTags = new Set(selectedTags);
  if (newTags.has(tag)) {
    newTags.delete(tag);  // Toggle off
  } else {
    newTags.add(tag);     // Toggle on
  }
  setSelectedTags(newTags);
  setPage(1);             // Reset pagination
}}

// 2. useEffect triggers API call
useEffect(() => {
  fetchImages();
}, [selectedTags, searchQuery, page]);

// 3. API response updates state
const data = await response.json();
setImages(prev => page === 1 ? data.images : [...prev, ...data.images]);
setHasMore(data.images.length === CONFIG.imagesPerPage);
```

---

## 8. Internationalization

### 8.1 Translation System

```typescript
// lib/i18n.ts
export const TRANSLATIONS = {
  zh: {
    title: '图片检索',
    searchPlaceholder: '搜索标签或描述...',
    // ... more translations
  },
  en: {
    title: 'Image Search',
    searchPlaceholder: 'Search tags or description...',
    // ... more translations
  }
};

export function useTranslation(lang: 'zh' | 'en') {
  return TRANSLATIONS[lang];
}
```

### 8.2 Language Toggle

```typescript
<button onClick={() => setLanguage(lang === 'zh' ? 'en' : 'zh')}>
  {lang === 'zh' ? 'EN' : '中文'}
</button>
```

---

## 9. Security

### 9.1 Image Serving Security

**Threat**: Path traversal attacks (e.g., `../../etc/passwd`)

**Mitigation**:
```typescript
// app/api/img/route.ts
const DEFAULT_ALLOWED_DIRS = [
  path.join(os.homedir(), 'Downloads'),
  path.join(os.homedir(), '.LocalImageSearch'),
  '/tmp',
];

const ALLOWED_DIRS = process.env.ALLOWED_IMAGE_DIRS
  ? process.env.ALLOWED_IMAGE_DIRS.split(':')
  : DEFAULT_ALLOWED_DIRS;

// Validate path
const absolutePath = path.resolve(imagePath);
const isAllowed = ALLOWED_DIRS.some(dir =>
  absolutePath.startsWith(path.resolve(dir))
);

if (!isAllowed) {
  return new Response('Forbidden', { status: 403 });
}
```

### 9.2 Input Validation

- **SQL Injection**: Prevented by parameterized queries
- **XSS**: React auto-escapes content
- **CSRF**: Not needed for read-only API

---

## 10. Performance

### 10.1 Optimization Strategies

| Technique | Implementation |
|-----------|----------------|
| **Server Components** | Use by default for static content |
| **Lazy Loading** | Infinite scroll with pagination |
| **Caching** | SQLite WAL mode, browser caching |
| **Image Optimization** | Native `<img>` with proper sizing |
| **Code Splitting** | Next.js automatic splitting |

### 10.2 Database Performance

- **Indexes**: tag_index for fast tag lookups
- **WAL Mode**: Better concurrency
- **LIMIT/OFFSET**: Pagination for large datasets

### 10.3 Network Optimization

- **API Response Size**: Only return needed fields
- **Image Serving**: Direct file streaming
- **Gzip**: Automatic by Next.js

---

## 11. Configuration

### 11.1 Display Configuration

```typescript
// lib/config.ts
export const CONFIG = {
  tagApiLimit: 100,           // Max tags from API
  tagCloudLimit: 20,          // Default visible tags
  tagCloudExpandedLimit: 100, // Max when expanded
  imagesPerPage: 20,          // Pagination size
} as const;
```

### 11.2 Database Configuration

```typescript
// lib/db.ts
const DATA_DIR = path.join(os.homedir(), '.LocalImageSearch', 'data');
const DB_PATH = path.join(DATA_DIR, 'image_tags.db');
```

### 11.3 Image Path Configuration

```typescript
// app/api/img/route.ts
const DEFAULT_ALLOWED_DIRS = [
  path.join(os.homedir(), 'Downloads'),
  path.join(os.homedir(), '.LocalImageSearch'),
  '/tmp',
];

const ALLOWED_DIRS = process.env.ALLOWED_IMAGE_DIRS
  ? process.env.ALLOWED_IMAGE_DIRS.split(':')
  : DEFAULT_ALLOWED_DIRS;

const BASE_DIR = process.env.IMAGE_BASE_DIR || path.join(os.homedir(), 'Downloads');
```

---

## 12. Future Enhancements

### 12.1 Planned Features

- [ ] User authentication
- [ ] Image upload and tagging
- [ ] Batch operations (delete, re-tag)
- [ ] Advanced filters (date range, model, language)
- [ ] Export search results
- [ ] Tag management (merge, rename, delete)
- [ ] Semantic search integration (FAISS)
- [ ] Mobile app (React Native)

### 12.2 Technical Debt

- [ ] Add comprehensive tests (Jest, Playwright)
- [ ] Implement error boundaries
- [ ] Add loading states and skeletons
- [ ] Improve accessibility (ARIA labels)
- [ ] Add analytics and monitoring

---

## 13. Deployment

### 13.1 Development

```bash
cd ui
npm install
npm run dev
```

### 13.2 Production

```bash
npm run build
npm start
```

### 13.3 Docker

See `docker-compose.yml` for containerized deployment.

---

**Document Version**: 1.0
**Last Updated**: 2026-02-05
**Author**: Claude Code Assistant
