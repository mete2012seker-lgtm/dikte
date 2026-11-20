import React from "react";
import {
  Img,
  interpolate,
  interpolateColors,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { CursorArrowIcon } from "../components/Icons";
import { Entrance, SceneExit, WordReveal } from "../components/MotionPrimitives";
import { StageScene } from "../components/StageLayers";
import { SCENES, theme } from "../theme";

export const Scene5ThemeToggler: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Circle reveal wipe from top-right theme toggle button (93.8%, 6.8%)
  // Single clean easeInOut curve so the circular expansion is unmistakably visible mid-sweep
  const revealT = interpolate(frame, [90, 134], [0, 1], {
    easing: theme.ease.inOut,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const circleRadiusPct = revealT * 145;

  // Smooth Ken Burns zoom + pan on the framed showcase container (preserves full UI corners/icons)
  const kbScale = interpolate(frame, [0, SCENES.s5.duration], [0.99, 1.04], {
    easing: theme.ease.inOut,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const kbPanX = interpolate(frame, [0, SCENES.s5.duration], [8, -10], {
    easing: theme.ease.inOut,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Cursor approaches the top-right theme button between frames 58 and 86
  const cursorAppear = spring({
    frame: frame - 56,
    fps,
    config: theme.spring.smooth,
  });
  const cursorMove = interpolate(frame, [58, 86], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cursorFadeOut = interpolate(frame, [118, 134], [1, 0], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cursorClick =
    frame >= 85 && frame <= 93
      ? interpolate(frame, [85, 89, 93], [1, 0.78, 1], {
          easing: theme.ease.out,
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  const cursorX = interpolate(cursorMove, [0, 1], [76, 93.8], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cursorY = interpolate(cursorMove, [0, 1], [28, 6.8], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Ripple ring at click point (frame 88..116)
  const rippleP = interpolate(frame, [88, 116], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const rippleScale = interpolate(rippleP, [0, 1], [0.4, 2.8], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const rippleOpacity = interpolate(rippleP, [0, 0.2, 1], [0, 0.9, 0], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const headingColor = interpolateColors(
    revealT,
    [0, 1],
    [theme.colors.text, theme.colors.lightText]
  );
  const subColor = interpolateColors(
    revealT,
    [0, 1],
    [theme.colors.textDim, theme.colors.lightMuted]
  );
  const frameBorderColor = interpolateColors(
    revealT,
    [0, 1],
    [theme.colors.lineStrong, theme.colors.primary]
  );

  return (
    <StageScene lightFactor={revealT}>
      <SceneExit durationInFrames={SCENES.s5.duration} exitFrames={12}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 80px",
            gap: 28,
          }}
        >
          {/* Headline */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 10,
            }}
          >
            <WordReveal
              text="Gözünü yormayan tasarım."
              delay={0}
              per={3}
              highlightWord="tasarım."
              highlightColor={theme.colors.primary}
              wordGapPx={16}
              style={{
                fontSize: 56,
                color: headingColor,
              }}
            />
            <Entrance delay={12} distance={16} scaleFrom={0.97}>
              <div
                style={{
                  fontSize: 23,
                  color: subColor,
                  fontWeight: 500,
                }}
              >
                Sade Dikte.AI veya Klasik Magic UI — tek tıkla dairesel tema geçişi.
              </div>
            </Entrance>
          </div>

          {/* Real App Screenshot Showcase (exact 1280x800 -> 1056x660 aspect ratio) */}
          <Entrance delay={6} distance={30} scaleFrom={0.95}>
            <div
              style={{
                position: "relative",
                width: 1056,
                height: 660,
                borderRadius: 24,
                overflow: "hidden",
                border: `1.5px solid ${frameBorderColor}`,
                boxShadow: `0 34px 86px ${theme.colors.black65}`,
                background: theme.colors.card,
                transform: `scale(${kbScale}) translateX(${kbPanX}px)`,
              }}
            >
              {/* Dark Theme Layer */}
              <Img
                src={staticFile("assets/ekran-dikte-koyu.png")}
                style={{
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />

              {/* AnimatedThemeToggler Light Theme Overlay via circle clip-path */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  clipPath: `circle(${circleRadiusPct}% at 93.8% 6.8%)`,
                  WebkitClipPath: `circle(${circleRadiusPct}% at 93.8% 6.8%)`,
                }}
              >
                <Img
                  src={staticFile("assets/ekran-dikte-acik.png")}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
              </div>

              {/* Click Ripple around Theme Pill */}
              {frame >= 88 && frame <= 116 && (
                <div
                  style={{
                    position: "absolute",
                    left: "93.8%",
                    top: "6.8%",
                    width: 48,
                    height: 48,
                    borderRadius: "50%",
                    border: `2.5px solid ${theme.colors.primary}`,
                    transform: `translate(-50%, -50%) scale(${rippleScale})`,
                    opacity: rippleOpacity,
                    pointerEvents: "none",
                  }}
                />
              )}

              {/* Subtle Animated Pointer */}
              <div
                style={{
                  position: "absolute",
                  left: `${cursorX}%`,
                  top: `${cursorY}%`,
                  opacity: cursorAppear * cursorFadeOut,
                  transform: `translate(-4px, -4px) scale(${cursorClick})`,
                  pointerEvents: "none",
                }}
              >
                <CursorArrowIcon size={30} color={theme.colors.text} />
              </div>
            </div>
          </Entrance>
        </div>
      </SceneExit>
    </StageScene>
  );
};
