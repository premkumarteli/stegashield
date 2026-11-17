import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#07131D",
        foreground: "#E5F1F3",
        abyss: {
          DEFAULT: "#07131D",
          deep: "#040B11",
          elevated: "#0B1D2A",
        },
        ocean: {
          DEFAULT: "#102631",
          light: "#183949",
          dark: "#0B1A22",
        },
        teal: {
          liquid: "#36D6C3",
          hover: "#2cb8a7",
          glow: "rgba(54, 214, 195, 0.35)",
        },
        mint: {
          DEFAULT: "#91F3E6",
          ice: "#B7F8F0",
        },
        iris: {
          DEFAULT: "#9B91F5",
          muted: "rgba(155, 145, 245, 0.4)",
        },
        frost: {
          DEFAULT: "#E5F1F3",
          muted: "#91A9B2",
          dim: "#5B7480",
        },
        glass: {
          border: "rgba(255, 255, 255, 0.10)",
          borderHover: "rgba(54, 214, 195, 0.30)",
          highlight: "rgba(255, 255, 255, 0.05)",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      boxShadow: {
        "glass-sm": "0 2px 12px rgba(0, 0, 0, 0.2)",
        "glass-md": "0 8px 32px rgba(0, 0, 0, 0.35)",
        "glass-lg": "0 12px 48px rgba(0, 0, 0, 0.5)",
        "teal-glow": "0 0 25px rgba(54, 214, 195, 0.35)",
        "teal-glow-lg": "0 0 45px rgba(54, 214, 195, 0.5)",
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "liquid-shimmer": "shimmer 2.5s linear infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
