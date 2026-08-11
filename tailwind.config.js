/** @type {import('tailwindcss').Config} */
// Paleta "wariant A — butelkowa zieleń + mosiądz". Zmiana palety = tylko ten blok colors.
module.exports = {
  content: [
    './templates/**/*.html',
    './oferty/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#f7f8f7',
        surface: '#ffffff',
        surface2: '#eef1ee',
        border: '#dde3de',
        ink: {
          DEFAULT: '#22312a',
          muted: '#5c6b62',
          subtle: '#8d9a90',
        },
        accent: {
          DEFAULT: '#8f6b21',
          soft: '#b08a35',
          bg: '#f4eeda',
        },
        hot: '#b91c1c',
        success: '#15803d',
        info: '#0369a1',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '6px',
      },
      boxShadow: {
        card: '0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.06)',
        'card-hover': '0 8px 24px -4px rgba(15, 23, 42, 0.12), 0 4px 8px -2px rgba(15, 23, 42, 0.06)',
        search: '0 12px 40px -12px rgba(15, 23, 42, 0.18)',
      },
      letterSpacing: {
        tightest: '-0.025em',
        widest: '0.22em',
      },
      maxWidth: {
        'screen-xl': '1280px',
        narrow: '1100px',
        prose: '760px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
