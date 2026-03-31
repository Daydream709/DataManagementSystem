/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Manrope", "Noto Sans SC", "sans-serif"],
        body: ["Noto Sans SC", "sans-serif"],
      },
      colors: {
        ink: "#102a43",
        mist: "#f3f6f9",
        ocean: "#136f63",
        sand: "#f4dfc8",
        coral: "#ff715b",
      },
      boxShadow: {
        card: "0 10px 25px rgba(16, 42, 67, 0.08)",
      },
    },
  },
  plugins: [],
};
