import { NextResponse } from 'next/server';
import { searchImages } from '@/lib/db';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const tags = url.searchParams.getAll('tag');
  const searchText = url.searchParams.get('search') || '';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '24');

  try {
    const result = searchImages({ tags, searchText, page, limit });
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
