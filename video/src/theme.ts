import { Easing } from "remotion";

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const TOTAL_FRAMES = 1350; // 45s @ 30fps

export const SCENES = {
  s1: { from: 0, duration: 180 }, // 0:00 - 0:06 Hook: Writing is slow/hard
  s2: { from: 180, duration: 180 }, // 0:06 - 0:12 Voice flow + 3.5x speed
  s3: { from: 360, duration: 240 }, // 0:12 - 0:20 Push-to-talk + Morph + Auto-paste
  s4: { from: 600, duration: 210 }, // 0:20 - 0:27 AI Clean & Translate
  s5: { from: 810, duration: 210 }, // 0:27 - 0:34 AnimatedThemeToggler (Dark -> Light)
  s6: { from: 1020, duration: 180 }, // 0:34 - 0:40 BentoGrid + MagicCard
  s7: { from: 1200, duration: 150 }, // 0:40 - 0:45 Calm CTA
} as const;

export const theme = {
  colors: {
    bg: "#060A14",
    app: "#080D1A",
    side: "#070B16",
    card: "#0C1322",
    inner: "#0A1120",
    elevated: "#111A2E",
    line: "#1B2740",
    lineSoft: "#141E33",
    lineStrong: "#2A3A5C",
    primary: "#4C6BFF",
    primaryBright: "#6E8CFF",
    primaryMid: "#7498FF",
    primaryDeep: "#3B59D4",
    primaryDark: "#3D5BF5",
    accent: "#6C5DF7",
    accentText: "#9DB2FF",
    text: "#E9EEF9",
    textDim: "#A7B2C9",
    textMuted: "#6E7B96",
    ready: "#2ED47A",
    readyBg: "rgba(46, 212, 122, 0.14)",
    readyBorder: "rgba(46, 212, 122, 0.36)",
    recording: "#EF5B5B",
    recordingBright: "#FF4D5A",
    recordingDark: "#DC2626",
    warning: "#F2B23E",
    warningBg: "rgba(242, 178, 62, 0.12)",
    warningBorder: "rgba(242, 178, 62, 0.34)",
    errorSoft: "rgba(239, 91, 91, 0.16)",
    errorBorder: "rgba(239, 91, 91, 0.48)",
    lightBg: "#F7F9FD",
    lightCard: "#FFFFFF",
    lightText: "#101828",
    lightMuted: "#475467",
    orbIdleTop: "#243B85",
    orbIdleMid: "#13204A",
    orbIdleEdge: "#0A1026",
    orbIdleBorder: "rgba(132, 168, 255, 0.88)",
    orbRecTop: "#2A121B",
    orbRecMid: "#170A12",
    orbRecEdge: "#0C070C",
    orbRecBorder: "rgba(239, 68, 68, 0.72)",
    micIconTint: "#C8D6F4",
    glow: "rgba(76, 107, 255, 0.42)",
    glowStrong: "rgba(76, 107, 255, 0.65)",
    glowSoft: "rgba(76, 107, 255, 0.16)",
    glowRed: "rgba(239, 68, 68, 0.42)",
    haloOuter: "rgba(100, 140, 255, 0.14)",
    haloInner: "rgba(110, 150, 255, 0.24)",
    dotGrid: "rgba(157, 178, 255, 0.14)",
    surfaceOverlay: "rgba(12, 19, 34, 0.88)",
    keyTop: "#17223B",
    keyBottom: "#0E1629",
    keySide: "#070B16",
    white04: "rgba(255, 255, 255, 0.04)",
    white08: "rgba(255, 255, 255, 0.08)",
    white14: "rgba(255, 255, 255, 0.14)",
    black40: "rgba(0, 0, 0, 0.40)",
    black65: "rgba(0, 0, 0, 0.65)",
    transparent: "transparent",
  },
  fonts: {
    display: "'Plus Jakarta Sans', sans-serif",
    body: "'Inter', sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  ease: {
    out: Easing.bezier(0.16, 1, 0.3, 1),
    inOut: Easing.bezier(0.83, 0, 0.17, 1),
    in: Easing.bezier(0.7, 0, 0.84, 0),
    morph: Easing.bezier(0.22, 1, 0.36, 1),
  },
  spring: {
    snappy: { damping: 14, stiffness: 160, mass: 0.6 },
    smooth: { damping: 20, stiffness: 90, mass: 1 },
    bouncy: { damping: 11, stiffness: 170, mass: 0.7 },
  },
} as const;
