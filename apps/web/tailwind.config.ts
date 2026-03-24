import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
    "../../packages/contracts/src/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f4f7f7",
          100: "#e5ecec",
          200: "#c9d7d7",
          300: "#a4bbbb",
          400: "#799696",
          500: "#5a7778",
          600: "#455d5f",
          700: "#334446",
          800: "#1d2b2d",
          900: "#101819",
          950: "#081012"
        },
        saffron: {
          50: "#fff8ec",
          100: "#ffefcf",
          200: "#ffdca1",
          300: "#ffc36a",
          400: "#ffaa3a",
          500: "#f98f12",
          600: "#d97706",
          700: "#ad5d06",
          800: "#8c490a",
          900: "#743d0e"
        }
      },
      boxShadow: {
        card: "0 24px 70px -40px rgba(8, 16, 18, 0.45)",
        lift: "0 20px 40px -24px rgba(8, 16, 18, 0.35)"
      },
      backgroundImage: {
        "court-grid":
          "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;
