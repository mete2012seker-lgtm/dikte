import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { DownloadIcon } from "../components/Icons";
import { Entrance, WordReveal } from "../components/MotionPrimitives";
import { StageScene } from "../components/StageLayers";
import { SCENES, theme } from "../theme";

export const Scene7CTA: React.FC = () => {
  const frame = useCurrentFrame();
  const breath = 1 + Math.sin(frame / 20) * 0.018;

  // Calm ending fade-out to dark canvas over last 16 frames
  const fadeOutOverlay = interpolate(
    frame,
    [SCENES.s7.duration - 16, SCENES.s7.duration - 1],
    [0, 1],
    {
      easing: theme.ease.in,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <StageScene>
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 120px",
          gap: 32,
        }}
      >
        {/* App Icon with Calm Concentric Ring */}
        <Entrance
          delay={2}
          distance={26}
          scaleFrom={0.84}
          springConfig={theme.spring.bouncy}
        >
          <div
            style={{
              position: "relative",
              width: 176,
              height: 176,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "50%",
                border: `1px solid ${theme.colors.haloOuter}`,
                transform: `scale(${breath})`,
              }}
            />
            <div
              style={{
                position: "absolute",
                inset: 18,
                borderRadius: "50%",
                border: `1px solid ${theme.colors.haloInner}`,
                transform: `scale(${breath})`,
              }}
            />
            <Img
              src={staticFile("assets/icon.png")}
              style={{
                width: 112,
                height: 112,
                borderRadius: 28,
                border: `1.5px solid ${theme.colors.lineStrong}`,
                boxShadow: `0 22px 54px ${theme.colors.black65}`,
              }}
            />
          </div>
        </Entrance>

        {/* Hero Title */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 16,
          }}
        >
          <WordReveal
            text="Klavyeyi bırak. Sadece konuş."
            delay={12}
            per={4}
            highlightWord="konuş."
            highlightColor={theme.colors.primaryBright}
            underlineColor={theme.colors.primary}
            wordGapPx={22}
            style={{
              fontSize: 82,
              color: theme.colors.text,
            }}
          />

          <Entrance delay={28} distance={18} scaleFrom={0.97}>
            <div
              style={{
                fontSize: 28,
                fontWeight: 500,
                color: theme.colors.textDim,
              }}
            >
              Dikte — Windows için Yerel Türkçe Sesli Dikte
            </div>
          </Entrance>
        </div>

        {/* Single Glowing CTA Element */}
        <Entrance
          delay={42}
          distance={24}
          scaleFrom={0.92}
          springConfig={theme.spring.snappy}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 18,
            marginTop: 8,
          }}
        >
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 14,
              padding: "20px 40px",
              borderRadius: 999,
              background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.primaryDark})`,
              border: `1.5px solid ${theme.colors.primaryBright}`,
              boxShadow: `0 0 60px ${theme.colors.glow}, 0 0 110px ${theme.colors.glowSoft}`,
              color: theme.colors.text,
              fontFamily: theme.fonts.display,
              fontSize: 28,
              fontWeight: 700,
              letterSpacing: "-0.01em",
              transform: `scale(${breath})`,
            }}
          >
            <DownloadIcon size={26} />
            <span>Ücretsiz İndir  •  v1.6.1</span>
          </div>

          <div
            style={{
              fontFamily: theme.fonts.mono,
              fontSize: 22,
              fontWeight: 500,
              color: theme.colors.accentText,
              letterSpacing: "0.02em",
            }}
          >
            mete2012seker-lgtm.github.io/dikte
          </div>
        </Entrance>
      </div>

      {fadeOutOverlay > 0.001 && (
        <AbsoluteFill
          style={{
            background: theme.colors.bg,
            opacity: fadeOutOverlay,
            pointerEvents: "none",
          }}
        />
      )}
    </StageScene>
  );
};
