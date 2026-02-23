import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        salmon: {
          DEFAULT: '#FFAFAF',
          light: '#FFD0D0',
          dim: 'rgba(255,175,175,0.55)',
        },
        periwinkle: {
          DEFAULT: '#AFD7FF',
          light: '#D0E8FF',
          dim: 'rgba(175,215,255,0.55)',
        },
        bg: {
          base: '#07070E',
          surface: '#0D0D1C',
          elevated: '#121225',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'terminal-line': {
          from: { opacity: '0', transform: 'translateX(-8px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        'float-slow': 'float 8s ease-in-out infinite',
        'fade-up': 'fade-up 0.6s ease-out forwards',
        'terminal-line': 'terminal-line 0.4s ease-out forwards',
      },
    },
  },
  plugins: [],
} satisfies Config
