import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { MicIcon } from "./Icons";

const BARS_PER_SIDE = 24;
const TOTAL_BARS = BARS_PER_SIDE * 2;

const LEFT_PROFILE = [
  0.07, 0.08, 0.08, 0.11, 0.15, 0.12, 0.2, 0.25, 0.18, 0.3, 0.38, 0.44, 0.32,
  0.56, 0.68, 0.5, 0.74, 0.88, 0.62, 0.94, 0.82, 0.72, 0.58, 0.48,
];

const RIGHT_PROFILE = [
  0.52, 0.64, 0.78, 0.88, 0.95, 0.68, 0.82, 0.72, 0.54, 0.62, 0.44, 0.36, 0.48,
  0.34, 0.26, 0.22, 0.28, 0.18, 0.14, 0.12, 0.09, 0.08, 0.08, 0.06,
];

const IDLE_HEIGHTS = [...LEFT_PROFILE, ...RIGHT_PROFILE];

const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

export const MicMorphWave: React.FC<{
  morph?: number;
  scale?: number;
  energy?: number;
  width?: number;
  height?: number;
}> = ({ morph = 0, scale = 1, energy = 1, width = 820, height = 380 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const timeSec = frame / fps;
  const m = clamp01(morph);

  const stageW = 820;
  const stageH = 380;
  const centerX = stageW / 2;
  const centerY = 164;

  const barWidth = mix(3.8, 4.4, m);
  const idleStep = 9.8;
  const idleInnerGap = 132;
  const activeStep = 9.6;
  const activeStartX = centerX - ((TOTAL_BARS - 1) * activeStep) / 2;

  const orbOffsetY = m * 124;
  const orbScale = mix(1, 0.41, m);
  const haloScale = mix(1, 0.32, m);
  const haloOpacity = 1 - m;
  const idleBreath = 1 + Math.sin(frame / 22) * 0.015 * (1 - m);

  const bars = [];
  for (let i = 0; i < TOTAL_BARS; i++) {
    const isLeft = i < BARS_PER_SIDE;
    const idleX = isLeft
      ? centerX - idleInnerGap - (BARS_PER_SIDE - 1 - i) * idleStep
      : centerX + idleInnerGap + (i - BARS_PER_SIDE) * idleStep;
    const activeX = activeStartX + i * activeStep;
    const x = mix(idleX, activeX, m);

    const sideDist = isLeft
      ? (BARS_PER_SIDE - 1 - i) / (BARS_PER_SIDE - 1)
      : (i - BARS_PER_SIDE) / (BARS_PER_SIDE - 1);

    const ambientWave1 = Math.sin(timeSec * 2.4 - sideDist * 5.2);
    const ambientWave2 = Math.cos(timeSec * 1.5 + sideDist * 3.1) * 0.5;
    const ambientFactor =
      0.84 + 0.32 * ((ambientWave1 + ambientWave2 + 1.5) / 3.0);
    const ambientFloor =
      (1 - sideDist * 0.75) *
      (4 + 4 * Math.sin(timeSec * 2.8 - sideDist * 4.5));
    const idleH = Math.max(
      4,
      IDLE_HEIGHTS[i] * 74 * ambientFactor + ambientFloor
    );

    const normCenter =
      Math.abs(i - (TOTAL_BARS - 1) / 2) / ((TOTAL_BARS - 1) / 2);
    const centerEnvelope = Math.pow(1 - normCenter * 0.76, 1.32);

    const wave1 = Math.sin(timeSec * 5.4 - i * 0.34);
    const wave2 = Math.sin(timeSec * 8.8 + i * 0.52) * 0.6;
    const wave3 = Math.cos(timeSec * 3.2 - i * 0.18) * 0.5;
    const syllablePulse =
      0.56 + 0.44 * Math.sin(timeSec * 2.7 + Math.sin(timeSec * 1.3));
    const combined = (wave1 + wave2 + wave3 + 2.1) / 4.2;
    const activeH =
      12 + combined * 124 * energy * centerEnvelope * syllablePulse;

    const barH = Math.max(4, mix(idleH, activeH, m));
    const alpha = mix(0.88, 1.0, m);

    bars.push(
      <rect
        key={i}
        x={x - barWidth / 2}
        y={centerY - barH / 2}
        width={barWidth}
        height={barH}
        rx={barWidth / 2}
        fill="url(#dikteWaveGrad)"
        opacity={alpha}
      />
    );
  }

  return (
    <div
      style={{
        position: "relative",
        width,
        height,
        transform: `scale(${scale})`,
        transformOrigin: "center center",
      }}
    >
      <svg
        width={stageW}
        height={stageH}
        viewBox={`0 0 ${stageW} ${stageH}`}
        style={{
          position: "absolute",
          inset: 0,
          overflow: "visible",
          filter: `drop-shadow(0 0 ${mix(6, 14, m)}px ${theme.colors.glow})`,
        }}
      >
        <defs>
          <linearGradient id="dikteWaveGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={theme.colors.primary} stopOpacity="0.82" />
            <stop offset="50%" stopColor={theme.colors.primaryMid} stopOpacity="1" />
            <stop offset="100%" stopColor={theme.colors.primaryDeep} stopOpacity="0.82" />
          </linearGradient>
        </defs>
        {bars}
      </svg>

      {/* Concentric outer halo rings */}
      <div
        style={{
          position: "absolute",
          top: centerY,
          left: centerX,
          width: 280,
          height: 280,
          transform: `translate(-50%, calc(-50% + ${orbOffsetY}px)) scale(${haloScale * idleBreath})`,
          opacity: haloOpacity,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: 264,
            height: 264,
            borderRadius: "50%",
            transform: "translate(-50%, -50%)",
            border: `1px solid ${theme.colors.haloOuter}`,
            boxShadow: `0 0 40px ${theme.colors.glowSoft}`,
          }}
        />
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: 208,
            height: 208,
            borderRadius: "50%",
            transform: "translate(-50%, -50%)",
            border: `1px solid ${theme.colors.haloInner}`,
            boxShadow: `0 0 30px ${theme.colors.glowSoft}`,
          }}
        />
      </div>

      {/* Main Morphing Orb */}
      <div
        style={{
          position: "absolute",
          top: centerY,
          left: centerX,
          width: 156,
          height: 156,
          borderRadius: "50%",
          transform: `translate(-50%, calc(-50% + ${orbOffsetY}px)) scale(${orbScale * idleBreath})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        {/* Idle Blue Orb Surface */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            opacity: 1 - m,
            border: `1.5px solid ${theme.colors.orbIdleBorder}`,
            background: `radial-gradient(circle at 50% 42%, ${theme.colors.orbIdleTop} 0%, ${theme.colors.orbIdleMid} 58%, ${theme.colors.orbIdleEdge} 100%)`,
            boxShadow: `0 0 44px ${theme.colors.glow}, inset 0 0 26px ${theme.colors.glowSoft}`,
          }}
        />
        {/* Recording Red Orb Surface */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            opacity: m,
            border: `2px solid ${theme.colors.orbRecBorder}`,
            background: `radial-gradient(circle at 50% 45%, ${theme.colors.orbRecTop} 0%, ${theme.colors.orbRecMid} 65%, ${theme.colors.orbRecEdge} 100%)`,
            boxShadow: `0 0 44px ${theme.colors.glowRed}, inset 0 0 24px ${theme.colors.glowRed}`,
          }}
        />

        {/* Icon Morph: Mic SVG -> Red Stop Square */}
        <div
          style={{
            position: "relative",
            width: 56,
            height: 56,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              position: "absolute",
              opacity: Math.max(0, 1 - m * 1.45),
              transform: `scale(${mix(1, 0.35, m)}) rotate(${mix(0, -18, m)}deg)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <MicIcon size={46} color={theme.colors.micIconTint} strokeWidth={1.65} />
          </div>

          <div
            style={{
              position: "absolute",
              width: 52,
              height: 52,
              borderRadius: 12,
              background: `linear-gradient(145deg, ${theme.colors.recordingBright}, ${theme.colors.recordingDark})`,
              boxShadow: `0 0 24px ${theme.colors.glowRed}`,
              opacity: clamp01((m - 0.15) * 1.35),
              transform: `scale(${mix(0.25, 1, m)}) rotate(${mix(18, 0, m)}deg)`,
            }}
          />
        </div>
      </div>
    </div>
  );
};
