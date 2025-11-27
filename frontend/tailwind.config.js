/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // NeuralCanvas Theme
        void: '#050505',
        glass: {
          900: 'rgba(15, 23, 42, 0.7)',
        },
        neon: {
          blue: '#3b82f6',
          purple: '#8b5cf6',
          green: '#10b981',
          red: '#ef4444',
        },
        slate: {
          900: '#0f172a',
          200: '#e2e8f0',
        }
      }
    },
  },
  plugins: [],
}
