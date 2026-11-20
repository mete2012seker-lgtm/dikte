import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { BoltIcon, CheckCircleIcon, MicIcon } from "../components/Icons";
import {
  AnimatedListItem,
  Keycap3D,
  ShineBorderCard,
} from "../components/MagicUI";
import { MicMorphWave } from "../components/MicMorphWave";
import { Entrance, SceneExit, WordReveal } from "../components/MotionPrimitives";
import { StageScene } from "../components/StageLayers";
import { SCENES, theme } from "../theme";

const DICTATION_WORDS =
  "Toplantı notlarını tek tek yazmak yerine sadece konuşuyorum; düşüncelerim hiç bölünmeden ekrana akıyor.".split(
    " "
  );

export const Scene3PushToTalk: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Key presses at frame 26, stays down until frame 120
  const pressIn = interpolate(frame, [24, 36], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const releaseOut = interpolate(frame, [120, 134], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const isPressed = pressIn * (1 - releaseOut);

  // Morph follows exact Dikte morph curve (0 -> 1 at press, 1 -> 0 at release)
  const morphIn = interpolate(frame, [24, 50], [0, 1], {
    easing: theme.ease.morph,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const morphOut = interpolate(frame, [120, 146], [0, 1], {
    easing: theme.ease.morph,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const morphVal = morphIn * (1 - morphOut);

  // ShineBorder active while Whisper processes (120..162)
  const shineIn = interpolate(frame, [120, 132], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shineOut = interpolate(frame, [156, 170], [0, 1], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shineVal = shineIn * (1 - shineOut);

  const isRecording = frame >= 26 && frame < 120;
  const isProcessing = frame >= 120 && frame < 156;
  const isDone = frame >= 156;

  const statusLabel = isRecording
    ? "Dinliyor..."
    : isProcessing
    ? "Yerel Whisper yazıya çeviriyor..."
    : isDone
    ? "Yapıştırıldı"
    : "Dinlemeye hazır";

  const statusColor = isRecording
    ? theme.colors.recording
    : isProcessing
    ? theme.colors.warning
    : theme.colors.ready;

  return (
    <StageScene>
      <SceneExit durationInFrames={SCENES.s3.duration} exitFrames={12}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: "0 110px",
            gap: 42,
          }}
        >
          {/* Scene Header */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 12,
            }}
          >
            <WordReveal
              text="Bas, konuş, bırak."
              delay={0}
              per={3}
              highlightWord="konuş,"
              highlightColor={theme.colors.primaryBright}
              wordGapPx={18}
              style={{
                fontSize: 64,
                color: theme.colors.text,
              }}
            />
            <Entrance delay={12} distance={18} scaleFrom={0.97}>
              <div
                style={{
                  fontSize: 25,
                  color: theme.colors.textDim,
                  fontWeight: 500,
                }}
              >
                Sağ Ctrl&apos;ye basılı tut — metin anında aktif pencereye aksın.
              </div>
            </Entrance>
          </div>

          {/* Two-Column Interaction Stage */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "600px 1fr",
              gap: 44,
              alignItems: "center",
              maxWidth: 1620,
              width: "100%",
              margin: "0 auto",
            }}
          >
            {/* Left Column: 3D Keycap + Morphing Mic Wave */}
            <Entrance
              delay={6}
              distance={26}
              scaleFrom={0.95}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 20,
              }}
            >
              <Keycap3D
                label="Sağ Ctrl"
                sublabel={isRecording ? "Basılı tutuluyor" : "Bas - Konuş"}
                pressed={isPressed}
              />

              <div
                style={{
                  width: 580,
                  height: 270,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  overflow: "visible",
                }}
              >
                <MicMorphWave morph={morphVal} scale={0.7} energy={1.08} />
              </div>
            </Entrance>

            {/* Right Column: Live Transcript Card + AnimatedList Pills */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 18,
              }}
            >
              <Entrance delay={10} distance={28} scaleFrom={0.96}>
                <ShineBorderCard shineActive={shineVal} padding="28px 32px">
                  {/* Card Header */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 18,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        fontFamily: theme.fonts.display,
                        fontSize: 20,
                        fontWeight: 600,
                        color: theme.colors.text,
                      }}
                    >
                      <MicIcon size={20} color={theme.colors.textDim} />
                      <span>Metin çıktısı</span>
                    </div>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 9,
                        padding: "7px 14px",
                        borderRadius: 999,
                        background: theme.colors.inner,
                        border: `1px solid ${theme.colors.lineStrong}`,
                        fontSize: 15,
                        fontWeight: 600,
                        color: statusColor,
                      }}
                    >
                      <span
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          background: statusColor,
                          boxShadow: `0 0 10px ${statusColor}`,
                        }}
                      />
                      <span>{statusLabel}</span>
                    </div>
                  </div>

                  {/* Transcript Box */}
                  <div
                    style={{
                      minHeight: 176,
                      borderRadius: 14,
                      background: theme.colors.inner,
                      border: `1px solid ${theme.colors.lineSoft}`,
                      padding: "24px 26px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        columnGap: 9,
                        rowGap: 6,
                        fontSize: 27,
                        fontWeight: 500,
                        lineHeight: 1.5,
                        color: theme.colors.text,
                      }}
                    >
                      {DICTATION_WORDS.map((word, idx) => {
                        const appearAt = 40 + idx * 5;
                        const wp = spring({
                          frame: frame - appearAt,
                          fps,
                          config: theme.spring.snappy,
                        });
                        const wy = interpolate(wp, [0, 1], [10, 0], {
                          easing: theme.ease.out,
                          extrapolateLeft: "clamp",
                          extrapolateRight: "clamp",
                        });
                        return (
                          <span
                            key={`${word}-${idx}`}
                            style={{
                              opacity: wp,
                              transform: `translateY(${wy}px)`,
                              display: "inline-block",
                            }}
                          >
                            {word}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </ShineBorderCard>
              </Entrance>

              {/* Staggered AnimatedList Status Pills */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 10,
                }}
              >
                <AnimatedListItem
                  delay={148}
                  icon={<MicIcon size={18} />}
                  text="Kayıt alındı • 3,2 sn"
                  accent="primary"
                />
                <AnimatedListItem
                  delay={158}
                  icon={<BoltIcon size={18} />}
                  text="Yerel Whisper • GPU (float16)"
                  accent="primary"
                />
                <AnimatedListItem
                  delay={168}
                  icon={<CheckCircleIcon size={18} />}
                  text="Aktif pencereye otomatik yapıştırıldı"
                  accent="ready"
                />
              </div>
            </div>
          </div>
        </div>
      </SceneExit>
    </StageScene>
  );
};
