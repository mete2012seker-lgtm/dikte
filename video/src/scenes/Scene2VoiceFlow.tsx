import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { KeyboardIcon, MicIcon } from "../components/Icons";
import { MicMorphWave } from "../components/MicMorphWave";
import {
  AnimatedCounter,
  Entrance,
  SceneExit,
  WordReveal,
} from "../components/MotionPrimitives";
import { StageScene } from "../components/StageLayers";
import { SCENES, theme } from "../theme";

export const Scene2VoiceFlow: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const keyboardBarWidth = interpolate(frame, [66, 98], [0, 26], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const voiceBarWidth = interpolate(frame, [74, 120], [0, 96], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const badgeP = spring({
    frame: frame - 102,
    fps,
    config: theme.spring.bouncy,
  });
  const badgeScale = interpolate(badgeP, [0, 1], [0.82, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <StageScene>
      <SceneExit durationInFrames={SCENES.s2.duration} exitFrames={12}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 110px",
            gap: 24,
          }}
        >
          {/* Headline */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 14,
            }}
          >
            <WordReveal
              text="Konuşurken duraksamazsın."
              delay={2}
              per={3}
              wordGapPx={18}
              style={{
                fontSize: 66,
                color: theme.colors.text,
              }}
            />
            <WordReveal
              text="Kendini sesle daha rahat ifade edersin."
              delay={26}
              per={3}
              highlightWord="sesle"
              highlightColor={theme.colors.primaryBright}
              underlineColor={theme.colors.primary}
              wordGapPx={13}
              style={{
                fontSize: 34,
                fontWeight: 600,
                color: theme.colors.textDim,
              }}
            />
          </div>

          {/* Centerpiece Mic + 48 Bar Wave */}
          <Entrance
            delay={4}
            distance={24}
            scaleFrom={0.9}
            springConfig={theme.spring.bouncy}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: 310,
            }}
          >
            <MicMorphWave morph={0} scale={0.92} />
          </Entrance>

          {/* Speed Comparison Card */}
          <Entrance
            delay={62}
            distance={28}
            scaleFrom={0.96}
            style={{ width: "100%", maxWidth: 1120 }}
          >
            <div
              style={{
                borderRadius: 22,
                background: theme.colors.card,
                border: `1px solid ${theme.colors.line}`,
                boxShadow: `0 22px 54px ${theme.colors.black65}`,
                padding: "24px 32px",
                display: "flex",
                flexDirection: "column",
                gap: 18,
              }}
            >
              {/* Keyboard Row */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "200px 1fr 220px",
                  alignItems: "center",
                  gap: 22,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    color: theme.colors.textDim,
                    fontSize: 20,
                    fontWeight: 500,
                  }}
                >
                  <KeyboardIcon size={22} color={theme.colors.textMuted} />
                  <span>Klavye</span>
                </div>
                <div
                  style={{
                    height: 16,
                    borderRadius: 999,
                    background: theme.colors.inner,
                    border: `1px solid ${theme.colors.lineSoft}`,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${keyboardBarWidth}%`,
                      height: "100%",
                      borderRadius: 999,
                      background: theme.colors.lineStrong,
                    }}
                  />
                </div>
                <div
                  style={{
                    textAlign: "right",
                    fontFamily: theme.fonts.mono,
                    fontSize: 20,
                    color: theme.colors.textMuted,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  ~40 kelime/dk
                </div>
              </div>

              {/* Voice Row */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "200px 1fr 220px",
                  alignItems: "center",
                  gap: 22,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    color: theme.colors.text,
                    fontSize: 21,
                    fontWeight: 600,
                  }}
                >
                  <MicIcon size={22} color={theme.colors.primaryBright} />
                  <span>Ses ile Dikte</span>
                </div>
                <div
                  style={{
                    height: 18,
                    borderRadius: 999,
                    background: theme.colors.inner,
                    border: `1px solid ${theme.colors.line}`,
                    overflow: "hidden",
                    position: "relative",
                  }}
                >
                  <div
                    style={{
                      width: `${voiceBarWidth}%`,
                      height: "100%",
                      borderRadius: 999,
                      background: `linear-gradient(90deg, ${theme.colors.primaryDark}, ${theme.colors.primaryBright})`,
                      boxShadow: `0 0 22px ${theme.colors.glow}`,
                    }}
                  />
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    gap: 12,
                  }}
                >
                  <AnimatedCounter
                    target={150}
                    delay={74}
                    suffix=" kelime/dk"
                    style={{
                      fontFamily: theme.fonts.mono,
                      fontSize: 22,
                      fontWeight: 600,
                      color: theme.colors.text,
                    }}
                  />
                </div>
              </div>

              {/* Highlight Multiplier Pill */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  marginTop: -4,
                }}
              >
                <div
                  style={{
                    opacity: badgeP,
                    transform: `scale(${badgeScale})`,
                    padding: "7px 16px",
                    borderRadius: 999,
                    background: theme.colors.glowSoft,
                    border: `1px solid ${theme.colors.primary}`,
                    color: theme.colors.accentText,
                    fontFamily: theme.fonts.display,
                    fontSize: 16,
                    fontWeight: 700,
                  }}
                >
                  3,5x daha hızlı ve kesintisiz akış
                </div>
              </div>
            </div>
          </Entrance>
        </div>
      </SceneExit>
    </StageScene>
  );
};
