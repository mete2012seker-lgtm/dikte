import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..", "..");
const VIDEO_HF = path.resolve(__dirname, "..");

const PROJECTS = ["yatay-tr", "yatay-en", "dikey-tr", "dikey-en"];

const IMAGES = [
  "ekran-dikte-koyu.png",
  "ekran-dikte-acik.png",
  "ekran-modeller.png",
  "icon.png",
];

const FONTS = [
  // Inter (latin + latin-ext, weights 400, 500, 600, 700, 800)
  ...["400", "500", "600", "700", "800"].flatMap((w) => [
    `inter/files/inter-latin-${w}-normal.woff2`,
    `inter/files/inter-latin-ext-${w}-normal.woff2`,
  ]),
  // Plus Jakarta Sans (latin + latin-ext, weights 600, 700, 800)
  ...["600", "700", "800"].flatMap((w) => [
    `plus-jakarta-sans/files/plus-jakarta-sans-latin-${w}-normal.woff2`,
    `plus-jakarta-sans/files/plus-jakarta-sans-latin-ext-${w}-normal.woff2`,
  ]),
  // JetBrains Mono (latin + latin-ext, weights 500, 600, 700)
  ...["500", "600", "700"].flatMap((w) => [
    `jetbrains-mono/files/jetbrains-mono-latin-${w}-normal.woff2`,
    `jetbrains-mono/files/jetbrains-mono-latin-ext-${w}-normal.woff2`,
  ]),
];

const AUDIO_DIR = path.join(VIDEO_HF, "shared-audio");
const audioFiles = fs.readdirSync(AUDIO_DIR).filter((f) => f.endsWith(".wav"));

for (const proj of PROJECTS) {
  const assetsDir = path.join(VIDEO_HF, proj, "assets");
  const fontsDir = path.join(assetsDir, "fonts");
  const audioOutDir = path.join(assetsDir, "audio");

  fs.mkdirSync(assetsDir, { recursive: true });
  fs.mkdirSync(fontsDir, { recursive: true });
  fs.mkdirSync(audioOutDir, { recursive: true });

  for (const img of IMAGES) {
    fs.copyFileSync(path.join(ROOT, "docs", "assets", img), path.join(assetsDir, img));
  }

  for (const fontRel of FONTS) {
    const src = path.join(ROOT, "video", "node_modules", "@fontsource", fontRel);
    const dst = path.join(fontsDir, path.basename(fontRel));
    fs.copyFileSync(src, dst);
  }

  for (const wav of audioFiles) {
    // Only copy the matching BGM for each orientation to keep project folders tidy
    if (wav.startsWith("bgm_124bpm") && proj.startsWith("dikey")) continue;
    if (wav.startsWith("bgm_128bpm") && proj.startsWith("yatay")) continue;
    fs.copyFileSync(path.join(AUDIO_DIR, wav), path.join(audioOutDir, wav));
  }

  console.log(`Synced assets to video-hf/${proj}/assets/`);
}
