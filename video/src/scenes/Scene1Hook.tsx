import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { KeyboardIcon } from "../components/Icons";
import { Entrance, SceneExit, WordReveal } from "../components/MotionPrimitives";
import { StageScene } from "../components/StageLayers";
import { SCENES, theme } from "../theme";

interface Step {
  text: string;
  isBackspace: boolean;
}

function buildTypingTimeline() {
  const steps: Step[] = [];
  let cur = "";

  const pushText = (s: string) => {
    for (const ch of s) {
      cur += ch;
      steps.push({ text: cur, isBackspace: false });
    }
  };
  const pushPause = (count: number) => {
    for (let i = 0; i < count; i++) {
      steps.push({ text: cur, isBackspace: false });
    }
  };
  const pushBack = (count: number) => {
    for (let i = 0; i < count; i++) {
      cur = cur.slice(0, -1);
      steps.push({ text: cur, isBackspace: true });
    }
  };

  pushText("Toplantıda bütüm");
  pushPause(3);
  pushBack(5); // delete "bütüm"
  pushPause(2);
  pushText("bütün notları yz");
  pushPause(3);
  pushBack(2); // delete "yz"
  pushPause(2);
  pushText("yazmak...");

  return steps;
}

const TYPING_STEPS = buildTypingTimeline();
const START_TYPING_FRAME = 16;
const FRAMES_PER_STEP = 2;

export const HOOK_KEY_EVENTS = (() => {
  const taps: number[] = [];
  const backspaces: number[] = [];
  for (let i = 0; i < TYPING_STEPS.length; i++) {
    const prevText = i > 0 ? TYPING_STEPS[i - 1].text : "";
    const curStep = TYPING_STEPS[i];
    if (curStep.text !== prevText) {
      const f = START_TYPING_FRAME + i * FRAMES_PER_STEP;
      if (curStep.isBackspace) {
        backspaces.push(f);
      } else {
        taps.push(f);
      }
    }
  }
  return { taps, backspaces };
})();

export const Scene1Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rawStep = Math.floor((frame - START_TYPING_FRAME) / FRAMES_PER_STEP);
  const typedText =
    frame < START_TYPING_FRAME
      ? ""
      : TYPING_STEPS[Math.min(TYPING_STEPS.length - 1, rawStep)].text;

  const isCorrecting =
    frame >= START_TYPING_FRAME &&
    rawStep >= 0 &&
    rawStep < TYPING_STEPS.length &&
    TYPING_STEPS[rawStep].isBackspace;

  const cursorBlink = Math.sin((frame / fps) * Math.PI * 3.2) > -0.2 ? 1 : 0.15;

  const secondLineP = spring({
    frame: frame - 74,
    fps,
    config: theme.spring.smooth,
  });

  const errorGlowOpacity = interpolate(
    frame,
    [58, 70, 86, 108, 120, 134],
    [0, 1, 0.25, 1, 0.25, 0],
    {
      easing: theme.ease.inOut,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <StageScene>
      <SceneExit durationInFrames={SCENES.s1.duration} exitFrames={12}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 120px",
            gap: 44,
          }}
        >
          {/* Headline area */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 14,
            }}
          >
            <WordReveal
              text="Aklındakiler hızlı..."
              delay={0}
              per={3}
              wordGapPx={20}
              style={{
                fontSize: 66,
                color: theme.colors.textDim,
              }}
            />
            <div style={{ opacity: secondLineP }}>
              <WordReveal
                text="Ama yazmak zor."
                delay={74}
                per={4}
                highlightWord="yazmak"
                highlightColor={theme.colors.recording}
                underlineColor={theme.colors.recording}
                wordGapPx={22}
                style={{
                  fontSize: 78,
                  color: theme.colors.text,
                }}
              />
            </div>
          </div>

          {/* Struggling Keyboard Editor Card */}
          <Entrance
            delay={4}
            distance={36}
            scaleFrom={0.94}
            style={{ width: "100%", maxWidth: 1080 }}
          >
            <div
              style={{
                borderRadius: 24,
                background: theme.colors.card,
                border: `1px solid ${
                  isCorrecting ? theme.colors.errorBorder : theme.colors.line
                }`,
                boxShadow: `0 28px 70px ${theme.colors.black65}`,
                padding: "26px 32px 32px",
              }}
            >
              {/* Window Top Bar */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 20,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span
                    style={{
                      width: 11,
                      height: 11,
                      borderRadius: "50%",
                      background: theme.colors.lineStrong,
                    }}
                  />
                  <span
                    style={{
                      width: 11,
                      height: 11,
                      borderRadius: "50%",
                      background: theme.colors.lineStrong,
                    }}
                  />
                  <span
                    style={{
                      width: 11,
                      height: 11,
                      borderRadius: "50%",
                      background: theme.colors.lineStrong,
                    }}
                  />
                  <span
                    style={{
                      marginLeft: 10,
                      fontFamily: theme.fonts.mono,
                      fontSize: 15,
                      color: theme.colors.textMuted,
                    }}
                  >
                    notlar.txt
                  </span>
                </div>

                {/* Pace indicator badge */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "7px 14px",
                    borderRadius: 999,
                    background: isCorrecting
                      ? theme.colors.errorSoft
                      : theme.colors.white04,
                    border: `1px solid ${
                      isCorrecting
                        ? theme.colors.errorBorder
                        : theme.colors.lineStrong
                    }`,
                    color: isCorrecting
                      ? theme.colors.recording
                      : theme.colors.textDim,
                    fontSize: 15,
                    fontWeight: 500,
                  }}
                >
                  <KeyboardIcon size={18} />
                  <span>
                    {isCorrecting
                      ? "Silip düzeltiliyor..."
                      : "Klavye ile yazılıyor..."}
                  </span>
                </div>
              </div>

              {/* Editor Text Canvas */}
              <div
                style={{
                  minHeight: 168,
                  borderRadius: 16,
                  background: theme.colors.inner,
                  border: `1px solid ${
                    errorGlowOpacity > 0.3
                      ? theme.colors.errorBorder
                      : theme.colors.lineSoft
                  }`,
                  padding: "28px 30px",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <div
                  style={{
                    fontFamily: theme.fonts.body,
                    fontSize: 32,
                    fontWeight: 500,
                    lineHeight: 1.45,
                    color: theme.colors.text,
                    letterSpacing: "-0.01em",
                  }}
                >
                  <span>{typedText}</span>
                  <span
                    style={{
                      display: "inline-block",
                      width: 3,
                      height: 34,
                      marginLeft: 4,
                      verticalAlign: "middle",
                      borderRadius: 2,
                      background: isCorrecting
                        ? theme.colors.recording
                        : theme.colors.primaryBright,
                      opacity: cursorBlink,
                    }}
                  />
                </div>
              </div>
            </div>
          </Entrance>
        </div>
      </SceneExit>
    </StageScene>
  );
};
