// ─── Application Configuration ────────────────────────────────

export const CONFIG = {
  // API 返回的标签总数（从数据库取TOP N个标签）
  tagApiLimit: 100,

  // 左侧标签云默认显示的标签数量
  tagCloudLimit: 20,

  // 点击"更多"后展示的标签数量上限（不能超过 tagApiLimit）
  tagCloudExpandedLimit: 100,

  // 每页显示图片数
  imagesPerPage: 20,
} as const;
