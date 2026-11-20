import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import {
  BoltIcon,
  CodeOpenIcon,
  LayersIcon,
  ShieldLockIcon,
} from "../components/Icons";
import { MagicCard } from "../components/MagicUI";
import { Entrance, SceneExit, WordReveal } from "../components/MotionPrimitives";
import { StageScene } from "../components/StageLayers";
import { SCENES, theme } from "../theme";

const FEATURES = [
  {
    title: "Tamamen Yerel & Gizli",
    desc: "Ses kaydın bilgisayarından dışarı çıkmaz. faster-whisper GPU ve CPU desteğiyle anında çeviri.",
    tag: "Yerel Gizlilik",
    icon: <ShieldLockIcon size={28} />,
  },
  {
    title: "Sistem Tepsisinde Hazır",
    desc: "Pencere kapalıyken bile her uygulamada 1–3 tuşlu serbest kısayolla anında otomatik yapıştırır.",
    tag: "Global Kısayol",
    icon: <BoltIcon size={28} />,
  },
  {
    title: "Esnek Model Desteği",
    desc: "6 Whisper ses modeli, 4 yerel GGUF metin modeli, Hugging Face ve OpenRouter entegrasyonu.",
    tag: "Ses + Metin",
    icon: <LayersIcon size={28} />,
  },
  {
    title: "Ücretsiz & Açık Kaynak",
    desc: "Windows için tek tık kurucu, abonelik veya kelime sınırı yok; akıllı otomatik güncelleme dahil.",
    tag: "MIT Lisansı",
    icon: <CodeOpenIcon size={28} />,
  },
];

export const Scene6BentoFeatures: React.FC = () => {
  const frame = useCurrentFrame();

  // Sequential single-card spotlight sweeping across card 0 -> 1 -> 2 -> 3
  const focusIndex = interpolate(frame, [26, 152], [0, 3.25], {
    easing: theme.ease.inOut,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const spotX = 28 + Math.sin(frame / 18) * 18;
  const spotY = 24 + Math.cos(frame / 22) * 12;

  return (
    <StageScene>
      <SceneExit durationInFrames={SCENES.s6.duration} exitFrames={12}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 110px",
            gap: 44,
          }}
        >
          {/* Headline */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 12,
            }}
          >
            <WordReveal
              text="Sen konuş, gerisini Dikte halletsin."
              delay={0}
              per={3}
              highlightWord="Dikte"
              highlightColor={theme.colors.primaryBright}
              underlineColor={theme.colors.primary}
              wordGapPx={18}
              style={{
                fontSize: 62,
                color: theme.colors.text,
              }}
            />
            <Entrance delay={12} distance={16} scaleFrom={0.97}>
              <div
                style={{
                  fontSize: 24,
                  color: theme.colors.textDim,
                  fontWeight: 500,
                }}
              >
                Günlük yazı yükünü ortadan kaldıran Windows masaüstü aracı.
              </div>
            </Entrance>
          </div>

          {/* 2x2 BentoGrid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 26,
              width: "100%",
              maxWidth: 1460,
            }}
          >
            {FEATURES.map((item, idx) => {
              const dist = Math.abs(focusIndex - idx);
              const glowIntensity = Math.max(0, 1 - dist * 1.15);
              return (
                <Entrance
                  key={item.title}
                  delay={14 + idx * 5}
                  distance={32}
                  scaleFrom={0.94}
                >
                  <MagicCard
                    glowIntensity={glowIntensity}
                    spotX={spotX}
                    spotY={spotY}
                    style={{ height: "100%" }}
                  >
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 18,
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <div
                          style={{
                            width: 56,
                            height: 56,
                            borderRadius: 16,
                            background:
                              glowIntensity > 0.35
                                ? theme.colors.primary
                                : theme.colors.glowSoft,
                            border: `1px solid ${
                              glowIntensity > 0.35
                                ? theme.colors.primaryBright
                                : theme.colors.lineStrong
                            }`,
                            color:
                              glowIntensity > 0.35
                                ? theme.colors.text
                                : theme.colors.primaryBright,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                        >
                          {item.icon}
                        </div>

                        <span
                          style={{
                            fontFamily: theme.fonts.mono,
                            fontSize: 14,
                            fontWeight: 600,
                            padding: "6px 13px",
                            borderRadius: 999,
                            background: theme.colors.inner,
                            border: `1px solid ${theme.colors.lineStrong}`,
                            color:
                              glowIntensity > 0.35
                                ? theme.colors.accentText
                                : theme.colors.textMuted,
                          }}
                        >
                          {item.tag}
                        </span>
                      </div>

                      <div
                        style={{
                          fontFamily: theme.fonts.display,
                          fontSize: 30,
                          fontWeight: 700,
                          letterSpacing: "-0.02em",
                          color: theme.colors.text,
                        }}
                      >
                        {item.title}
                      </div>

                      <div
                        style={{
                          fontSize: 20,
                          lineHeight: 1.5,
                          color: theme.colors.textDim,
                        }}
                      >
                        {item.desc}
                      </div>
                    </div>
                  </MagicCard>
                </Entrance>
              );
            })}
          </div>
        </div>
      </SceneExit>
    </StageScene>
  );
};
