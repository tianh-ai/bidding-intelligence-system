/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Grok 风格配色
        grok: {
          bg: '#0A0A0A',
          surface: '#111111',
          border: '#2A2A2A',
          text: '#E5E5E5',
          textMuted: '#A0A0A0',
          accent: '#00D9FF',
          accentHover: '#00B8D4',
          success: '#00E676',
          warning: '#FFD600',
          error: '#FF1744',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
