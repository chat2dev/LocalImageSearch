import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '图片标签检索',
  description: '基于倒排索引的图片分类检索系统',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh">
      <body className="min-h-screen bg-slate-50" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
