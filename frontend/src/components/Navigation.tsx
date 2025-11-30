import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavigationItem {
  href: string;
  label: string;
  icon: string;
  active?: boolean;
}

export default function Navigation() {
  const pathname = usePathname();

  const navigationItems: NavigationItem[] = [
    {
      href: '/',
      label: '首页',
      icon: '🏠',
      active: pathname === '/'
    },
    {
      href: '/mcp',
      label: 'MCP Inspector',
      icon: '🔧',
      active: pathname === '/mcp'
    },
    {
      href: '/tools',
      label: '工具管理',
      icon: '🛠️',
      active: pathname === '/tools'
    },
    {
      href: '/tasks',
      label: '任务管理',
      icon: '📋',
      active: pathname === '/tasks'
    },
    {
      href: '/results',
      label: '结果分析',
      icon: '📊',
      active: pathname === '/results'
    },
    {
      href: '/integrations',
      label: '系统集成',
      icon: '🔧',
      active: pathname === '/integrations'
    },
    {
      href: '/settings',
      label: '系统设置',
      icon: '⚙️',
      active: pathname === '/settings'
    }
  ];

  return (
    <nav className="bg-safeflow-bg-secondary border-b border-safeflow-border sticky top-0 z-50 shadow-dark-sm">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center space-x-2">
            <div className="text-2xl">🔧</div>
            <div className="text-h1 text-safeflow-accent">SafeFlow</div>
          </Link>

          <div className="hidden md:flex items-center space-x-6">
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 ${
                  item.active
                    ? 'text-safeflow-text-primary bg-safeflow-accent/20 border border-safeflow-accent/30'
                    : 'text-safeflow-text-secondary hover:text-safeflow-text-primary hover:bg-safeflow-bg-hover'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          {/* API 文档链接 */}
          <div className="hidden md:flex items-center space-x-4">
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-sm"
            >
              📖 API 文档
            </a>
          </div>
        </div>

        {/* 移动端菜单按钮 */}
        <div className="md:hidden">
          <button className="p-2 rounded-md text-safeflow-text-tertiary hover:text-safeflow-text-secondary hover:bg-safeflow-bg-hover transition-colors">
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* 移动端菜单 */}
      {false && (
        <div className="md:hidden border-t border-safeflow-border bg-safeflow-bg-secondary">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm w-full transition-all duration-200 ${
                  item.active
                    ? 'text-safeflow-text-primary bg-safeflow-accent/20 border border-safeflow-accent/30'
                    : 'text-safeflow-text-secondary hover:text-safeflow-text-primary hover:bg-safeflow-bg-hover'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}

            <div className="px-3 py-2">
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary text-sm w-full text-center"
              >
                📖 API 文档
              </a>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}