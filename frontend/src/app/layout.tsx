import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SafeFlow - 智能测试平台',
  description: '基于 LLM Agent 的智能测试平台接入系统',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased">
        <div className="min-h-screen bg-safeflow-bg-primary">
          {children}
        </div>
      </body>
    </html>
  );
}