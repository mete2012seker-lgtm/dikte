import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.resolve(__dirname, "..", "public", "sfx");
const SAMPLE_RATE = 44100;

fs.mkdirSync(OUT_DIR, { recursive: true });

// Deterministic PRNG (Mulberry32) so every SFX build is bit-for-bit repeatable.
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
  buf.writeUInt32LE(16, 16); // PCM chunk size
  buf.writeUInt16LE(1, 20); // PCM format
  buf.writeUInt16LE(1, 22); // Mono
  buf.writeUInt32LE(SAMPLE_RATE, 24);
  buf.writeUInt32LE(SAMPLE_RATE * 2, 28);
  buf.writeUInt16LE(2, 32); // Block align
  buf.writeUInt16LE(16, 34); // Bits per sample
  buf.write("data", 36);
  buf.writeUInt32LE(dataBytes, 40);

  for (let i = 0; i < numSamples; i++) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    const pcm = clamped < 0 ? Math.round(clamped * 32768) : Math.round(clamped * 32767);
    buf.writeInt16LE(pcm, 44 + i * 2);
  }

  const outPath = path.join(OUT_DIR, filename);
  fs.writeFileSync(outPath, buf);
  return { filename, bytes: buf.length };
}

function synthKeyTap() {
  const dur = 0.055;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const rng = createRng(101);
  let lp = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const envClick = Math.exp(-t * 280);
    const envBody = Math.exp(-t * 115);
    const noise = (rng() * 2 - 1);
    lp = lp * 0.68 + noise * 0.32;
    const body = Math.sin(2 * Math.PI * (340 - t * 2400) * t) * 0.52;
    const top = Math.sin(2 * Math.PI * 1650 * t) * 0.22 * envClick;
    const attackFade = Math.min(1, i / 18);
    out[i] = attackFade * (lp * 0.35 * envClick + body * envBody + top) * 0.72;
  }
  return out;
}

function synthKeyBackspace() {
  const dur = 0.07;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const rng = createRng(202);
  let lp = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const env = Math.exp(-t * 88);
    const noise = rng() * 2 - 1;
    lp = lp * 0.84 + noise * 0.16;
    const thud = Math.sin(2 * Math.PI * (195 - t * 950) * t) * 0.65;
    const attackFade = Math.min(1, i / 22);
    out[i] = attackFade * (thud + lp * 0.25) * env * 0.78;
  }
  return out;
}

function synthWhoosh() {
  const dur = 0.38;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const rng = createRng(303);
  let bp1 = 0;
  let bp2 = 0;
  for (let i = 0; i < len; i++) {
    const p = i / len;
    const env = Math.sin(Math.PI * p) ** 1.35;
    const noise = rng() * 2 - 1;
    // Smooth two-pole lowpass/bandpass sweep
    const cutoff = 0.04 + 0.18 * Math.sin(Math.PI * p);
    bp1 += cutoff * (noise - bp1);
    bp2 += cutoff * (bp1 - bp2);
    const air = bp1 - bp2 * 0.62;
    const subSine = Math.sin(2 * Math.PI * (140 + 180 * p) * (i / SAMPLE_RATE)) * 0.08;
    out[i] = (air * 0.95 + subSine) * env * 0.65;
  }
  return out;
}

function synthBassHit() {
  const dur = 0.42;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  let phase = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 42 + 68 * Math.exp(-t * 16);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const env = Math.min(1, i / 40) * Math.exp(-t * 7.8);
    const fund = Math.sin(phase);
    const warm = Math.sin(phase * 2) * 0.18 * Math.exp(-t * 14);
    out[i] = Math.tanh((fund + warm) * 1.15) * env * 0.78;
  }
  return out;
}

