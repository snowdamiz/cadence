import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        salmon: {
          DEFAULT: '#FFAFAF',
          light: '#FFD0D0',
        },
        periwinkle: {
          DEFAULT: '#AFD7FF',
          light: '#D0E8FF',
        },
        bg: {
          base: '#07070E',
          surface: '#0D0D1C',
          elevated: '#121225',
          card: '#161632',
        },
        border: {
          subtle: '#1A1A30',
          DEFAULT: '#252545',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'Monaco', 'monospace'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'scroll-down': 'scroll-down 1.5s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        'scroll-down': {
          '0%': { opacity: '1', transform: 'translateY(0)' },
          '100%': { opacity: '0', transform: 'translateY(8px)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
