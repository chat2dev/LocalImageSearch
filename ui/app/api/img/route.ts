import fs from 'fs';
import path from 'path';
import os from 'os';

// Configure allowed directories via environment variable or use defaults
const DEFAULT_ALLOWED_DIRS = process.env.NODE_ENV === 'production'
  ? [
      '/app/data',
      '/app/downloads',
      '/app/custom_images',
      '/app/tests/fixtures/test_images',
      '/downloads',
      '/tmp',
    ]
  : [
      path.join(os.homedir(), 'Downloads'),
      path.join(os.homedir(), '.LocalImageSearch'),
      '/tmp',
    ];

const ALLOWED_DIRS = process.env.ALLOWED_IMAGE_DIRS
  ? process.env.ALLOWED_IMAGE_DIRS.split(':')
  : DEFAULT_ALLOWED_DIRS;

// Base directory for relative paths (can be configured via environment variable)
const BASE_DIR = process.env.IMAGE_BASE_DIR ||
  (process.env.NODE_ENV === 'production' ? '/app/downloads' : path.join(os.homedir(), 'Downloads'));

export async function GET(request: Request) {
  const url = new URL(request.url);
  const imagePath = url.searchParams.get('path');

  if (!imagePath) {
    return new Response(JSON.stringify({ error: 'Missing path' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // 处理相对路径：如果不是绝对路径，则基于 BASE_DIR 解析
  const absolutePath = path.isAbsolute(imagePath)
    ? imagePath
    : path.join(BASE_DIR, imagePath);

  // 路径安全校验：只允许读取指定目录
  const resolved = path.resolve(absolutePath);
  const allowed = ALLOWED_DIRS.some((dir) => resolved.startsWith(dir));
  if (!allowed) {
    return new Response(JSON.stringify({ error: 'Access denied' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    if (!fs.existsSync(resolved)) {
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const buffer = fs.readFileSync(resolved);
    const ext = path.extname(resolved).toLowerCase();
    const mimeMap: Record<string, string> = {
      '.png': 'image/png',
      '.gif': 'image/gif',
      '.webp': 'image/webp',
      '.bmp': 'image/bmp',
      '.svg': 'image/svg+xml',
    };
    const contentType = mimeMap[ext] || 'image/jpeg';

    return new Response(buffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400',
      },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: String(error) }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
