import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.resolve(__dirname, "..", "shared-audio");
const SAMPLE_RATE = 44100;

fs.mkdirSync(OUT_DIR, { recursive: true });

function createRng(seed) {
  let a = seed >>> 0;
  return function next() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function writeWav(filename, samples) {
  const numSamples = samples.length;
  const dataBytes = numSamples * 2;
  const buf = Buffer.alloc(44 + dataBytes);

  buf.write("RIFF", 0);
  buf.writeUInt32LE(36 + dataBytes, 4);
  buf.write("WAVE", 8);
  buf.write("fmt ", 12);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20);
  buf.writeUInt16LE(1, 22);
  buf.writeUInt32LE(SAMPLE_RATE, 24);
  buf.writeUInt32LE(SAMPLE_RATE * 2, 28);
  buf.writeUInt16LE(2, 32);
  buf.writeUInt16LE(16, 34);
  buf.write("data", 36);
  buf.writeUInt32LE(dataBytes, 40);

  for (let i = 0; i < numSamples; i++) {
    const clamped = Math.max(-0.96, Math.min(0.96, samples[i]));
    const pcm = clamped < 0 ? Math.round(clamped * 32768) : Math.round(clamped * 32767);
    buf.writeInt16LE(pcm, 44 + i * 2);
  }

  const outPath = path.join(OUT_DIR, filename);
  fs.writeFileSync(outPath, buf);
  return { filename, bytes: buf.length, duration: (numSamples / SAMPLE_RATE).toFixed(2) };
}

function synthKeyClick() {
  const dur = 0.08;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const rng = createRng(101);
  let lp = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const envClick = Math.exp(-t * 260);
    const envBody = Math.exp(-t * 110);
    const noise = rng() * 2 - 1;
    lp = lp * 0.65 + noise * 0.35;
    const body = Math.sin(2 * Math.PI * (360 - t * 2200) * t) * 0.55;
    const top = Math.sin(2 * Math.PI * 1800 * t) * 0.25 * envClick;
    const attack = Math.min(1, i / 14);
    out[i] = attack * (lp * 0.38 * envClick + body * envBody + top) * 0.8;
  }
  return out;
}

function synthBassHit() {
  const dur = 0.45;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  let phase = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 46 + 74 * Math.exp(-t * 16);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const env = Math.min(1, i / 36) * Math.exp(-t * 7.2);
    const fund = Math.sin(phase);
    const warm = Math.sin(phase * 2) * 0.2 * Math.exp(-t * 14);
    out[i] = Math.tanh((fund + warm) * 1.15) * env * 0.82;
  }
  return out;
}

function synthDrop() {
  const dur = 0.14;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  let phase = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 220 + 340 * Math.exp(-t * 38);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const env = Math.min(1, i / 20) * Math.exp(-t * 28);
    out[i] = (Math.sin(phase) + 0.18 * Math.sin(phase * 2)) * env * 0.72;
  }
  return out;
}

function synthSwitch() {
  const dur = 0.16;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const rng = createRng(404);
  let lp = 0;
  let phase = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 480 + 420 * Math.min(1, t / 0.06);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const env = Math.min(1, i / 24) * Math.exp(-t * 26);
    const noise = rng() * 2 - 1;
    lp = lp * 0.78 + noise * 0.22;
    const airEnv = Math.sin(Math.PI * Math.min(1, t / 0.14)) * 0.22;
    out[i] = (Math.sin(phase) * 0.55 * env + lp * airEnv) * 0.76;
  }
  return out;
}

function synthChime() {
  const dur = 0.28;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const half = Math.floor(len * 0.36);
  let pA = 0;
  let pB = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    pA += (2 * Math.PI * 587.33) / SAMPLE_RATE; // D5
    pB += (2 * Math.PI * 880.0) / SAMPLE_RATE;  // A5
    const envA = Math.min(1, i / 80) * Math.exp(-t * 14);
    const noteA = (Math.sin(pA) + 0.22 * Math.sin(pA * 2)) * envA;
    let noteB = 0;
    if (i >= half) {
      const tb = (i - half) / SAMPLE_RATE;
      const envB = Math.min(1, (i - half) / 80) * Math.exp(-tb * 12);
      noteB = (Math.sin(pB) + 0.2 * Math.sin(pB * 2)) * envB;
    }
    out[i] = (noteA * 0.48 + noteB * 0.62) * 0.68;
  }
  return out;
}

