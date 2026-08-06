/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  corePlugins: {
    preflight: false,
  },
  theme: {
    extend: {
      colors: {
        ivory: '#fbf9f2',
        navy: '#111c4e',
        violet: '#7657ff',
        electric: '#2878ff',
      },
      boxShadow: {
        soft: '0 24px 70px rgba(31, 41, 105, 0.10)',
      },
      fontFamily: {
        display: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
};
