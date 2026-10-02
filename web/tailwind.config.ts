import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        "surface-elevated": "var(--color-surface-elevated)",
        "surface-highlight": "var(--color-surface-highlight)",
        spark: "var(--color-spark)",
        "spark-glow": "var(--color-spark-glow)",
        friction: "var(--color-friction)",
        "friction-glow": "var(--color-friction-glow)",
        accent: "var(--color-accent)",
        "accent-glow": "var(--color-accent-glow)",
        ink: "var(--color-ink)",
        muted: "var(--color-muted)",
        "muted-dark": "var(--color-muted-dark)",
        hairline: "var(--color-hairline)",
        "hairline-bright": "var(--color-hairline-bright)",
        brand: {
          blue: "#2563EB",
          orange: "#EA580C",
        },
      },
      fontFamily: {
        sans: ["'Inter Tight Variable'", "Inter Tight", "system-ui", "-apple-system", "sans-serif"],
        display: ["'Inter Tight Variable'", "Inter Tight", "system-ui", "-apple-system", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      fontSize: {
        dense: ["13px", { lineHeight: "1.45" }],
        micro: ["11px", { lineHeight: "1.3" }],
        body: ["15px", { lineHeight: "1.5" }],
      },
      letterSpacing: {
        tightest: "-0.04em",
        tight: "-0.02em",
      },
      borderRadius: {
        card: "20px",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        "glass-inset": "inset 0 1px 0 0 rgba(255, 255, 255, 0.08)",
        "spark-glow": "0 0 20px -3px rgba(124, 255, 178, 0.4)",
        "friction-glow": "0 0 20px -3px rgba(255, 92, 122, 0.4)",
        "accent-glow": "0 0 20px -3px rgba(139, 139, 255, 0.4)",
      },
      keyframes: {
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        pulseSlow: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.4", transform: "scale(0.96)" },
        },
        conicSpin: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        shimmer: "shimmer 2s infinite",
        "pulse-slow": "pulseSlow 3s ease-in-out infinite",
        "conic-spin": "conicSpin 4s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
