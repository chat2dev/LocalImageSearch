'use client';

import { useState, useEffect, useCallback } from 'react';
import { TRANSLATIONS, type Lang } from '@/lib/i18n';
import { CONFIG } from '@/lib/config';

// ─── Types ────────────────────────────────────────────────────
interface ImageData {
  id: number;
  image_path: string;
  tags: string;
  description: string | null;
  model_name: string;
  tag_count: number;
  generated_at: string;
  original_width: number | null;
  original_height: number | null;
  image_format: string | null;
}

interface TagInfo {
  tag: string;
  count: number;
}

// ─── Tag Color Palette ────────────────────────────────────────
const TAG_COLORS = [
  { bg: '#fee2e2', text: '#b91c1c' },
  { bg: '#fce7f3', text: '#be185d' },
  { bg: '#f3e8ff', text: '#7c3aed' },
  { bg: '#ede9fe', text: '#6d28d9' },
  { bg: '#e0e7ff', text: '#4f46e5' },
  { bg: '#dbeafe', text: '#2563eb' },
  { bg: '#cffafe', text: '#0891b2' },
  { bg: '#ccfbf1', text: '#0d9488' },
  { bg: '#d1fae5', text: '#059669' },
  { bg: '#dcfce7', text: '#16a34a' },
  { bg: '#fef9c3', text: '#ca8a04' },
  { bg: '#ffedd5', text: '#ea580c' },
];

function getTagStyle(tag: string) {
  let h = 0;
  for (let i = 0; i < tag.length; i++) h = ((h << 5) - h + tag.charCodeAt(i)) | 0;
  return TAG_COLORS[Math.abs(h) % TAG_COLORS.length];
}

function imgUrl(p: string) {
  return `/api/img?path=${encodeURIComponent(p)}`;
}

// ─── TagPill ──────────────────────────────────────────────────
function TagPill({
  tag,
  count,
  selected,
  onClick,
  compact,
}: {
  tag: string;
  count?: number;
  selected?: boolean;
  onClick?: () => void;
  compact?: boolean;
}) {
  const { bg, text } = getTagStyle(tag);
  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center gap-1 rounded-full font-medium transition-all duration-150 ${
        onClick ? 'cursor-pointer hover:opacity-80 active:scale-95' : ''
      } ${compact ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-0.5 text-xs'}`}
      style={{
        backgroundColor: selected ? text : bg,
        color: selected ? '#fff' : text,
        boxShadow: selected ? `0 0 0 2px #fff, 0 0 0 3.5px ${text}` : 'none',
      }}
    >
      {tag}
      {count !== undefined && <span className="opacity-60 font-normal">({count})</span>}
    </span>
  );
}

// ─── Placeholder ──────────────────────────────────────────────
function Placeholder() {
  return (
    <div className="flex items-center justify-center w-full h-full bg-slate-100">
      <svg className="w-10 h-10 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.2}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    </div>
  );
}

