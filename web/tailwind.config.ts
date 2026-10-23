// Design tokens: drafting-paper surface, ink text, one signal colour per contract status.
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F3F0E8",
        sheet: "#FBFAF6",
        rule: "#D8D2C4",
        ink: "#16191D",
        graphite: "#5C6168",
        signal: "#C2410C",
        good: "#0F766E",
        lapsed: "#B7791F",
        orphan: "#7C3AED",
        blueprint: "#1E3A5F",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: { sheet: "6px" },
    },
  },
  plugins: [],
} satisfies Config;
