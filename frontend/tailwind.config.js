/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: { 950: '#0a0e1a', 900: '#0f1424', 800: '#161d33' },
        cyan: { 400: '#22d3ee', 500: '#06b6d4' },
      },
    },
  },
  plugins: [],
}
