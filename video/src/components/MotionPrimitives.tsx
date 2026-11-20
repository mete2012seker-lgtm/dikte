import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

export const Entrance: React.FC<{
  delay?: number;
  distance?: number;
  scaleFrom?: number;
  springConfig?: typeof theme.spring.smooth | typeof theme.spring.snappy | typeof theme.spring.bouncy;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({
  delay = 0,
  distance = 32,
  scaleFrom = 0.95,
  springConfig = theme.spring.smooth,
  style,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: springConfig,
  });

  const translateY = interpolate(p, [0, 1], [distance, 0], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(p, [0, 1], [scaleFrom, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        opacity: p,
        transform: `translateY(${translateY}px) scale(${scale})`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const WordReveal: React.FC<{
  text: string;
  delay?: number;
  per?: number;
  highlightWord?: string;
  highlightColor?: string;
  underlineColor?: string;
  wordGapPx?: number;
  align?: "left" | "center";
  style?: React.CSSProperties;
}> = ({
  text,
  delay = 0,
  per = 3,
  highlightWord,
  highlightColor = theme.colors.primary,
  underlineColor,
  wordGapPx = 18,
  align = "center",
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: align === "center" ? "center" : "flex-start",
        columnGap: wordGapPx,
        rowGap: 10,
        fontFamily: theme.fonts.display,
        fontWeight: 700,
        letterSpacing: "-0.03em",
        lineHeight: 1.08,
        ...style,
      }}
    >
      {words.map((word, i) => {
        const wordStart = delay + i * per;
        const p = spring({
          frame: frame - wordStart,
          fps,
          config: theme.spring.snappy,
        });
        const y = interpolate(p, [0, 1], [28, 0], {
          easing: theme.ease.out,
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const scale = interpolate(p, [0, 1], [0.94, 1], {
          easing: theme.ease.out,
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const cleanWord = word.replace(/[.,!?;:]/g, "").toLocaleLowerCase("tr-TR");
        const cleanTarget = highlightWord
          ? highlightWord.replace(/[.,!?;:]/g, "").toLocaleLowerCase("tr-TR")
          : "";
        const isHighlighted = Boolean(cleanTarget && cleanWord === cleanTarget);

        const underlineP = spring({
          frame: frame - (wordStart + 5),
          fps,
          config: theme.spring.snappy,
        });

        return (
          <span
            key={`${word}-${i}`}
            style={{
              position: "relative",
              display: "inline-block",
              opacity: p,
              transform: `translateY(${y}px) scale(${scale})`,
              color: isHighlighted ? highlightColor : undefined,
            }}
          >
            {word}
            {isHighlighted && underlineColor && (
              <span
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  bottom: -4,
                  height: 5,
                  borderRadius: 99,
                  background: underlineColor,
                  transformOrigin: "left center",
                  transform: `scaleX(${underlineP})`,
                  opacity: underlineP,
                }}
              />
            )}
          </span>
        );
      })}
    </div>
  );
};

export const SceneExit: React.FC<{
  durationInFrames: number;
  exitFrames?: number;
  children: React.ReactNode;
}> = ({ durationInFrames, exitFrames = 12, children }) => {
  const frame = useCurrentFrame();
  const start = Math.max(0, durationInFrames - exitFrames);
  const end = Math.max(start + 1, durationInFrames - 2);

  const opacity = interpolate(frame, [start, end], [1, 0], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [start, end], [0, -34], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(frame, [start, end], [1, 0.97], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        opacity,
        transform: `translateY(${translateY}px) scale(${scale})`,
      }}
    >
      {children}
    </div>
  );
};

export const AnimatedCounter: React.FC<{
  target: number;
  delay?: number;
  decimals?: number;
  suffix?: string;
  style?: React.CSSProperties;
}> = ({ target, delay = 0, decimals = 0, suffix = "", style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: { damping: 30, stiffness: 60 },
  });
  const val = interpolate(p, [0, 1], [0, target], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <span style={{ fontVariantNumeric: "tabular-nums", ...style }}>
      {val.toFixed(decimals)}
      {suffix}
    </span>
  );
};