function synthPastePop() {
  const dur = 0.12;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  let phase = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 320 + 560 * Math.exp(-t * 44);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const env = Math.min(1, i / 18) * Math.exp(-t * 32);
    const sparkle = Math.sin(2 * Math.PI * 1320 * t) * Math.exp(-t * 48) * 0.25;
    out[i] = (Math.sin(phase) * 0.65 * env + sparkle) * 0.72;
  }
  return out;
}

function synthWhoosh() {
  const dur = 0.36;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const rng = createRng(303);
  let bp1 = 0;
  let bp2 = 0;
  for (let i = 0; i < len; i++) {
    const p = i / len;
    const env = Math.sin(Math.PI * p) ** 1.3;
    const noise = rng() * 2 - 1;
    const cutoff = 0.04 + 0.2 * Math.sin(Math.PI * p);
    bp1 += cutoff * (noise - bp1);
    bp2 += cutoff * (bp1 - bp2);
    const air = bp1 - bp2 * 0.62;
    const subSine = Math.sin(2 * Math.PI * (150 + 210 * p) * (i / SAMPLE_RATE)) * 0.1;
    out[i] = (air * 0.95 + subSine) * env * 0.72;
  }
  return out;
}

function synthBellOutro() {
  const dur = 1.4;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const freqs = [523.25, 659.25, 783.99, 1046.5]; // C5 E5 G5 C6
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const env = Math.min(1, i / 90) * Math.exp(-t * 2.8);
    let sum = 0;
    for (let k = 0; k < freqs.length; k++) {
      const harmonic = Math.sin(2 * Math.PI * freqs[k] * t) + 0.18 * Math.sin(2 * Math.PI * freqs[k] * 2 * t) * Math.exp(-t * 5);
      sum += harmonic * (0.34 - k * 0.05);
    }
    out[i] = sum * env * 0.75;
  }
  return out;
}

