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
        // Semantic theme tokens (resolve via CSS custom properties)
        page:   'var(--color-page-bg)',
        card:   'var(--color-card-bg)',
        border: 'var(--color-border)',
        muted:  'var(--color-muted)',
        hover:  'var(--color-hover)',
        input:  'var(--color-input-bg)',

        // Static brand palette
        cyber: {
          dark:    '#0a0d14',
          card:    '#111726',
          border:  '#1e293b',
          muted:   '#64748b',
          accent:  '#06b6d4',
          allow:   '#10b981',
          deny:    '#ef4444',
          warning: '#f59e0b',
        },
      },
      textColor: {
        page:  'var(--color-page-text)',
        card:  'var(--color-card-text)',
        muted: 'var(--color-muted)',
      },
      backgroundColor: {
        page:  'var(--color-page-bg)',
        card:  'var(--color-card-bg)',
        hover: 'var(--color-hover)',
        input: 'var(--color-input-bg)',
      },
      borderColor: {
        border: 'var(--color-border)',
      },
    },
  },
  plugins: [],
}
