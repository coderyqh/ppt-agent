/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bark: {
          50: '#faf6f1',
          100: '#f0e6d8',
          200: '#e0ccaf',
          300: '#d4a574',
          400: '#c48b52',
          500: '#8b7355',
          600: '#6b5a42',
          700: '#4a3f2e',
          800: '#2d261c',
          900: '#1a1610',
        },
        moss: {
          50: '#f0f7f2',
          100: '#d4e8d9',
          200: '#a8d1b3',
          300: '#7cba8d',
          400: '#4a7c59',
          500: '#3a6347',
          600: '#2d4d38',
          700: '#1f3728',
          800: '#132218',
          900: '#0a1309',
        },
        sand: {
          50: '#fffdf9',
          100: '#fff8f0',
          200: '#f5e6d3',
          300: '#e8d0b5',
          400: '#d4b896',
          500: '#c0a078',
          600: '#a08060',
          700: '#806048',
          800: '#604030',
          900: '#402018',
        },
        clay: {
          50: '#fdf5ee',
          100: '#f9e8d5',
          200: '#f0d0aa',
          300: '#d4a574',
          400: '#c08850',
          500: '#a06830',
          600: '#805020',
          700: '#603818',
          800: '#402010',
          900: '#201008',
        },
        cream: '#fff8f0',
        earth: '#6b4423',
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        body: ['Nunito', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'organic': '30% 70% 70% 30% / 30% 30% 70% 70%',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
}
