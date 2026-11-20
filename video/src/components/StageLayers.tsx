import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { theme } from "../theme";

export const BgMesh: React.FC<{ lightFactor?: number }> = ({ lightFactor = 0 }) => {
  const frame = useCurrentFrame();
  const d1 = Math.sin(frame / 55) * 48;
  const d2 = Math.cos(frame / 70) * 38;
  const bgOpacityLight = interpolate(lightFactor, [0, 1], [0, 0.92], {
    easing: theme.ease.inOut,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: theme.colors.bg, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          width: 1280,
          height: 1280,
          borderRadius: "50%",
          top: -480,
          left: -260 + d1,
          filter: "blur(72px)",
          background: `radial-gradient(circle, ${theme.colors.primary}2E, ${theme.colors.transparent} 64%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 980,
          height: 980,
          borderRadius: "50%",
          bottom: -420,
          right: -200 - d2,
          filter: "blur(84px)",
          background: `radial-gradient(circle, ${theme.colors.accent}24, ${theme.colors.transparent} 66%)`,
        }}
      />
      {/* Subtle radial dot grid inspired by Dikte DotPattern */}
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(${theme.colors.dotGrid} 1.4px, ${theme.colors.transparent} 1.4px)`,
          backgroundSize: "30px 30px",
          maskImage:
            "radial-gradient(ellipse 82% 72% at 50% 45%, #000 35%, transparent 100%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 82% 72% at 50% 45%, #000 35%, transparent 100%)",
          opacity: 0.72,
        }}
      />
      {bgOpacityLight > 0.001 && (
        <AbsoluteFill
          style={{
            background: theme.colors.lightBg,
            opacity: bgOpacityLight,
          }}
        />
      )}
    </AbsoluteFill>
  );
};

export const ColorGrade: React.FC<{ opacity?: number }> = ({ opacity = 0.16 }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill
      style={{
        backgroundColor: theme.colors.primary,
        mixBlendMode: "soft-light",
        opacity,
      }}
    />
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${theme.colors.black40}, ${theme.colors.transparent} 26%, ${theme.colors.transparent} 74%, ${theme.colors.black40})`,
        opacity: 0.35,
      }}
    />
  </AbsoluteFill>
);

export const Grain: React.FC<{ isLight?: boolean }> = ({ isLight = false }) => {
  const frame = useCurrentFrame();
  const noise = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E")`;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        backgroundImage: noise,
        backgroundSize: "220px",
        backgroundPosition: `${(frame * 7) % 220}px ${(frame * 13) % 220}px`,
        opacity: isLight ? 0.03 : 0.045,
        mixBlendMode: isLight ? "multiply" : "overlay",
      }}
    />
  );
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.28 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      background: `radial-gradient(ellipse at center, ${theme.colors.transparent} 58%, rgba(0, 0, 0, ${strength}) 100%)`,
    }}
  />
);

export const StageScene: React.FC<{
  children: React.ReactNode;
  lightFactor?: number;
}> = ({ children, lightFactor = 0 }) => {
  const gradeOpacity = interpolate(lightFactor, [0, 1], [0.16, 0.08], {
    easing: theme.ease.inOut,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const vignetteStrength = interpolate(lightFactor, [0, 1], [0.3, 0.14], {
    easing: theme.ease.inOut,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        fontFamily: theme.fonts.body,
        color: theme.colors.text,
        overflow: "hidden",
      }}
    >
      {/* Layer 1: Background mesh + DotPattern */}
      <BgMesh lightFactor={lightFactor} />
      {/* Layers 2 & 3: Assets, UI & Typography */}
      <AbsoluteFill>{children}</AbsoluteFill>
      {/* Layer 4: Color grade */}
      <ColorGrade opacity={gradeOpacity} />
      {/* Layer 5: Grain + Vignette */}
      <Grain isLight={lightFactor > 0.5} />
      <Vignette strength={vignetteStrength} />
    </AbsoluteFill>
  );
};