function synthChime(freqA, freqB, dur) {
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  const half = Math.floor(len * 0.44);
  let pA = 0;
  let pB = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    pA += (2 * Math.PI * freqA) / SAMPLE_RATE;
    pB += (2 * Math.PI * freqB) / SAMPLE_RATE;

    const envA = Math.min(1, i / 90) * Math.exp(-t * 18);
    const noteA = (Math.sin(pA) + 0.25 * Math.sin(pA * 2)) * envA;

    let noteB = 0;
    if (i >= half) {
      const tb = (i - half) / SAMPLE_RATE;
      const envB = Math.min(1, (i - half) / 90) * Math.exp(-tb * 14);
      noteB = (Math.sin(pB) + 0.22 * Math.sin(pB * 2)) * envB;
    }
    out[i] = (noteA * 0.5 + noteB * 0.65) * 0.55;
  }
  return out;
}

function synthPop() {
  const dur = 0.09;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  let phase = 0;
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 160 + 260 * Math.exp(-t * 42);
    phase += (2 * Math.PI * freq) / SAMPLE_RATE;
    const env = Math.min(1, i / 25) * Math.exp(-t * 36);
    out[i] = Math.sin(phase) * env * 0.62;
  }
  return out;
}

function synthShimmer() {
  const dur = 0.55;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  // Cmaj9 airy chord: C5, E5, G5, B5, D6
  const freqs = [523.25, 659.25, 783.99, 987.77, 1174.66];
  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    const p = i / len;
    const env = Math.sin(Math.PI * p) ** 1.1 * Math.exp(-t * 2.2);
    let sum = 0;
    for (let k = 0; k < freqs.length; k++) {
      const entry = Math.max(0, Math.min(1, (p - k * 0.04) * 5));
      const detune = 1 + Math.sin(2 * Math.PI * (1.8 + k * 0.4) * t) * 0.0025;
      sum += Math.sin(2 * Math.PI * freqs[k] * detune * t) * entry * (0.28 - k * 0.03);
    }
    out[i] = sum * env * 0.48;
  }
  return out;
}

function synthAmbientBed() {
  const dur = 45.5;
  const len = Math.floor(SAMPLE_RATE * dur);
  const out = new Float32Array(len);
  // Warm analog Cmaj9 -> Am9 slow pad
  const voices = [
    { f1: 130.81, f2: 110.0, amp: 0.28 }, // C3 -> A2
    { f1: 196.0, f2: 164.81, amp: 0.20 }, // G3 -> E3
    { f1: 246.94, f2: 246.94, amp: 0.16 }, // B3
    { f1: 293.66, f2: 261.63, amp: 0.14 }, // D4 -> C4
    { f1: 329.63, f2: 329.63, amp: 0.10 }, // E4
  ];
  const phases = new Float64Array(voices.length);

  for (let i = 0; i < len; i++) {
    const t = i / SAMPLE_RATE;
    // Slow 16-second harmonic breath between chord I and VI
    const blend = 0.5 - 0.5 * Math.cos((2 * Math.PI * t) / 16);
    const swell = 0.82 + 0.18 * Math.sin((2 * Math.PI * t) / 9);
    let sample = 0;
    for (let v = 0; v < voices.length; v++) {
      const freq = voices[v].f1 + (voices[v].f2 - voices[v].f1) * blend;
      phases[v] += (2 * Math.PI * freq) / SAMPLE_RATE;
      const tone = Math.sin(phases[v]) + 0.16 * Math.sin(phases[v] * 2);
      sample += tone * voices[v].amp;
    }
    const fadeIn = Math.min(1, t / 1.2);
    const fadeOut = Math.min(1, (dur - t) / 1.5);
    out[i] = sample * swell * fadeIn * fadeOut * 0.42;
  }
  return out;
}

const files = [
  writeWav("key_tap.wav", synthKeyTap()),
  writeWav("key_backspace.wav", synthKeyBackspace()),
  writeWav("whoosh.wav", synthWhoosh()),
  writeWav("bass_hit.wav", synthBassHit()),
  writeWav("mic_on.wav", synthChime(523.25, 659.25, 0.18)),
  writeWav("mic_off.wav", synthChime(659.25, 523.25, 0.16)),
  writeWav("pop.wav", synthPop()),
  writeWav("shimmer.wav", synthShimmer()),
  writeWav("ambient_bed.wav", synthAmbientBed()),
];

console.log("Generated SFX kit in", OUT_DIR);
for (const f of files) {
  console.log(` - ${f.filename}: ${f.bytes} bytes`);
}
