import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

export const ShineBorderCard: React.FC<{
  shineActive?: number;
  borderRadius?: number;
  padding?: number | string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ shineActive = 0, borderRadius = 22, padding = 28, style, children }) => {
  const frame = useCurrentFrame();
  const angle = (frame * 5.2) % 360;
  const clampedActive = Math.max(0, Math.min(1, shineActive));

  return (
    <div
      style={{
        position: "relative",
        borderRadius,
        background: theme.colors.card,
        border: `1px solid ${theme.colors.line}`,
        boxShadow:
          clampedActive > 0.05
            ? `0 24px 60px ${theme.colors.black65}, 0 0 ${46 * clampedActive}px ${theme.colors.glowSoft}`
            : `0 24px 60px ${theme.colors.black65}`,
        padding,
        overflow: "hidden",
        ...style,
      }}
    >
      {/* Rotating conic ShineBorder */}
      {clampedActive > 0.01 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius,
            padding: 2,
            background: `conic-gradient(from ${angle}deg, ${theme.colors.transparent} 0deg, ${theme.colors.primary} 65deg, ${theme.colors.accent} 115deg, ${theme.colors.transparent} 185deg)`,
            opacity: clampedActive,
            WebkitMask:
              "linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)",
            WebkitMaskComposite: "xor",
            maskComposite: "exclude",
            pointerEvents: "none",
          }}
        />
      )}
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
};

export const MagicCard: React.FC<{
  glowIntensity?: number;
  spotX?: number;
  spotY?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({
  glowIntensity = 0,
  spotX = 50,
  spotY = 30,
  style,
  children,
}) => {
  const active = Math.max(0, Math.min(1, glowIntensity));
  return (
    <div
      style={{
        position: "relative",
        borderRadius: 24,
        background: theme.colors.card,
        border: `1px solid ${
          active > 0.3 ? theme.colors.primary : theme.colors.line
        }`,
        boxShadow:
          active > 0.15
            ? `0 20px 50px ${theme.colors.black65}, 0 0 ${48 * active}px ${theme.colors.glowSoft}`
            : `0 18px 44px ${theme.colors.black40}`,
        padding: "32px 34px",
        overflow: "hidden",
        ...style,
      }}
    >
      {/* Moving radial spotlight following MagicCard spec */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          opacity: active * 0.9,
          background: `radial-gradient(360px circle at ${spotX}% ${spotY}%, ${theme.colors.glowSoft}, ${theme.colors.transparent} 72%)`,
        }}
      />
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
};

export const AnimatedListItem: React.FC<{
  delay?: number;
  icon: React.ReactNode;
  text: string;
  accent?: "ready" | "primary";
}> = ({ delay = 0, icon, text, accent = "ready" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: theme.spring.snappy,
  });

  const y = interpolate(p, [0, 1], [18, 0], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(p, [0, 1], [0.94, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const borderColor =
    accent === "ready" ? theme.colors.readyBorder : theme.colors.lineStrong;
  const iconBg =
    accent === "ready" ? theme.colors.readyBg : theme.colors.glowSoft;
  const iconColor =
    accent === "ready" ? theme.colors.ready : theme.colors.primaryBright;

  return (
    <div
      style={{
        opacity: p,
        transform: `translateY(${y}px) scale(${scale})`,
        display: "flex",
        alignItems: "center",
        gap: 14,
        padding: "12px 18px",
        borderRadius: 14,
        background: theme.colors.card,
        border: `1px solid ${borderColor}`,
        boxShadow: `0 10px 26px ${theme.colors.black40}`,
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 10,
          background: iconBg,
          color: iconColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <span
        style={{
          fontFamily: theme.fonts.body,
          fontSize: 18,
          fontWeight: 500,
          color: theme.colors.text,
          letterSpacing: "-0.01em",
        }}
      >
        {text}
      </span>
    </div>
  );
};

export const Keycap3D: React.FC<{
  label: string;
  sublabel?: string;
  pressed?: number;
}> = ({ label, sublabel, pressed = 0 }) => {
  const p = Math.max(0, Math.min(1, pressed));
  const pressY = interpolate(p, [0, 1], [0, 10], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bottomLip = interpolate(p, [0, 1], [14, 4], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "relative",
        width: 248,
        height: 112,
        paddingBottom: 14,
      }}
    >
      {/* Keycap Base / Housing */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: 22,
          background: theme.colors.keySide,
          border: `1px solid ${
            p > 0.35 ? theme.colors.primary : theme.colors.lineStrong
          }`,
          boxShadow:
            p > 0.35
              ? `0 22px 46px ${theme.colors.black65}, 0 0 ${38 * p}px ${theme.colors.glow}`
              : `0 24px 48px ${theme.colors.black65}`,
        }}
      />
      {/* Keycap Top Surface */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: 98,
          transform: `translateY(${pressY}px)`,
          borderRadius: 20,
          background: `linear-gradient(180deg, ${theme.colors.keyTop} 0%, ${theme.colors.keyBottom} 100%)`,
          border: `1.5px solid ${
            p > 0.35 ? theme.colors.primaryBright : theme.colors.lineStrong
          }`,
          boxShadow: `0 ${bottomLip}px 0 ${theme.colors.keySide}, inset 0 1px 0 ${theme.colors.white14}`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
        }}
      >
        <span
          style={{
            fontFamily: theme.fonts.display,
            fontSize: 28,
            fontWeight: 700,
            color: p > 0.35 ? theme.colors.text : theme.colors.textDim,
            letterSpacing: "-0.02em",
          }}
        >
          {label}
        </span>
        {sublabel && (
          <span
            style={{
              fontFamily: theme.fonts.mono,
              fontSize: 13,
              fontWeight: 500,
              color: p > 0.35 ? theme.colors.accentText : theme.colors.textMuted,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            {sublabel}
          </span>
        )}
      </div>
    </div>
  );
};