function synthModernElectronicBgm({ durationSec, bpm, seamlessLoop, fadeOutStart }) {
  const len = Math.floor(SAMPLE_RATE * durationSec);
  const out = new Float32Array(len);
  const beatSec = 60 / bpm;
  const rng = createRng(seamlessLoop ? 909 : 707);

  // 4-chord progression (4 beats per chord = 16 beats per cycle)
  // Am9 -> Fmaj7 -> Cmaj9 -> G6
  const chords = [
    { bass: 55.0, pad: [220.0, 261.63, 329.63, 392.0], arp: [440.0, 523.25, 659.25, 783.99] },
    { bass: 43.65, pad: [174.61, 220.0, 261.63, 329.63], arp: [349.23, 440.0, 523.25, 659.25] },
    { bass: 65.41, pad: [196.0, 246.94, 293.66, 329.63], arp: [392.0, 493.88, 587.33, 659.25] },
    { bass: 49.0, pad: [196.0, 246.94, 293.66, 392.0], arp: [392.0, 493.88, 587.33, 783.99] },
  ];

  let hpPrev = 0;
  let noisePrev = 0;

  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const beatFloat = t / beatSec;
    const beatIndex = Math.floor(beatFloat);
    const beatFrac = beatFloat - beatIndex;
    const beatTime = beatFrac * beatSec;

    const stepFloat = beatFloat * 2; // 8th notes
    const stepIndex = Math.floor(stepFloat);
    const stepTime = (stepFloat - stepIndex) * (beatSec / 2);

    const sixteenthFloat = beatFloat * 4;
    const sixteenthIndex = Math.floor(sixteenthFloat);
    const sixteenthTime = (sixteenthFloat - sixteenthIndex) * (beatSec / 4);

    const chordIdx = Math.floor(beatIndex / 4) % chords.length;
    const chord = chords[chordIdx];

    // 1. Tight modern four-on-the-floor muted kick
    const kickFreq = 46 + 92 * Math.exp(-beatTime * 36);
    const kickEnv = Math.min(1, beatTime / 0.003) * Math.exp(-beatTime * 12);
    const kick = Math.sin(2 * Math.PI * kickFreq * beatTime) * kickEnv * 0.34;

    // 2. Soft crisp off-beat hi-hat (on 8th off-beats)
    const rawNoise = rng() * 2 - 1;
    const hp = rawNoise - noisePrev + 0.85 * hpPrev;
    noisePrev = rawNoise;
    hpPrev = hp;
    const hatAccent = stepIndex % 2 === 1 ? 1.0 : 0.35;
    const hatEnv = Math.exp(-stepTime * 55) * hatAccent;
    const hat = Math.max(-1, Math.min(1, hp * 0.5)) * hatEnv * 0.085;

    // 3. Soft clap / snap on beats 2 & 4
    let snap = 0;
    if (beatIndex % 2 === 1) {
      const snapEnv = Math.exp(-beatTime * 30);
      snap = Math.max(-1, Math.min(1, hp * 0.45)) * snapEnv * 0.095;
    }

    // 4. Sidechained warm sub-bass
    const sidechain = 0.25 + 0.75 * Math.min(1, beatFrac * 2.8);
    const bass =
      (Math.sin(2 * Math.PI * chord.bass * t) * 0.75 +
        Math.sin(2 * Math.PI * chord.bass * 2 * t) * 0.25) *
      sidechain *
      0.24;

    // 5. Lush Linear/Raycast-style pad
    let pad = 0;
    for (let p = 0; p < chord.pad.length; p++) {
      pad += Math.sin(2 * Math.PI * chord.pad[p] * t) * 0.048;
    }
    pad *= sidechain;

    // 6. Subtle plucked 16th arpeggio
    const arpPattern = [0, 1, 2, 3, 2, 1, 3, 2];
    const arpNote = chord.arp[arpPattern[sixteenthIndex % arpPattern.length]];
    const arpEnv = Math.min(1, sixteenthTime / 0.004) * Math.exp(-sixteenthTime * 16);
    const arpGate = sixteenthIndex % 4 === 2 ? 0.45 : 0.85;
    const arp =
      (Math.sin(2 * Math.PI * arpNote * t) + 0.2 * Math.sin(2 * Math.PI * arpNote * 2 * t)) *
      arpEnv *
      arpGate *
      0.095;

    let envGlobal = 1.0;
    if (seamlessLoop) {
      // Micro 12ms boundary smoothing so loop has zero click
      const edgeFade = 0.012;
      if (t < edgeFade) envGlobal = t / edgeFade;
      else if (durationSec - t < edgeFade) envGlobal = (durationSec - t) / edgeFade;
    } else {
      if (t < 0.06) envGlobal = t / 0.06;
      if (fadeOutStart != null && t > fadeOutStart) {
        envGlobal *= Math.max(0, 1 - (t - fadeOutStart) / (durationSec - fadeOutStart));
      }
    }

    out[i] = Math.tanh((kick + hat + snap + bass + pad + arp) * 1.1) * envGlobal * 0.72;
  }

  return out;
}

const files = [
  writeWav("click_key.wav", synthKeyClick()),
  writeWav("bass_hit.wav", synthBassHit()),
  writeWav("drop.wav", synthDrop()),
  writeWav("switch.wav", synthSwitch()),
  writeWav("chime.wav", synthChime()),
  writeWav("paste_pop.wav", synthPastePop()),
  writeWav("whoosh.wav", synthWhoosh()),
  writeWav("bell_outro.wav", synthBellOutro()),
  writeWav(
    "bgm_124bpm_50s.wav",
    synthModernElectronicBgm({
      durationSec: 50.0,
      bpm: 124,
      seamlessLoop: false,
      fadeOutStart: 47.2,
    }),
  ),
  writeWav(
    "bgm_128bpm_30s_loop.wav",
    synthModernElectronicBgm({
      durationSec: 30.0,
      bpm: 128,
      seamlessLoop: true,
      fadeOutStart: null,
    }),
  ),
];

console.log("Generated HyperFrames audio kit in", OUT_DIR);
for (const f of files) {
  console.log(` - ${f.filename}: ${f.bytes} bytes (${f.duration}s)`);
}
