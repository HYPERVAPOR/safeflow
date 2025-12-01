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
          '"Plus Jakarta Sans"',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
        'mono': ['JetBrains Mono', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
      },
      colors: {
        // Professional Developer Theme - Soft Gray Palette
        'dev': {
          // Background Colors - Soft Gray to Black
          'bg-primary': '#1A1A1A',      // Main background - soft black
          'bg-secondary': '#2A2A2A',    // Secondary background - medium gray
          'bg-tertiary': '#3A3A3A',     // Tertiary background - light gray
          'bg-overlay': '#252525',      // Overlay/panel background
          'bg-surface': '#404040',      // Surface/interactive element background
          // Accent Colors - Subtle Blue/Gray
          'accent': '#6B7280',          // Primary accent - muted blue-gray
          'accent-hover': '#9CA3AF',    // Accent hover state - lighter gray
          'accent-subtle': 'rgba(107, 114, 128, 0.15)', // Subtle accent background
          'accent-subtle-hover': 'rgba(107, 114, 128, 0.25)', // Subtle accent hover
          // Text Colors - Enhanced Gray Hierarchy
          'text-primary': '#D1D5DB',    // Primary text - medium gray (more gray)
          'text-secondary': '#9CA3AF',  // Secondary text - muted gray
          'text-muted': '#6B7280',      // Muted text - dark gray
          'text-subtle': '#4B5563',     // Subtle text/divider - darker gray
          'text-faint': '#374151',      // Very faint text - darkest gray
          // Border & Interactive Colors - Multi-level Gray Hierarchy
          'border': '#2D2D2D',          // Primary border - very dark gray (main borders)
          'border-secondary': '#374151', // Secondary border - dark gray (cards)
          'border-tertiary': '#4B5563', // Tertiary border - medium-dark gray (active states)
          'border-quaternary': '#6B7280', // Quaternary border - medium gray (hover states)
          'border-subtle': '#1A1A1A',   // Subtle border - almost black (dividers)
          'border-accent': '#404040',   // Accent border - light gray (important elements)
          'border-hover': '#5A5A5A',    // Border on hover state - medium gray
          'hover': '#374151',           // Hover background - dark gray
          'active': '#4B5563',          // Active/selected state
          // Status Colors - Subtle Professional Palette
          'success': '#34D399',         // Success state - emerald green
          'success-subtle': 'rgba(52, 211, 153, 0.15)', // Success background
          'error': '#F87171',           // Error state - soft red
          'error-subtle': 'rgba(248, 113, 113, 0.15)', // Error background
          'warning': '#FBBF24',         // Warning state - amber
          'warning-subtle': 'rgba(251, 191, 36, 0.15)', // Warning background
          'info': '#60A5FA',            // Info state - soft blue
          'info-subtle': 'rgba(96, 165, 250, 0.15)', // Info background
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