import { NextResponse } from 'next/server';
import { getAllTags } from '@/lib/db';
import { CONFIG } from '@/lib/config';

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const limitParam = url.searchParams.get('limit');
    // 使用配置的 API 限制，或者 URL 参数（不超过配置上限）
    const limit = limitParam
      ? Math.min(parseInt(limitParam), CONFIG.tagApiLimit)
      : CONFIG.tagApiLimit;

    const tags = getAllTags(limit);
    return NextResponse.json(tags);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
