import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile } from "remotion";
import { HOOK_KEY_EVENTS, Scene1Hook } from "./scenes/Scene1Hook";
import { Scene2VoiceFlow } from "./scenes/Scene2VoiceFlow";
import { Scene3PushToTalk } from "./scenes/Scene3PushToTalk";
import { Scene4AICleanTranslate } from "./scenes/Scene4AICleanTranslate";
import { Scene5ThemeToggler } from "./scenes/Scene5ThemeToggler";
import { Scene6BentoFeatures } from "./scenes/Scene6BentoFeatures";
import { Scene7CTA } from "./scenes/Scene7CTA";
import { SCENES, TOTAL_FRAMES, theme } from "./theme";

export const DiktePromo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* Continuous soft ambient harmonic bed */}
      <Audio
        src={staticFile("sfx/ambient_bed.wav")}
        volume={(f) => {
          const fadeIn = interpolate(f, [0, 30], [0, 1], {
            easing: theme.ease.out,
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const fadeOut = interpolate(
            f,
            [TOTAL_FRAMES - 40, TOTAL_FRAMES],
            [1, 0],
            {
              easing: theme.ease.in,
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }
          );
          return 0.14 * fadeIn * fadeOut;
        }}
      />

      {/* Scene 1 typing & backspace SFX (2-3 frames anticipation for tactile sync) */}
      {HOOK_KEY_EVENTS.taps.map((tapFrame, idx) => (
        <Sequence key={`tap-${idx}`} from={Math.max(0, tapFrame - 1)} durationInFrames={6}>
          <Audio src={staticFile("sfx/key_tap.wav")} volume={0.28} />
        </Sequence>
      ))}
      {HOOK_KEY_EVENTS.backspaces.map((backFrame, idx) => (
        <Sequence key={`back-${idx}`} from={Math.max(0, backFrame - 1)} durationInFrames={6}>
          <Audio src={staticFile("sfx/key_backspace.wav")} volume={0.36} />
        </Sequence>
      ))}

      {/* Transition Whooshes (2-4 frames before cut) */}
      {[176, 356, 596, 806, 1016, 1196].map((f) => (
        <Sequence key={`whoosh-${f}`} from={f} durationInFrames={16}>
          <Audio src={staticFile("sfx/whoosh.wav")} volume={0.42} />
        </Sequence>
      ))}

      {/* Bass Hits on major visual landings */}
      <Sequence from={SCENES.s2.from} durationInFrames={18}>
        <Audio src={staticFile("sfx/bass_hit.wav")} volume={0.46} />
      </Sequence>
      <Sequence from={SCENES.s7.from + 2} durationInFrames={18}>
        <Audio src={staticFile("sfx/bass_hit.wav")} volume={0.48} />
      </Sequence>

      {/* Scene 3 Push-to-Talk Mic On / Off & Auto-Paste Pop */}
      <Sequence from={SCENES.s3.from + 22} durationInFrames={12}>
        <Audio src={staticFile("sfx/mic_on.wav")} volume={0.44} />
      </Sequence>
      <Sequence from={SCENES.s3.from + 118} durationInFrames={12}>
        <Audio src={staticFile("sfx/mic_off.wav")} volume={0.4} />
      </Sequence>
      <Sequence from={SCENES.s3.from + 166} durationInFrames={8}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.4} />
      </Sequence>

      {/* Scene 4 AI Clean Shimmer & Language Switch Pop */}
      <Sequence from={SCENES.s4.from + 66} durationInFrames={22}>
        <Audio src={staticFile("sfx/shimmer.wav")} volume={0.42} />
      </Sequence>
      <Sequence from={SCENES.s4.from + 124} durationInFrames={8}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.38} />
      </Sequence>

      {/* Scene 5 Theme Toggler Click & Circular Reveal Shimmer */}
      <Sequence from={SCENES.s5.from + 86} durationInFrames={8}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.42} />
      </Sequence>
      <Sequence from={SCENES.s5.from + 88} durationInFrames={22}>
        <Audio src={staticFile("sfx/shimmer.wav")} volume={0.44} />
      </Sequence>

      {/* Scene 6 Bento Card Entrance Pops */}
      {[14, 19, 24, 29].map((offset) => (
        <Sequence
          key={`bento-pop-${offset}`}
          from={SCENES.s6.from + offset - 2}
          durationInFrames={8}
        >
          <Audio src={staticFile("sfx/pop.wav")} volume={0.28} />
        </Sequence>
      ))}

      {/* Visual Scenes */}
      <Sequence from={SCENES.s1.from} durationInFrames={SCENES.s1.duration}>
        <Scene1Hook />
      </Sequence>

      <Sequence from={SCENES.s2.from} durationInFrames={SCENES.s2.duration}>
        <Scene2VoiceFlow />
      </Sequence>

      <Sequence from={SCENES.s3.from} durationInFrames={SCENES.s3.duration}>
        <Scene3PushToTalk />
      </Sequence>

      <Sequence from={SCENES.s4.from} durationInFrames={SCENES.s4.duration}>
        <Scene4AICleanTranslate />
      </Sequence>

      <Sequence from={SCENES.s5.from} durationInFrames={SCENES.s5.duration}>
        <Scene5ThemeToggler />
      </Sequence>

      <Sequence from={SCENES.s6.from} durationInFrames={SCENES.s6.duration}>
        <Scene6BentoFeatures />
      </Sequence>

      <Sequence from={SCENES.s7.from} durationInFrames={SCENES.s7.duration}>
        <Scene7CTA />
      </Sequence>
    </AbsoluteFill>
  );
};
