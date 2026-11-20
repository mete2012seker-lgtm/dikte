import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import {
  CheckCircleIcon,
  GlobeIcon,
  SparklesIcon,
} from "../components/Icons";
import { ShineBorderCard } from "../components/MagicUI";
import { Entrance, SceneExit, WordReveal } from "../components/MotionPrimitives";
import { StageScene } from "../components/StageLayers";
import { SCENES, theme } from "../theme";

const RAW_WORDS =
  "şey yarın sabah saat onda tasarım toplantısını yapalım mı acaba".split(" ");
const CLEAN_WORDS =
  "Yarın sabah 10:00'da tasarım toplantısını yapalım mı?".split(" ");
const EN_WORDS =
  "Shall we have the design meeting tomorrow at 10:00 AM?".split(" ");

export const Scene4AICleanTranslate: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ShineBorder active during Clean (66..98) and Translate (128..162)
  const cleanShineIn = interpolate(frame, [66, 76], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cleanShineOut = interpolate(frame, [96, 108], [0, 1], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const transShineIn = interpolate(frame, [128, 138], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const transShineOut = interpolate(frame, [160, 174], [0, 1], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const shineVal = Math.max(
    cleanShineIn * (1 - cleanShineOut),
    transShineIn * (1 - transShineOut)
  );

  // Switch from messy text to clean text at frame 84
  const rawOpacity = interpolate(frame, [78, 86], [1, 0], {
    easing: theme.ease.in,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cleanActive = frame >= 84;
  const cleanBtnHighlight =
    frame >= 66 && frame < 98
      ? interpolate(frame, [66, 72, 92, 98], [0, 1, 1, 0], {
          easing: theme.ease.inOut,
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 0;

  const translateBtnHighlight =
    frame >= 126 && frame < 164
      ? interpolate(frame, [126, 132, 158, 164], [0, 1, 1, 0], {
          easing: theme.ease.inOut,
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 0;

  const langSwitched = frame >= 126;
  const translationCardP = spring({
    frame: frame - 142,
    fps,
    config: theme.spring.smooth,
  });
  const translationY = interpolate(translationCardP, [0, 1], [18, 0], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const cleanCheckP = spring({
    frame: frame - 92,
    fps,
    config: theme.spring.snappy,
  });

  return (
    <StageScene>
      <SceneExit durationInFrames={SCENES.s4.duration} exitFrames={12}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 110px",
            gap: 36,
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
              text="Dağınık konuş. Temiz metin al."
              delay={0}
              per={3}
              highlightWord="Temiz"
              highlightColor={theme.colors.primaryBright}
              underlineColor={theme.colors.primary}
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
                Tek çağrıda imla temizliği ve Türkçe, İngilizce veya Almanca çıktı.
              </div>
            </Entrance>
          </div>

          {/* Dikte Text Output Card Replica */}
          <Entrance
            delay={8}
            distance={30}
            scaleFrom={0.96}
            style={{ width: "100%", maxWidth: 1180 }}
          >
            <ShineBorderCard shineActive={shineVal} padding="30px 34px">
              {/* Top Panel Header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 20,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <span
                    style={{
                      fontFamily: theme.fonts.display,
                      fontSize: 21,
                      fontWeight: 600,
                      color: theme.colors.text,
                    }}
                  >
                    Metin çıktısı
                  </span>
                  {cleanActive && (
                    <span
                      style={{
                        opacity: cleanCheckP,
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 7,
                        padding: "5px 12px",
                        borderRadius: 999,
                        background: theme.colors.readyBg,
                        border: `1px solid ${theme.colors.readyBorder}`,
                        color: theme.colors.ready,
                        fontSize: 14,
                        fontWeight: 600,
                      }}
                    >
                      <CheckCircleIcon size={15} />
                      <span>İmla düzeltildi</span>
                    </span>
                  )}
                </div>

                {/* Language Selector + Auto-translate */}
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      padding: "9px 16px",
                      borderRadius: 12,
                      background: theme.colors.inner,
                      border: `1px solid ${
                        langSwitched
                          ? theme.colors.primary
                          : theme.colors.lineStrong
                      }`,
                      color: theme.colors.text,
                      fontSize: 16,
                      fontWeight: 500,
                    }}
                  >
                    <GlobeIcon size={18} color={theme.colors.primaryBright} />
                    <span>
                      Çıktı Dili: {langSwitched ? "İngilizce" : "Türkçe"}
                    </span>
                  </div>

                  <div
                    style={{
                      padding: "9px 14px",
                      borderRadius: 12,
                      background: theme.colors.inner,
                      border: `1px solid ${theme.colors.lineSoft}`,
                      fontFamily: theme.fonts.mono,
                      fontSize: 14,
                      fontWeight: 600,
                      color: theme.colors.accentText,
                    }}
                  >
                    TR / EN / DE
                  </div>
                </div>
              </div>

              {/* Transcript Content Box */}
              <div
                style={{
                  minHeight: 205,
                  borderRadius: 16,
                  background: theme.colors.inner,
                  border: `1px solid ${theme.colors.lineSoft}`,
                  padding: "26px 30px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                  gap: 20,
                  position: "relative",
                }}
              >
                {/* Raw Dictation vs Cleaned Text */}
                {!cleanActive ? (
                  <div
                    style={{
                      opacity: rawOpacity,
                      display: "flex",
                      flexWrap: "wrap",
                      columnGap: 10,
                      rowGap: 6,
                      fontSize: 30,
                      fontWeight: 400,
                      color: theme.colors.textDim,
                    }}
                  >
                    {RAW_WORDS.map((word, idx) => {
                      const p = spring({
                        frame: frame - (10 + idx * 4),
                        fps,
                        config: theme.spring.snappy,
                      });
                      const isFiller = word === "şey" || word === "acaba";
                      return (
                        <span
                          key={`${word}-${idx}`}
                          style={{
                            opacity: p,
                            color: isFiller
                              ? theme.colors.warning
                              : theme.colors.textDim,
                          }}
                        >
                          {word}
                        </span>
                      );
                    })}
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      columnGap: 10,
                      rowGap: 6,
                      fontSize: 31,
                      fontWeight: 600,
                      color: theme.colors.text,
                    }}
                  >
                    {CLEAN_WORDS.map((word, idx) => {
                      const p = spring({
                        frame: frame - (84 + idx * 3),
                        fps,
                        config: theme.spring.snappy,
                      });
                      const y = interpolate(p, [0, 1], [12, 0], {
                        easing: theme.ease.out,
                        extrapolateLeft: "clamp",
                        extrapolateRight: "clamp",
                      });
                      return (
                        <span
                          key={`${word}-${idx}`}
                          style={{
                            opacity: p,
                            transform: `translateY(${y}px)`,
                            display: "inline-block",
                          }}
                        >
                          {word}
                        </span>
                      );
                    })}
                  </div>
                )}

                {/* Translated Output Box */}
                {frame >= 142 && (
                  <div
                    style={{
                      opacity: translationCardP,
                      transform: `translateY(${translationY}px)`,
                      padding: "18px 22px",
                      borderRadius: 14,
                      background: theme.colors.card,
                      border: `1px solid ${theme.colors.primary}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 16,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        columnGap: 9,
                        rowGap: 4,
                        fontSize: 26,
                        fontWeight: 600,
                        color: theme.colors.accentText,
                      }}
                    >
                      {EN_WORDS.map((word, idx) => {
                        const wp = spring({
                          frame: frame - (144 + idx * 2),
                          fps,
                          config: theme.spring.snappy,
                        });
                        return (
                          <span key={`${word}-${idx}`} style={{ opacity: wp }}>
                            {word}
                          </span>
                        );
                      })}
                    </div>
                    <span
                      style={{
                        fontFamily: theme.fonts.mono,
                        fontSize: 13,
                        fontWeight: 600,
                        padding: "5px 10px",
                        borderRadius: 8,
                        background: theme.colors.glowSoft,
                        color: theme.colors.primaryBright,
                        flexShrink: 0,
                      }}
                    >
                      EN
                    </span>
                  </div>
                )}
              </div>

              {/* Action Buttons Row */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  marginTop: 22,
                }}
              >
                <div
                  style={{
                    padding: "12px 20px",
                    borderRadius: 12,
                    background: theme.colors.inner,
                    border: `1px solid ${theme.colors.lineStrong}`,
                    color: theme.colors.textDim,
                    fontSize: 16,
                    fontWeight: 500,
                  }}
                >
                  Kopyala
                </div>
                <div
                  style={{
                    padding: "12px 20px",
                    borderRadius: 12,
                    background: theme.colors.inner,
                    border: `1px solid ${theme.colors.lineStrong}`,
                    color: theme.colors.textDim,
                    fontSize: 16,
                    fontWeight: 500,
                  }}
                >
                  Transkripsiyonu Yenile
                </div>

                {/* Clean AI Button */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 9,
                    padding: "12px 22px",
                    borderRadius: 12,
                    background:
                      cleanBtnHighlight > 0.25
                        ? theme.colors.primary
                        : theme.colors.glowSoft,
                    border: `1px solid ${theme.colors.primary}`,
                    boxShadow:
                      cleanBtnHighlight > 0.25
                        ? `0 0 28px ${theme.colors.glow}`
                        : "none",
                    transform: `scale(${1 - cleanBtnHighlight * 0.03})`,
                    color: theme.colors.text,
                    fontSize: 16,
                    fontWeight: 600,
                  }}
                >
                  <SparklesIcon size={18} />
                  <span>Yapay Zeka ile Temizle</span>
                </div>

                {/* Translate Button */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 9,
                    padding: "12px 22px",
                    borderRadius: 12,
                    background:
                      translateBtnHighlight > 0.25
                        ? theme.colors.primary
                        : theme.colors.inner,
                    border: `1px solid ${
                      translateBtnHighlight > 0.25
                        ? theme.colors.primaryBright
                        : theme.colors.lineStrong
                    }`,
                    boxShadow:
                      translateBtnHighlight > 0.25
                        ? `0 0 28px ${theme.colors.glow}`
                        : "none",
                    transform: `scale(${1 - translateBtnHighlight * 0.03})`,
                    color: theme.colors.text,
                    fontSize: 16,
                    fontWeight: 600,
                  }}
                >
                  <GlobeIcon size={18} />
                  <span>Çevir</span>
                </div>
              </div>
            </ShineBorderCard>
          </Entrance>
        </div>
      </SceneExit>
    </StageScene>
  );
};
