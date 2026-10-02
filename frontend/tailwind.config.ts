import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#060b14", 900: "#0b1220", 800: "#111a2c", 700: "#1a2540", 600: "#26345a" },
        signal: { DEFAULT: "#22d3ee", dim: "#0e7490" },
        safe: "#34d399",
        warn: "#fbbf24",
        danger: "#f87171",
      },
      fontFamily: { mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"] },
    },
  },
  plugins: [],
} satisfies Config;
