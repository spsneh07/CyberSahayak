import type { Config } from "tailwindcss";

/*
 * Light, high-contrast public-service palette.
 * Component classes keep their semantic names: `ink-*` are surfaces (950 = page, 900 = cards,
 * 800 = subtle fills, 700/600 = borders), `white` is heading text, `slate-*` are body text shades,
 * `signal` is the primary action colour.
 */
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#f3f5f9", 900: "#ffffff", 800: "#eef2f8", 700: "#dde3ec", 600: "#c3cdda" },
        navy: { DEFAULT: "#0b2447", light: "#19376d" },
        signal: { DEFAULT: "#0b5cad", dim: "#084a8c" },
        white: "#0b2447",
        slate: { 200: "#1e293b", 300: "#334155", 400: "#475569", 500: "#5b6576" },
        safe: "#047857",
        warn: "#b45309",
        danger: "#b91c1c",
        paper: "#ffffff",
      },
      fontFamily: {
        sans: ["\"Segoe UI\"", "\"Noto Sans\"", "\"Noto Sans Devanagari\"", "system-ui", "-apple-system", "Roboto", "Arial", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Consolas", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
