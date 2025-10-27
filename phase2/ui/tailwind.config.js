// ui/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'rika-blue': '#3B82F6',
        'rika-green': '#10B981',
        'rika-red': '#EF4444',
        'rika-orange': '#F59E0B',
        'rika-purple': '#8B5CF6'
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-gentle': 'bounce 2s infinite'
      }
    },
  },
  plugins: [],
}