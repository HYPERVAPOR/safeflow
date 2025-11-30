/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          '"Noto Sans"',
          'sans-serif',
          '"Apple Color Emoji"',
          '"Segoe UI Emoji"',
          '"Segoe UI Symbol"',
          '"Noto Color Emoji"',
          'PingFang SC',
          'Microsoft YaHei',
        ],
        'mono': ['JetBrains Mono', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
      },
      colors: {
        // SafeFlow 深色主题配色方案
        'safeflow': {
          // 背景色系
          'bg-primary': '#0F172A',      // 主界面和内容区域的深色背景
          'bg-secondary': '#1E293B',    // 侧边栏、卡片容器或分割区域的深色背景
          'bg-card': '#334155',         // 卡片、弹出框、输入框的背景色
          'bg-tertiary': '#475569',     // 悬停状态背景色
          // 边框和分割线
          'border': '#475569',          // 分割线、输入框边框
          'hover': '#475569',           // 按钮、卡片、列表项的悬停背景色
          // 强调色 - 现代青绿色
          'accent': '#14B8A6',          // 主要操作按钮、选中 Tab、高亮文本、链接
          'accent-hover': '#0D9488',    // 强调色悬停状态（略微加深）
          // 文本色系
          'text-primary': '#F1F5F9',    // 主要正文、标题、最重要的信息
          'text-secondary': '#CBD5E1',  // 次要信息、描述文本、提示信息
          'text-tertiary': '#94A3B8',   // 辅助文本、版权声明、图标默认色
          // 状态色
          'success': '#22C55E',         // 成功通知、状态指示
          'warning': '#F59E0B',         // 警告信息、需要注意的状态
          'error': '#EF4444',           // 错误信息、删除操作按钮
        }
      },
      fontSize: {
        'h1': ['30px', { fontWeight: '700', lineHeight: '1.2' }],     // 1.875rem
        'h2': ['20px', { fontWeight: '600', lineHeight: '1.3' }],     // 1.25rem
        'body': ['16px', { fontWeight: '400', lineHeight: '1.5' }],    // 1rem
        'small': ['14px', { fontWeight: '400', lineHeight: '1.4' }],   // 0.875rem
        'tiny': ['12px', { fontWeight: '400', lineHeight: '1.3' }],    // 0.75rem
      },
      spacing: {
        '18': '4.5rem',    // 72px
        '88': '22rem',     // 352px
        '128': '32rem',    // 512px
      },
      borderRadius: {
        'card': '8px',     // 卡片圆角
        'button': '6px',   // 按钮圆角
      },
      boxShadow: {
        'dark-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'dark-md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'dark-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
      animation: {
        'fade-in': 'fadeIn 1.2s ease-out',
        'loading': 'loading 1s linear infinite',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        loading: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}