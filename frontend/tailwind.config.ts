import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#dc2626",
          dark: "#7f1d1d",
          light: "#fecaca",
        },
        gold: {
          DEFAULT: "#facc15",
          dark: "#a16207",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
