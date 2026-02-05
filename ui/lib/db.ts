import Database from 'better-sqlite3';
import path from 'path';
import os from 'os';
import fs from 'fs';

// Use user home directory for database storage (or /app/data in Docker)
const DATA_DIR = process.env.DB_DATA_DIR ||
  (process.env.NODE_ENV === 'production' && fs.existsSync('/app/data')
    ? '/app/data'  // Docker environment
    : path.join(os.homedir(), '.LocalImageSearch', 'data'));  // Local development

const DB_PATH = path.join(DATA_DIR, 'image_tags.db');

let db: Database.Database;

export function getDb(): Database.Database {
  if (!db) {
    // Ensure data directory exists
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }

    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
  }
  return db;
}

// ─── Types ───────────────────────────────────────────────────
export interface ImageData {
  id: number;
  image_unique_id: string;
  image_path: string;
  tags: string;
  description: string | null;
  model_name: string;
  image_size: string;
  tag_count: number;
  generated_at: string;
  original_width: number | null;
  original_height: number | null;
  image_format: string | null;
  status: string;
  language: string;
}

export interface TagCount {
  tag: string;
  count: number;
}

// ─── Queries ─────────────────────────────────────────────────
export function getAllTags(limit?: number): TagCount[] {
  const db = getDb();
  const sql = `
    SELECT tag, COUNT(*) as count
    FROM tag_index
    GROUP BY tag
    ORDER BY count DESC
    ${limit ? 'LIMIT ?' : ''}
  `;
  return (limit
    ? db.prepare(sql).all(limit)
    : db.prepare(sql).all()
  ) as TagCount[];
}

export function searchImages(query: {
  tags?: string[];
  searchText?: string;
  page?: number;
  limit?: number;
}): { images: ImageData[]; total: number } {
  const db = getDb();
  const { tags = [], searchText, page = 1, limit = 24 } = query;
  const offset = (page - 1) * limit;

  const conditions: string[] = ["status = 'success'"];
  const params: (string | number)[] = [];

  // 多标签 AND 筛选（通过倒排索引）
  if (tags.length > 0) {
    const placeholders = tags.map(() => '?').join(',');
    conditions.push(
      `id IN (
        SELECT image_id FROM tag_index
        WHERE tag IN (${placeholders})
        GROUP BY image_id
        HAVING COUNT(DISTINCT tag) = ?
      )`
    );
    params.push(...tags, tags.length);
  }

  // 全文模糊搜索（搜索框输入）
  if (searchText && searchText.trim()) {
    const like = `%${searchText.trim()}%`;
    conditions.push(
      `(
        id IN (SELECT image_id FROM tag_index WHERE tag LIKE ?)
        OR COALESCE(description, '') LIKE ?
      )`
    );
    params.push(like, like);
  }

  const where = `WHERE ${conditions.join(' AND ')}`;

  const { total } = db.prepare(
    `SELECT COUNT(*) as total FROM image_tags ${where}`
  ).get(...params) as { total: number };

  const images = db.prepare(
    `SELECT * FROM image_tags ${where} ORDER BY generated_at DESC LIMIT ? OFFSET ?`
  ).all(...params, limit, offset) as ImageData[];

  return { images, total };
}
