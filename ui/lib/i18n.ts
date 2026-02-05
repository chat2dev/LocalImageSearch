// ─── i18n Configuration ───────────────────────────────────────
export const TRANSLATIONS = {
  zh: {
    title: '图片检索',
    searchPlaceholder: '搜索标签或描述...',
    imagesUnit: '张',
    clearButton: '清除',
    tagsTitle: '标签',
    typesUnit: '种',
    allTag: '全部',
    collapseButton: '收起',
    moreButton: (n: number) => `+${n} 更多`,
    noResults: '没有找到匹配的图片',
    loadMore: '加载更多',
    modal: {
      model: '模型',
      size: '尺寸',
      format: '格式',
      tagCount: '标签数',
      generatedAt: '生成时间',
    },
  },
  en: {
    title: 'Image Search',
    searchPlaceholder: 'Search tags or description...',
    imagesUnit: 'images',
    clearButton: 'Clear',
    tagsTitle: 'Tags',
    typesUnit: 'types',
    allTag: 'All',
    collapseButton: 'Collapse',
    moreButton: (n: number) => `+${n} more`,
    noResults: 'No matching images found',
    loadMore: 'Load more',
    modal: {
      model: 'Model',
      size: 'Size',
      format: 'Format',
      tagCount: 'Tags',
      generatedAt: 'Generated',
    },
  },
} as const;

export type Lang = keyof typeof TRANSLATIONS;

export function getTranslations(lang: Lang) {
  return TRANSLATIONS[lang];
}
