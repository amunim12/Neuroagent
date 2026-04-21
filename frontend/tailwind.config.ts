import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#07080E",
        elevated: "#0C0F1A",
        panel: "#10131F",
        overlay: "#151A2E",
        border: "#1C2340",
        "border-bright": "#2A3558",
        accent: "#6366F1",
        "accent-light": "#818CF8",
        "accent-dim": "#312E81",
        fore: "#EEF2FF",
        "fore-muted": "#9CA3AF",
        "fore-subtle": "#6B7280",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        "glow-sm": "0 0 12px rgba(99,102,241,0.25)",
        "glow-md": "0 0 28px rgba(99,102,241,0.4)",
        "panel": "0 4px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04)",
      },
      backgroundImage: {
        "gradient-accent": "linear-gradient(135deg, #6366F1, #8B5CF6)",
        "dot-grid": "radial-gradient(circle, rgba(99,102,241,0.12) 1px, transparent 1px)",
      },
      backgroundSize: {
        "dot-grid": "28px 28px",
      },
      animation: {
        "slide-up": "slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1)",
        "fade-in": "fadeIn 0.25s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "shimmer": "shimmer 1.8s linear infinite",
        "bounce-dot": "bounceDot 1.4s ease-in-out infinite",
        "flow-in": "flowIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        slideUp: {
          "0%": { transform: "translateY(16px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 8px rgba(99,102,241,0.3)" },
          "50%": { boxShadow: "0 0 24px rgba(99,102,241,0.6)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        bounceDot: {
          "0%, 80%, 100%": { transform: "scale(0.4)", opacity: "0.3" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
        flowIn: {
          "0%": { transform: "translateX(-8px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
