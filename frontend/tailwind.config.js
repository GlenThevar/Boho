/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          dark: '#0a0d14',
          card: '#111726',
          border: '#1e293b',
          muted: '#64748b',
          accent: '#06b6d4',
          allow: '#10b981',
          deny: '#ef4444',
          warning: '#f59e0b',
        }
      }
    },
  },
  plugins: [],
}