// ─── ImageCard ────────────────────────────────────────────────
function ImageCard({ image, onClick }: { image: ImageData; onClick: () => void }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const tags = image.tags.split(',').map((t) => t.trim()).filter(Boolean);

  return (
    <div
      onClick={onClick}
      className="group bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md overflow-hidden cursor-pointer transition-all duration-200 hover:-translate-y-1 flex flex-col"
    >
      {/* 图片区域 */}
      <div className="relative aspect-square overflow-hidden bg-slate-100">
        {!error ? (
          <>
            {!loaded && <div className="absolute inset-0 bg-slate-100 animate-pulse" />}
            <img
              src={imgUrl(image.image_path)}
              alt={image.tags}
              onLoad={() => setLoaded(true)}
              onError={() => setError(true)}
              className={`w-full h-full object-cover transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0'}`}
            />
          </>
        ) : (
          <Placeholder />
        )}
        {/* hover 遮层 */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-all duration-200" />
      </div>

      {/* 标签区域 */}
      <div className="p-2.5 flex flex-col gap-1.5 mt-auto">
        <div className="flex flex-wrap gap-1.5">
          {tags.slice(0, 4).map((tag) => (
            <TagPill key={tag} tag={tag} compact />
          ))}
          {tags.length > 4 && (
            <span className="text-[11px] text-slate-400 self-center font-medium">+{tags.length - 4}</span>
          )}
        </div>
        {/* 路径显示 */}
        <p
          className="text-[10px] text-slate-400 truncate font-mono leading-tight"
          title={image.image_path}
        >
          {image.image_path}
        </p>
      </div>
    </div>
  );
}

// ─── ImageModal ───────────────────────────────────────────────
function ImageModal({ image, onClose, lang }: { image: ImageData; onClose: () => void; lang: Lang }) {
  const [error, setError] = useState(false);
  const tags = image.tags.split(',').map((t) => t.trim()).filter(Boolean);
  const fileName = image.image_path.split('/').pop();

  // ESC 关闭
  useEffect(() => {
    const fn = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', fn);
    return () => window.removeEventListener('keydown', fn);
  }, [onClose]);

  // 锁定滚动
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  const t = TRANSLATIONS[lang].modal;
  const meta = [
    { label: t.model, value: image.model_name },
    {
      label: t.size,
      value: image.original_width && image.original_height ? `${image.original_width} × ${image.original_height}` : '—',
    },
    { label: t.format, value: image.image_format || '—' },
    { label: t.tagCount, value: String(image.tag_count) },
    { label: t.generatedAt, value: image.generated_at },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4 py-8" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/55 backdrop-blur-[2px]" />

      {/* Modal 面板 */}
      <div
        className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-full overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 关闭按钮 */}
        <button
          onClick={onClose}
          className="absolute top-2.5 right-2.5 z-10 bg-white/90 backdrop-blur rounded-full p-1.5 shadow-sm hover:bg-slate-100 transition-colors"
        >
          <svg className="w-4.5 h-4.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* 图片 */}
        <div className="rounded-t-2xl overflow-hidden bg-slate-100 flex items-center justify-center" style={{ minHeight: 200 }}>
          {!error ? (
            <img
              src={imgUrl(image.image_path)}
              alt={image.tags}
              onError={() => setError(true)}
              className="w-full object-contain"
              style={{ maxHeight: '55vh' }}
            />
          ) : (
            <div style={{ height: 240 }}>
              <Placeholder />
            </div>
          )}
        </div>

        {/* 信息区 */}
        <div className="p-5">
          {/* 完整路径 */}
          <div className="mb-3">
            <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Path</p>
            <p
              className="text-xs text-slate-600 font-mono bg-slate-50 rounded px-2 py-1.5 break-all"
              title={image.image_path}
            >
              {image.image_path}
            </p>
          </div>

          {/* 标签 */}
          <div className="flex flex-wrap gap-1.5 mb-4">
            {tags.map((tag) => (
              <TagPill key={tag} tag={tag} />
            ))}
          </div>

          {/* 描述 */}
          {image.description && (
            <p className="text-sm text-slate-600 mb-4 bg-slate-50 rounded-lg px-3 py-2">{image.description}</p>
          )}

          {/* 元数据网格 */}
          <div className="grid grid-cols-3 gap-2">
            {meta.map((item) => (
              <div key={item.label} className="bg-slate-50 rounded-lg p-2.5">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">{item.label}</p>
                <p className="text-xs text-slate-700 font-semibold mt-0.5 truncate">{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────
function Skeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="aspect-square bg-slate-100 animate-pulse" />
          <div className="p-2.5 flex gap-1.5">
            <div className="h-5 w-14 bg-slate-100 animate-pulse rounded-full" />
            <div className="h-5 w-10 bg-slate-100 animate-pulse rounded-full" />
            <div className="h-5 w-12 bg-slate-100 animate-pulse rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────
export default function Page() {
  const [allTags, setAllTags] = useState<TagInfo[]>([]);
  const [images, setImages] = useState<ImageData[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
  const [showAllTags, setShowAllTags] = useState(false);
  const [lang, setLang] = useState<Lang>('zh');

  const t = TRANSLATIONS[lang];

  // 用于 useEffect dep 比较的稳定 key
  const tagKey = Array.from(selectedTags).sort().join('\x00');

  // 初始获取TOP标签（使用配置的API限制）
  useEffect(() => {
    fetch(`/api/tags?limit=${CONFIG.tagApiLimit}`)
      .then((r) => r.json())
      .then((data: TagInfo[]) => setAllTags(data))
      .catch(console.error);
  }, []);

  // Search 去重
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchQuery), 280);
    return () => clearTimeout(t);
  }, [searchQuery]);

  // 筛选变化 → 重置分页并拉数据
  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      const params = new URLSearchParams();
      selectedTags.forEach((tag) => params.append('tag', tag));
      if (debouncedSearch) params.set('search', debouncedSearch);
      params.set('page', '1');
      params.set('limit', String(CONFIG.imagesPerPage));

      try {
        const res = await fetch(`/api/images?${params}`);
        const data = await res.json();
        if (cancelled) return;
        setImages(data.images);
        setTotal(data.total);
        setHasMore(data.images.length === CONFIG.imagesPerPage);
        setPage(1);
      } catch (e) {
        console.error(e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tagKey, debouncedSearch]);

  // 加载更多
  const loadMore = useCallback(async () => {
    const next = page + 1;
    const params = new URLSearchParams();
    selectedTags.forEach((tag) => params.append('tag', tag));
    if (debouncedSearch) params.set('search', debouncedSearch);
    params.set('page', String(next));
    params.set('limit', String(CONFIG.imagesPerPage));

    try {
      const res = await fetch(`/api/images?${params}`);
      const data = await res.json();
      setImages((prev) => [...prev, ...data.images]);
      setTotal(data.total);
      setHasMore(data.images.length === CONFIG.imagesPerPage);
      setPage(next);
    } catch (e) {
      console.error(e);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, tagKey, debouncedSearch]);

  const toggleTag = useCallback((tag: string) => {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      next.has(tag) ? next.delete(tag) : next.add(tag);
      return next;
    });
  }, []);

  const clearAll = useCallback(() => {
    setSelectedTags(new Set());
    setSearchQuery('');
  }, []);

  const displayedTags = showAllTags
    ? allTags.slice(0, CONFIG.tagCloudExpandedLimit)
    : allTags.slice(0, CONFIG.tagCloudLimit);

  // 调试日志
  useEffect(() => {
    console.log('🏷️ 标签统计:', {
      总标签数: allTags.length,
      默认显示: CONFIG.tagCloudLimit,
      展开上限: CONFIG.tagCloudExpandedLimit,
      当前展开: showAllTags,
      实际显示: displayedTags.length,
      前5个: displayedTags.slice(0, 5).map(t => `${t.tag}(${t.count})`),
    });
  }, [allTags.length, displayedTags.length, showAllTags]);

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Modal ── */}
      {selectedImage && <ImageModal image={selectedImage} onClose={() => setSelectedImage(null)} lang={lang} />}

      {/* ── Header ── */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-5 py-3 flex items-center gap-4">
          {/* Title */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg className="w-4.5 h-4.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-lg font-bold text-slate-800">{t.title}</h1>
          </div>

          {/* Lang Toggle */}
          <button
            onClick={() => setLang((prev) => (prev === 'zh' ? 'en' : 'zh'))}
            className="flex-shrink-0 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:text-indigo-600 transition-colors rounded border border-slate-300 hover:border-indigo-400"
          >
            {lang === 'zh' ? 'EN' : '中'}
          </button>

          {/* Search */}
          <div className="relative flex-1 max-w-lg">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t.searchPlaceholder}
              className="w-full pl-9 pr-9 py-2 bg-slate-100 border border-slate-200 rounded-lg text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Stats + Clear */}
          <div className="flex items-center gap-3 ml-auto flex-shrink-0">
            <span className="text-sm text-slate-500">
              <span className="font-semibold text-slate-700">{total}</span> {t.imagesUnit}
            </span>
            {(selectedTags.size > 0 || searchQuery) && (
              <button
                onClick={clearAll}
                className="text-xs text-indigo-500 hover:text-indigo-700 font-semibold transition-colors underline underline-offset-2"
              >
                {t.clearButton}
              </button>
            )}
          </div>
        </div>

        {/* 已选标签 */}
        {selectedTags.size > 0 && (
          <div className="max-w-7xl mx-auto px-5 pb-2.5 flex flex-wrap gap-1.5">
            {Array.from(selectedTags).map((tag) => {
              const { bg, text } = getTagStyle(tag);
              return (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold"
                  style={{ backgroundColor: bg, color: text }}
                >
                  {tag}
                  <button onClick={() => toggleTag(tag)} className="opacity-60 hover:opacity-100 transition-opacity">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              );
            })}
          </div>
        )}
      </header>

      {/* ── Body ── */}
      <div className="flex flex-1 max-w-7xl w-full mx-auto px-5 py-5 gap-5">
        {/* ── Sidebar ── */}
        <aside className="w-52 flex-shrink-0">
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 sticky top-20 max-h-[calc(100vh_-_100px)] overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest">{t.tagsTitle}</h2>
              <span className="text-[10px] text-slate-300">{allTags.length} {t.typesUnit}</span>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {/* "全部" 标签 */}
              <TagPill
                key="__all__"
                tag={t.allTag}
                count={total}
                selected={selectedTags.size === 0}
                onClick={() => {
                  setSelectedTags(new Set());
                  setSearchQuery('');
                }}
              />

              {displayedTags.map(({ tag, count }) => (
                <TagPill key={tag} tag={tag} count={count} selected={selectedTags.has(tag)} onClick={() => toggleTag(tag)} />
              ))}
            </div>

            {allTags.length > CONFIG.tagCloudLimit && (
              <button
                onClick={() => setShowAllTags((v) => !v)}
                className="mt-3 text-xs text-indigo-500 hover:text-indigo-700 font-semibold transition-colors"
              >
                {showAllTags
                  ? t.collapseButton
                  : t.moreButton(Math.min(allTags.length - CONFIG.tagCloudLimit, CONFIG.tagCloudExpandedLimit - CONFIG.tagCloudLimit))
                }
              </button>
            )}
          </div>
        </aside>

        {/* ── Grid ── */}
        <main className="flex-1 min-w-0">
          {loading && images.length === 0 ? (
            <Skeleton />
          ) : images.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400">
              <svg className="w-14 h-14 mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm">{t.noResults}</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {images.map((img) => (
                  <ImageCard key={img.id} image={img} onClick={() => setSelectedImage(img)} />
                ))}
              </div>

              {/* Load More */}
              {hasMore && (
                <div className="mt-6 text-center">
                  <button
                    onClick={loadMore}
                    className="px-6 py-2 bg-indigo-500 hover:bg-indigo-600 active:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
                  >
                    {t.loadMore}
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
