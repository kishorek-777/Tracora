/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        tracora: {
          void: '#050811',
          bg: '#080c18',
          surface: '#0c1222',
          card: '#0f172a',
          'card-hover': '#141f36',
          border: 'rgba(56, 189, 248, 0.12)',
          'border-subtle': '#1e293b',
          'border-focus': 'rgba(0, 229, 255, 0.4)',
          cyan: '#00e5ff',
          'cyan-glow': 'rgba(0, 229, 255, 0.15)',
          blue: '#2563eb',
          'blue-dark': '#1d4ed8',
          indigo: '#6366f1',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
          muted: '#64748b',
          text: '#f8fafc',
          'text-secondary': '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -3px rgba(0, 229, 255, 0.25)',
        'glow-blue': '0 0 25px -4px rgba(37, 99, 235, 0.3)',
        'glow-card': '0 8px 32px 0 rgba(0, 0, 0, 0.45)',
        'hud-badge': '0 0 12px rgba(0, 229, 255, 0.2)',
      },
      backgroundImage: {
        'grid-pattern': 'radial-gradient(circle, rgba(56, 189, 248, 0.07) 1px, transparent 1px)',
      }
    },
  },
  plugins: [],
}
