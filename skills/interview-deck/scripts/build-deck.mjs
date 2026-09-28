#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { imageSize } from "image-size";
import PptxGenJS from "pptxgenjs";

const sourceArg = process.argv[2];
if (!sourceArg) {
  console.error("Usage: build-deck.mjs <content.json>");
  process.exit(2);
}

const sourcePath = path.resolve(sourceArg);
const repoRoot = process.cwd();
const deck = JSON.parse(fs.readFileSync(sourcePath, "utf8"));
const pptx = new PptxGenJS();

const W = 13.333;
const H = 7.5;
const C = {
  navy: "0B1220",
  ink: "10233E",
  muted: "526176",
  pale: "E8EEF6",
  paper: "F6F8FB",
  white: "FFFFFF",
  cyan: "19B5C5",
  cyanPale: "DFF5F7",
  blue: "3A72F8",
  bluePale: "E8EFFF",
  amber: "F4A340",
  amberPale: "FFF0D8",
  green: "2CA58D",
  greenPale: "DFF4EF",
  red: "D95D69",
  redPale: "FBE7E9",
  grid: "DCE3ED",
};

const isZh = deck.meta.language === "zh-CN";
const F = {
  head: isZh ? "Noto Sans CJK SC" : "Liberation Sans",
  body: isZh ? "Noto Sans CJK SC" : "Liberation Sans",
};

pptx.layout = "LAYOUT_WIDE";
pptx.author = deck.meta.author;
pptx.company = "YoungYang";
pptx.subject = deck.meta.targetRole;
pptx.title = deck.meta.title;
pptx.lang = deck.meta.language;
pptx.theme = {
  headFontFace: F.head,
  bodyFontFace: F.body,
  lang: deck.meta.language,
};
pptx.defineSlideMaster({
  title: "INTERVIEW_LIGHT",
  background: { color: C.paper },
  objects: [
    { line: { x: 0.62, y: 0.38, w: 0.44, h: 0, line: { color: C.cyan, width: 4 } } },
    { text: { text: deck.meta.author, options: { x: 0.65, y: 7.12, w: 2.2, h: 0.18, fontFace: F.body, fontSize: 8.5, color: C.muted, margin: 0 } } },
    { text: { text: deck.meta.targetRole, options: { x: 9.0, y: 7.12, w: 3.65, h: 0.18, fontFace: F.body, fontSize: 8.5, color: C.muted, align: "right", margin: 0 } } },
  ],
  slideNumber: { x: 12.68, y: 7.08, w: 0.28, h: 0.2, fontFace: F.body, fontSize: 8.5, color: C.muted, align: "right", margin: 0 },
  margin: 0,
});

function asset(name) {
  const rel = deck.meta.assets?.[name];
  if (!rel) return null;
  const resolved = path.resolve(repoRoot, rel);
  if (!fs.existsSync(resolved)) throw new Error(`Missing asset ${name}: ${resolved}`);
  return resolved;
}

function imageDataUri(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mime = ext === ".png" ? "image/png" : "image/jpeg";
  return `data:${mime};base64,${fs.readFileSync(filePath).toString("base64")}`;
}

function addImageContain(slide, filePath, x, y, w, h) {
  const { width, height } = imageSize(filePath);
  if (!width || !height) throw new Error(`Cannot read image dimensions: ${filePath}`);
  const scale = Math.min(w / width, h / height);
  const imageW = width * scale;
  const imageH = height * scale;
  slide.addImage({
    path: filePath,
    x: x + (w - imageW) / 2,
    y: y + (h - imageH) / 2,
    w: imageW,
    h: imageH,
  });
}

function tx(slide, text, x, y, w, h, options = {}) {
  slide.addText(text, {
    x, y, w, h,
    fontFace: F.body,
    fontSize: 18,
    color: C.ink,
    margin: 0,
    breakLine: false,
    fit: "shrink",
    valign: "mid",
    ...options,
  });
}

function rect(slide, x, y, w, h, fill, radius = true, line = fill) {
  slide.addShape(radius ? pptx.ShapeType.roundRect : pptx.ShapeType.rect, {
    x, y, w, h,
    rectRadius: 0.06,
    fill: { color: fill },
    line: { color: line, transparency: line === fill ? 100 : 0, width: 1 },
  });
}

function line(slide, x, y, w, h, color = C.grid, width = 1.5, arrow = false) {
  slide.addShape(pptx.ShapeType.line, {
    x, y, w, h,
    line: { color, width, endArrowType: arrow ? "triangle" : undefined },
  });
}

function circle(slide, x, y, d, fill, label = "", color = C.white, size = 14) {
  slide.addShape(pptx.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  if (label) tx(slide, label, x, y, d, d, { fontSize: size, bold: true, color, align: "center" });
}

function title(slide, slideData, section) {
  tx(slide, section.toUpperCase(), 1.17, 0.31, 5.2, 0.24, { fontSize: 8.5, bold: true, color: C.cyan, charSpacing: 2.1 });
  tx(slide, slideData.title, 0.65, 0.68, 12.0, 0.55, { fontSize: 27, bold: true, color: C.ink, valign: "top" });
  tx(slide, slideData.takeaway, 0.66, 1.27, 11.7, 0.36, { fontSize: 12.5, color: C.muted, valign: "top" });
}

function pill(slide, label, x, y, w, color = C.cyan, fill = C.cyanPale) {
  rect(slide, x, y, w, 0.34, fill, true);
  tx(slide, label, x + 0.09, y, w - 0.18, 0.34, { fontSize: 10, bold: true, color, align: "center" });
}

function metric(slide, value, label, x, y, w, color = C.blue, note = "") {
  rect(slide, x, y, w, 1.08, C.white, true, C.grid);
  tx(slide, value, x + 0.18, y + 0.12, w - 0.36, 0.42, { fontSize: 23, bold: true, color });
  tx(slide, label, x + 0.18, y + 0.55, w - 0.36, 0.24, { fontSize: 11, bold: true, color: C.ink });
  if (note) tx(slide, note, x + 0.18, y + 0.81, w - 0.36, 0.16, { fontSize: 8.5, color: C.muted });
}

function bulletList(slide, items, x, y, w, rowH = 0.5, options = {}) {
  items.forEach((item, index) => {
    circle(slide, x, y + index * rowH + 0.12, 0.13, options.dot || C.cyan);
    tx(slide, item, x + 0.26, y + index * rowH, w - 0.26, rowH, {
      fontSize: options.fontSize || 14,
      color: options.color || C.ink,
      valign: "mid",
    });
  });
}

function notes(slide, slideData) {
  slide.addNotes(Array.isArray(slideData.notes) ? slideData.notes.join("\n") : slideData.notes);
}

function addCover(slideData) {
  const slide = pptx.addSlide();
  slide.background = { color: C.navy };
  const hero = asset(slideData.heroAsset || "hero");
  if (hero) {
    // The source hero and the slide are both 16:9. Fill the canvas directly so
    // the image is never stretched into the old portrait-shaped right column.
    slide.addImage({ path: hero, x: 0, y: 0, w: W, h: H });
    slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.navy, transparency: 42 }, line: { transparency: 100 } });
    slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 7.55, h: H, fill: { color: C.navy, transparency: 5 }, line: { transparency: 100 } });
  }
  line(slide, 0.72, 0.72, 0.52, 0, C.cyan, 4);
  tx(slide, slideData.kicker, 1.4, 0.57, 5.6, 0.34, { fontSize: 10, bold: true, color: C.cyan, charSpacing: 2.2 });
  tx(slide, slideData.name, 0.72, 1.43, 6.4, 0.74, { fontSize: 37, bold: true, color: C.white });
  tx(slide, slideData.role, 0.74, 2.24, 6.45, 0.55, { fontSize: 22, bold: true, color: "BFE8ED" });
  tx(slide, slideData.subtitle, 0.74, 3.02, 6.2, 1.25, { fontSize: 22, bold: true, color: C.white, valign: "top", breakLine: true });
  (slideData.chips || []).forEach((chip, index) => pill(slide, chip, 0.74 + index * 1.58, 4.64, 1.38, C.white, "1A2B43"));
  tx(slide, slideData.context, 0.74, 5.54, 6.15, 0.65, { fontSize: 13, color: "C9D3E0", valign: "top" });
  tx(slide, `${deck.meta.version}  ·  ${deck.meta.durationMinutes} min`, 0.74, 6.85, 3.4, 0.22, { fontSize: 9, color: "8EA0B7" });
  notes(slide, slideData);
}

function addProfile(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "01 / POSITIONING");
  rect(slide, 0.65, 1.82, 3.1, 4.95, C.navy, true);
  const portrait = asset(slideData.portraitAsset || "portrait");
  rect(slide, 0.91, 2.08, 2.58, 2.86, C.white, false);
  addImageContain(slide, portrait, 0.91, 2.08, 2.58, 2.86);
  tx(slide, slideData.label, 0.96, 5.18, 2.48, 0.82, { fontSize: 15.5, bold: true, color: C.white, align: "center", valign: "mid" });
  tx(slide, slideData.education, 0.96, 6.15, 2.48, 0.32, { fontSize: 10.5, color: "AFC0D5", align: "center" });

  (slideData.highlights || []).forEach((item, index) => {
    const x = 4.1 + index * 2.93;
    rect(slide, x, 2.0, 2.63, 2.2, [C.bluePale, C.cyanPale, C.amberPale][index], true);
    tx(slide, `0${index + 1}`, x + 0.18, 2.18, 0.48, 0.28, { fontSize: 11, bold: true, color: [C.blue, C.cyan, C.amber][index] });
    tx(slide, item.title, x + 0.18, 2.62, 2.25, 0.5, { fontSize: 17, bold: true });
    tx(slide, item.body, x + 0.18, 3.21, 2.25, 0.64, { fontSize: 12, color: C.muted, valign: "top" });
  });
  rect(slide, 4.1, 4.58, 8.5, 1.72, C.white, true, C.grid);
  tx(slide, slideData.principleLabel || "我的判断方式", 4.35, 4.82, 1.5, 0.28, { fontSize: 11, bold: true, color: C.cyan });
  tx(slide, slideData.principle, 4.35, 5.18, 7.82, 0.64, { fontSize: 20, bold: true, color: C.ink, valign: "top" });
  tx(slide, slideData.boundary, 4.35, 5.92, 7.82, 0.23, { fontSize: 9.5, color: C.muted });
  notes(slide, slideData);
}

function addCapability(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "02 / CAPABILITY MAP");
  const nodes = slideData.nodes || [];
  const startX = 0.72;
  const gap = 0.17;
  const boxW = (11.9 - gap * (nodes.length - 1)) / nodes.length;
  line(slide, 1.15, 3.17, 10.95, 0, C.grid, 2);
  nodes.forEach((node, index) => {
    const x = startX + index * (boxW + gap);
    const y = index % 2 === 0 ? 2.25 : 3.62;
    circle(slide, x + boxW / 2 - 0.18, 2.98, 0.36, index < 4 ? C.blue : C.cyan, `${index + 1}`, C.white, 10);
    rect(slide, x, y, boxW, 1.22, C.white, true, C.grid);
    tx(slide, node.title, x + 0.12, y + 0.15, boxW - 0.24, 0.32, { fontSize: 13, bold: true, align: "center" });
    tx(slide, node.body, x + 0.12, y + 0.52, boxW - 0.24, 0.5, { fontSize: 9.5, color: C.muted, align: "center", valign: "top" });
  });
  rect(slide, 1.28, 5.55, 10.76, 0.72, C.navy, true);
  tx(slide, slideData.summary, 1.62, 5.55, 10.08, 0.72, { fontSize: 16, bold: true, color: C.white, align: "center" });
  tx(slide, slideData.boundary, 1.28, 6.46, 10.76, 0.25, { fontSize: 9.5, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addJourney(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "02 / JOURNEY");
  const milestones = slideData.milestones || [];
  const startX = 0.72;
  const step = 2.43;
  const cardW = 2.13;
  line(slide, 1.0, 3.55, 10.75, 0, C.grid, 2.2);
  milestones.forEach((item, index) => {
    const x = startX + index * step;
    const upper = index % 2 === 0;
    const cardY = upper ? 1.92 : 4.08;
    const cardFill = [C.bluePale, C.cyanPale, C.greenPale, C.amberPale, C.bluePale][index % 5];
    const accent = [C.blue, C.cyan, C.green, C.amber, C.blue][index % 5];
    rect(slide, x, cardY, cardW, 1.35, cardFill, true);
    tx(slide, item.period, x + 0.16, cardY + 0.14, cardW - 0.32, 0.22, { fontSize: 9.3, bold: true, color: accent });
    tx(slide, item.title, x + 0.16, cardY + 0.43, cardW - 0.32, 0.36, { fontSize: 13.2, bold: true });
    tx(slide, item.proof, x + 0.16, cardY + 0.86, cardW - 0.32, 0.3, { fontSize: 9.5, color: C.muted, valign: "top" });
    const nodeX = x + cardW / 2 - 0.18;
    circle(slide, nodeX, 3.37, 0.36, accent, `${index + 1}`, C.white, 9.5);
    line(slide, nodeX + 0.18, upper ? cardY + 1.35 : 3.73, 0, upper ? 0.1 : 0.35, accent, 1.4);
  });
  rect(slide, 1.02, 5.82, 11.28, 0.58, C.navy, true);
  tx(slide, slideData.summary, 1.28, 5.82, 10.76, 0.58, { fontSize: 14.5, bold: true, color: C.white, align: "center" });
  tx(slide, slideData.boundary, 1.02, 6.53, 11.28, 0.25, { fontSize: 9.3, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addEarlyWork(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "03 / EARLY EXPLORATION");
  const product = slideData.product;
  const ai = slideData.ai;

  rect(slide, 0.72, 1.88, 5.83, 4.28, C.white, true, C.grid);
  pill(slide, product.tag, 0.98, 2.14, 1.34, C.blue, C.bluePale);
  const productImage = asset(product.asset);
  rect(slide, 0.98, 2.68, 2.58, 1.54, C.pale, false);
  addImageContain(slide, productImage, 0.98, 2.68, 2.58, 1.54);
  tx(slide, product.title, 3.82, 2.4, 2.38, 0.43, { fontSize: 17, bold: true });
  tx(slide, product.body, 3.82, 2.98, 2.35, 0.86, { fontSize: 11.2, color: C.muted, valign: "top" });
  tx(slide, product.evidence, 3.82, 4.07, 2.35, 0.3, { fontSize: 11, bold: true, color: C.blue });
  rect(slide, 0.98, 4.68, 5.31, 1.12, C.bluePale, true);
  tx(slide, slideData.contributionLabel || "个人贡献", 1.2, 4.88, 0.98, 0.25, { fontSize: 9.5, bold: true, color: C.blue });
  tx(slide, product.contribution, 2.22, 4.8, 3.82, 0.68, { fontSize: 11.2, bold: true, color: C.ink, valign: "top" });

  rect(slide, 6.79, 1.88, 5.82, 4.28, C.cyanPale, true);
  pill(slide, ai.tag, 7.06, 2.14, 1.34, C.cyan, C.white);
  tx(slide, ai.title, 7.06, 2.58, 5.17, 0.43, { fontSize: 17, bold: true });
  const flow = ai.flow || [];
  flow.forEach((label, index) => {
    const x = 7.06 + index * 1.72;
    rect(slide, x, 3.28, 1.39, 0.58, C.white, true, C.grid);
    tx(slide, label, x + 0.12, 3.28, 1.15, 0.58, { fontSize: 12.5, bold: true, color: C.ink, align: "center" });
    if (index < flow.length - 1) line(slide, x + 1.39, 3.57, 0.28, 0, C.cyan, 1.5, true);
  });
  (ai.outputs || []).forEach((item, index) => {
    rect(slide, 7.06 + index * 2.55, 4.2, 2.25, 0.62, C.white, true, C.grid);
    tx(slide, item, 7.2 + index * 2.55, 4.2, 1.97, 0.62, { fontSize: 11, bold: true, color: C.ink, align: "center" });
  });
  rect(slide, 7.06, 5.2, 5.17, 0.6, C.navy, true);
  tx(slide, ai.evidence, 7.3, 5.2, 4.69, 0.6, { fontSize: 12, bold: true, color: C.white, align: "center" });

  rect(slide, 1.05, 6.38, 11.22, 0.43, C.navy, true);
  tx(slide, slideData.bridge, 1.3, 6.38, 10.72, 0.43, { fontSize: 11.4, bold: true, color: C.white, align: "center" });
  tx(slide, slideData.boundary, 1.05, 6.86, 11.22, 0.2, { fontSize: 8.8, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addPortfolio(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "03 / PRODUCT ITERATION");
  const items = slideData.items || [];
  items.forEach((item, index) => {
    const x = 0.72 + index * 4.03;
    const imagePath = asset(item.asset);
    const accent = [C.blue, C.cyan, C.amber][index];
    rect(slide, x, 1.87, 3.62, 4.15, C.white, true, C.grid);
    rect(slide, x + 0.13, 2.02, 3.36, 2.02, C.pale, false);
    addImageContain(slide, imagePath, x + 0.13, 2.02, 3.36, 2.02);
    pill(slide, item.tag, x + 0.22, 4.22, 0.9, accent, index === 2 ? C.amberPale : index === 1 ? C.cyanPale : C.bluePale);
    tx(slide, item.title, x + 0.22, 4.65, 3.16, 0.36, { fontSize: 14.5, bold: true });
    tx(slide, item.body, x + 0.22, 5.06, 3.16, 0.43, { fontSize: 9.8, color: C.muted, valign: "top" });
    tx(slide, item.evidence, x + 0.22, 5.58, 3.16, 0.22, { fontSize: 9.2, bold: true, color: accent, align: "center" });
  });
  rect(slide, 1.13, 6.22, 11.07, 0.43, C.navy, true);
  tx(slide, slideData.contribution, 1.39, 6.22, 10.55, 0.43, { fontSize: 11.3, bold: true, color: C.white, align: "center" });
  tx(slide, slideData.boundary, 1.13, 6.72, 11.07, 0.22, { fontSize: 8.8, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addBreadth(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "04 / SYSTEM BREADTH");
  const items = slideData.items || [];
  items.forEach((item, index) => {
    const x = 0.72 + index * 4.03;
    const fills = [C.bluePale, C.cyanPale, C.greenPale];
    const accents = [C.blue, C.cyan, C.green];
    rect(slide, x, 1.9, 3.62, 3.98, fills[index], true);
    circle(slide, x + 0.25, 2.18, 0.52, accents[index], item.code, C.white, 8.7);
    tx(slide, item.title, x + 0.92, 2.14, 2.42, 0.42, { fontSize: 16, bold: true });
    tx(slide, item.role, x + 0.25, 2.84, 3.1, 0.27, { fontSize: 10, bold: true, color: accents[index] });
    bulletList(slide, item.points || [], x + 0.25, 3.28, 3.12, 0.62, { fontSize: 10.7, dot: accents[index] });
    rect(slide, x + 0.25, 5.21, 3.12, 0.44, C.white, true);
    tx(slide, item.evidence, x + 0.39, 5.21, 2.84, 0.44, { fontSize: 10, bold: true, color: C.ink, align: "center" });
  });
  rect(slide, 1.0, 6.15, 11.34, 0.52, C.navy, true);
  tx(slide, slideData.bridge, 1.28, 6.15, 10.78, 0.52, { fontSize: 13, bold: true, color: C.white, align: "center" });
  notes(slide, slideData);
}

function addSystem(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "03 / FLAGSHIP SYSTEM");
  const hero = asset(slideData.heroAsset || "hero");
  const video = slideData.videoAsset ? asset(slideData.videoAsset) : null;
  if (video) {
    slide.addMedia({ type: "video", path: video, cover: imageDataUri(hero), x: 0.65, y: 1.88, w: 5.37, h: 3.02 });
    pill(slide, slideData.videoLabel || "VIDEO", 0.86, 2.08, 1.72, C.white, C.navy);
  } else {
    slide.addImage({ path: hero, x: 0.65, y: 1.88, w: 5.37, h: 3.02 });
  }
  rect(slide, 0.86, 5.18, 4.95, 1.12, C.navy, true);
  tx(slide, slideData.challenge, 1.08, 5.34, 4.51, 0.7, { fontSize: 14, bold: true, color: C.white, valign: "top" });

  const layers = slideData.layers || [];
  layers.forEach((layer, index) => {
    const y = 1.91 + index * 0.86;
    const fill = [C.bluePale, C.cyanPale, C.greenPale, C.amberPale, C.white][index];
    rect(slide, 6.48, y, 5.99, 0.68, fill, true, C.grid);
    pill(slide, layer.label, 6.67, y + 0.17, 1.1, [C.blue, C.cyan, C.green, C.amber, C.ink][index], C.white);
    tx(slide, layer.body, 7.96, y + 0.08, 4.22, 0.51, { fontSize: 12.5, bold: index === layers.length - 1, color: C.ink });
  });
  tx(slide, slideData.ownership, 6.55, 6.35, 5.78, 0.37, { fontSize: 10.5, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addDataTraining(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "04 / DATA & TRAINING");
  tx(slide, slideData.comparisonTitle || "同一配方，两个评测域给出相反结论", 0.72, 1.87, 5.35, 0.35, { fontSize: 14, bold: true });
  const rows = slideData.comparisons || [];
  const max = Math.max(...rows.flatMap((row) => [row.before, row.after]));
  rows.forEach((row, index) => {
    const y = 2.42 + index * 1.38;
    tx(slide, row.label, 0.75, y, 1.2, 0.32, { fontSize: 12, bold: true });
    const scale = 3.8 / max;
    rect(slide, 2.0, y, Math.max(0.18, row.before * scale), 0.31, C.grid, false);
    tx(slide, row.beforeLabel, 2.08 + row.before * scale, y - 0.02, 1.0, 0.32, { fontSize: 10, color: C.muted });
    rect(slide, 2.0, y + 0.46, Math.max(0.18, row.after * scale), 0.31, index === 0 ? C.green : C.red, false);
    tx(slide, row.afterLabel, 2.08 + row.after * scale, y + 0.44, 1.2, 0.32, { fontSize: 10, bold: true, color: index === 0 ? C.green : C.red });
  });
  rect(slide, 0.72, 5.32, 5.4, 1.02, C.amberPale, true);
  tx(slide, slideData.decisionLabel || "结论", 0.94, 5.53, 0.65, 0.25, { fontSize: 10, bold: true, color: C.amber });
  tx(slide, slideData.decision, 1.62, 5.43, 4.18, 0.56, { fontSize: 13.5, bold: true });

  tx(slide, slideData.loopTitle || "数据—策略—失败回流闭环", 6.68, 1.87, 5.35, 0.35, { fontSize: 14, bold: true });
  (slideData.loop || []).forEach((item, index) => {
    const y = 2.36 + index * 0.86;
    circle(slide, 6.74, y, 0.47, index < 3 ? C.blue : C.cyan, `${index + 1}`, C.white, 11);
    if (index < slideData.loop.length - 1) line(slide, 6.975, y + 0.47, 0, 0.39, C.grid, 2);
    tx(slide, item.title, 7.43, y - 0.01, 1.48, 0.3, { fontSize: 12.5, bold: true });
    tx(slide, item.body, 8.92, y - 0.02, 3.45, 0.48, { fontSize: 10.5, color: C.muted, valign: "top" });
  });
  tx(slide, slideData.boundary, 6.72, 6.39, 5.52, 0.34, { fontSize: 9.5, color: C.muted });
  notes(slide, slideData);
}

function addPerformance(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "05 / INFERENCE PERFORMANCE");
  const summaryColors = [C.blue, C.cyan, C.amber];
  (slideData.summaryMetrics || []).forEach((item, index) => {
    metric(slide, item.value, item.label, 0.72 + index * 2.63, 1.83, 2.45, summaryColors[index], item.note);
  });

  const stages = slideData.stages || [];
  const max = Math.max(...stages.map((stage) => stage.value));
  stages.forEach((stage, index) => {
    const y = 3.27 + index * 0.47;
    tx(slide, stage.label, 0.74, y, 2.05, 0.25, { fontSize: 9.7, color: C.muted, align: "right" });
    const width = Math.max(0.27, 5.8 * stage.value / max);
    rect(slide, 2.98, y, width, 0.27, index === stages.length - 1 ? C.cyan : index < 4 ? C.blue : "6A8AF2", false);
    tx(slide, `${stage.value}${stage.unit || " ms"}`, 3.08 + width, y - 0.02, 1.12, 0.28, { fontSize: 9.5, bold: true, color: C.ink });
  });

  rect(slide, 10.15, 1.83, 2.48, 4.65, C.navy, true);
  tx(slide, slideData.methodTitle, 10.43, 2.11, 1.92, 0.5, { fontSize: 17, bold: true, color: C.white, align: "center" });
  bulletList(slide, slideData.lessons || [], 10.43, 2.92, 1.92, 0.72, { fontSize: 11, color: "DDE6F1", dot: C.cyan });
  tx(slide, slideData.boundary, 10.43, 5.78, 1.92, 0.48, { fontSize: 9, color: "9DB0C7", align: "center", valign: "top" });
  notes(slide, slideData);
}

function addDeployment(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "06 / REAL-ROBOT DELIVERY");
  (slideData.metrics || []).forEach((item, index) => metric(slide, item.value, item.label, 0.72 + index * 2.7, 1.82, 2.42, [C.cyan, C.green, C.blue][index], item.note));
  tx(slide, "把动作连续性拆成三层治理", 0.74, 3.28, 5.7, 0.35, { fontSize: 15, bold: true });
  const layers = slideData.layers || [];
  layers.forEach((layer, index) => {
    const x = 0.75 + index * 3.98;
    rect(slide, x, 3.85, 3.55, 1.78, [C.bluePale, C.cyanPale, C.greenPale][index], true);
    pill(slide, layer.label, x + 0.23, 4.08, 1.12, [C.blue, C.cyan, C.green][index], C.white);
    tx(slide, layer.title, x + 0.23, 4.54, 3.08, 0.35, { fontSize: 15, bold: true });
    tx(slide, layer.body, x + 0.23, 4.98, 3.08, 0.42, { fontSize: 10.5, color: C.muted, valign: "top" });
    if (index < layers.length - 1) line(slide, x + 3.56, 4.72, 0.39, 0, C.grid, 2, true);
  });
  rect(slide, 1.64, 6.09, 10.07, 0.54, C.amberPale, true);
  tx(slide, slideData.boundary, 1.91, 6.09, 9.52, 0.54, { fontSize: 10.5, bold: true, color: C.ink, align: "center" });
  notes(slide, slideData);
}

function addDebug(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, "07 · FALSIFIABLE DEBUGGING");
  rect(slide, 0.72, 1.85, 3.0, 4.8, C.navy, true);
  tx(slide, "现象", 1.0, 2.13, 0.7, 0.3, { fontSize: 10, bold: true, color: C.cyan });
  tx(slide, slideData.symptom, 1.0, 2.58, 2.43, 0.82, { fontSize: 20, bold: true, color: C.white, valign: "top" });
  line(slide, 1.0, 3.7, 2.42, 0, "40506A", 1);
  tx(slide, "可证伪判据", 1.0, 3.97, 1.2, 0.3, { fontSize: 10, bold: true, color: C.cyan });
  tx(slide, slideData.test, 1.0, 4.4, 2.43, 0.92, { fontSize: 16, bold: true, color: C.white, valign: "top" });
  tx(slide, slideData.boundary, 1.0, 5.72, 2.43, 0.55, { fontSize: 9.5, color: "AFC0D5", valign: "top" });

  const steps = slideData.steps || [];
  steps.forEach((step, index) => {
    const y = 1.92 + index * 0.77;
    const nodeColor = step.result === "根因" || step.result === "确认现象" ? C.red : step.result === "通过" ? C.green : C.blue;
    circle(slide, 4.13, y, 0.42, nodeColor, `${index + 1}`, C.white, 10);
    if (index < steps.length - 1) line(slide, 4.34, y + 0.42, 0, 0.35, C.grid, 2);
    tx(slide, step.hypothesis, 4.78, y - 0.01, 2.25, 0.3, { fontSize: 12, bold: true });
    pill(slide, step.result, 7.14, y + 0.01, 1.08, step.pass ? C.green : C.red, step.pass ? C.greenPale : C.redPale);
    tx(slide, step.evidence, 8.48, y - 0.03, 3.85, 0.45, { fontSize: 10.5, color: C.muted, valign: "top" });
  });
  rect(slide, 4.13, 5.95, 8.19, 0.7, C.cyanPale, true);
  tx(slide, slideData.result, 4.42, 5.95, 7.62, 0.7, { fontSize: 14, bold: true, color: C.ink, align: "center" });
  notes(slide, slideData);
}

function addTrainingFlow(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "07 · TRAINING LOOP");
  const stages = slideData.stages || [];
  const fills = [C.bluePale, C.bluePale, C.cyanPale, C.amberPale, C.greenPale];
  const accents = [C.blue, C.blue, C.cyan, C.amber, C.green];
  const startX = 0.72;
  const cardW = 2.28;
  const gap = 0.18;
  stages.forEach((stage, index) => {
    const x = startX + index * (cardW + gap);
    rect(slide, x, 1.92, cardW, 2.25, fills[index], true);
    pill(slide, stage.tag, x + 0.2, 2.15, 0.82, accents[index], C.white);
    tx(slide, stage.title, x + 0.2, 2.62, cardW - 0.4, 0.37, { fontSize: 15.5, bold: true });
    tx(slide, stage.body, x + 0.2, 3.06, cardW - 0.4, 0.58, { fontSize: 10.5, color: C.muted, valign: "top" });
    tx(slide, stage.output, x + 0.2, 3.76, cardW - 0.4, 0.2, { fontSize: 9.3, bold: true, color: accents[index], align: "center" });
    if (index < stages.length - 1) line(slide, x + cardW, 3.02, gap, 0, C.grid, 1.6, true);
  });

  (slideData.evidence || []).forEach((item, index) => {
    const x = 0.72 + index * 4.03;
    rect(slide, x, 4.55, 3.66, 1.32, C.white, true, C.grid);
    tx(slide, item.label, x + 0.2, 4.74, 1.0, 0.25, { fontSize: 9.5, bold: true, color: accents[index + 1] });
    tx(slide, item.value, x + 0.2, 5.08, 3.24, 0.35, { fontSize: 16, bold: true, color: C.ink });
    tx(slide, item.note, x + 0.2, 5.48, 3.24, 0.22, { fontSize: 8.8, color: C.muted });
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 1.14, y: 6.17, w: 10.72, h: 0,
    line: { color: C.cyan, width: 2, beginArrowType: "triangle" },
  });
  rect(slide, 4.24, 6.0, 4.86, 0.34, C.paper, false);
  tx(slide, slideData.loopLabel, 4.4, 6.03, 4.55, 0.28, { fontSize: 10, bold: true, color: C.cyan, align: "center" });
  tx(slide, slideData.boundary, 0.9, 6.52, 11.56, 0.26, { fontSize: 9.5, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addWorldModel(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "08 / WORLD MODEL RESEARCH");
  tx(slide, slideData.pipelineTitle, 0.72, 1.86, 6.25, 0.35, { fontSize: 14.5, bold: true });
  const visual = slideData.visualAsset ? asset(slideData.visualAsset) : null;
  const visualSequence = (slideData.visualAssets || []).map((name) => asset(name));
  if (visualSequence.length) {
    rect(slide, 0.71, 2.25, 5.99, 1.93, C.white, false, C.grid);
    visualSequence.forEach((imagePath, index) => {
      const imageW = 1.72;
      const x = 0.82 + index * 1.93;
      addImageContain(slide, imagePath, x, 2.3, imageW, 1.76);
      if (index < visualSequence.length - 1) line(slide, x + imageW, 3.18, 0.2, 0, C.cyan, 1.4, true);
    });
    tx(slide, slideData.visualCaption, 0.76, 4.22, 5.87, 0.28, { fontSize: 9.2, color: C.muted, align: "center" });
  } else if (visual) {
    rect(slide, 0.71, 2.25, 5.99, 1.93, C.white, false, C.grid);
    addImageContain(slide, visual, 0.73, 2.27, 5.95, 1.874);
    tx(slide, slideData.visualCaption, 0.76, 4.22, 5.87, 0.28, { fontSize: 9.2, color: C.muted, align: "center" });
  } else {
    (slideData.pipeline || []).forEach((node, index) => {
      const x = 0.73 + index * 1.55;
      rect(slide, x, 2.43, 1.29, 1.17, index === slideData.pipeline.length - 1 ? C.cyanPale : C.white, true, C.grid);
      tx(slide, node.title, x + 0.1, 2.59, 1.09, 0.3, { fontSize: 11, bold: true, align: "center" });
      tx(slide, node.body, x + 0.1, 2.98, 1.09, 0.39, { fontSize: 8.5, color: C.muted, align: "center", valign: "top" });
      if (index < slideData.pipeline.length - 1) line(slide, x + 1.29, 3.0, 0.25, 0, C.grid, 1.5, true);
    });
  }
  const evidenceColors = [C.cyan, C.blue];
  (slideData.evidenceMetrics || []).forEach((item, index) => {
    metric(slide, item.value, item.label, 0.73 + index * 2.81, visual || visualSequence.length ? 4.58 : 4.08, index === 0 ? 2.6 : 2.95, evidenceColors[index], item.note);
  });

  rect(slide, 7.03, 1.88, 5.58, 4.78, C.navy, true);
  tx(slide, slideData.findingsTitle || "研究结论：价值在分叉，不在复杂度", 7.34, 2.16, 4.96, 0.48, { fontSize: 18, bold: true, color: C.white });
  (slideData.findings || []).forEach((finding, index) => {
    const y = 2.93 + index * 0.92;
    const statusW = isZh ? 0.86 : 1.12;
    const findingX = 7.57 + statusW;
    const findingW = 12.15 - findingX;
    pill(slide, finding.status, 7.34, y, statusW, finding.color === "green" ? C.green : finding.color === "amber" ? C.amber : C.red, "19263A");
    tx(slide, finding.title, findingX, y - 0.02, findingW, 0.3, { fontSize: 12.5, bold: true, color: C.white });
    tx(slide, finding.body, findingX, y + 0.31, findingW, 0.34, { fontSize: 9.3, color: "AFC0D5", valign: "top" });
  });
  tx(slide, slideData.boundary, 7.34, 5.95, 4.96, 0.45, { fontSize: 9.5, color: "91A5BD", valign: "top" });
  notes(slide, slideData);
}

function addEngineering(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "09 / SYSTEMS FOUNDATION");
  const items = slideData.items || [];
  items.forEach((item, index) => {
    const y = 1.93 + index * 0.92;
    circle(slide, 0.75, y, 0.45, index < 3 ? C.blue : C.cyan, item.code, C.white, 9.5);
    tx(slide, item.title, 1.42, y - 0.01, 2.08, 0.31, { fontSize: 13, bold: true });
    tx(slide, item.body, 3.48, y - 0.01, 4.82, 0.45, { fontSize: 10.7, color: C.muted, valign: "top" });
  });
  rect(slide, 8.83, 1.85, 3.78, 2.33, C.navy, true);
  tx(slide, slideData.chainTitle || "策略输出之后", 9.08, 2.05, 3.28, 0.28, { fontSize: 10, bold: true, color: C.cyan, align: "center" });
  const chain = slideData.chain || ["仿真 / 运动学", "ROS 总控与通信", "嵌入式实时执行", "双臂 / 底盘机构"];
  chain.forEach((label, index) => {
    rect(slide, 9.24, 2.48 + index * 0.4, 2.96, 0.28, index === chain.length - 1 ? "24445C" : "172A42", true);
    tx(slide, label, 9.38, 2.48 + index * 0.4, 2.68, 0.28, { fontSize: 9.5, bold: true, color: C.white, align: "center" });
  });
  rect(slide, 8.83, 4.45, 3.78, 1.27, C.navy, true);
  tx(slide, slideData.result, 9.08, 4.68, 3.28, 0.72, { fontSize: 16, bold: true, color: C.white, align: "center", valign: "mid" });
  rect(slide, 0.75, 6.07, 11.86, 0.55, C.bluePale, true);
  tx(slide, slideData.bridge, 1.04, 6.07, 11.28, 0.55, { fontSize: 12, bold: true, color: C.ink, align: "center" });
  if (slideData.boundary) tx(slide, slideData.boundary, 0.88, 6.69, 11.6, 0.2, { fontSize: 8.8, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addFit(slideData) {
  const slide = pptx.addSlide("INTERVIEW_LIGHT");
  title(slide, slideData, slideData.section || "10 / ROLE FIT");
  (slideData.strengths || []).forEach((item, index) => {
    const x = 0.73 + index * 4.04;
    const colors = [[C.bluePale, C.blue], [C.cyanPale, C.cyan], [C.amberPale, C.amber]][index];
    rect(slide, x, 1.92, 3.67, 2.02, colors[0], true);
    tx(slide, `0${index + 1}`, x + 0.23, 2.15, 0.48, 0.28, { fontSize: 10, bold: true, color: colors[1] });
    tx(slide, item.title, x + 0.23, 2.58, 3.17, 0.38, { fontSize: 17, bold: true });
    tx(slide, item.body, x + 0.23, 3.08, 3.17, 0.55, { fontSize: 11.5, color: C.muted, valign: "top" });
  });
  tx(slide, slideData.planTitle || "进入团队后的 30 / 60 / 90 天", 0.74, 4.42, 5.1, 0.35, { fontSize: 15, bold: true });
  line(slide, 1.03, 5.34, 10.96, 0, C.grid, 2);
  (slideData.plan || []).forEach((item, index) => {
    const x = 1.03 + index * 5.45;
    circle(slide, x, 5.1, 0.48, index === 0 ? C.blue : C.cyan, item.day, C.white, 9);
    tx(slide, item.title, x + 0.72, 4.98, 1.58, 0.31, { fontSize: 12.5, bold: true });
    tx(slide, item.body, x + 0.72, 5.38, 4.15, 0.63, { fontSize: 10.5, color: C.muted, valign: "top" });
  });
  tx(slide, slideData.boundary, 0.76, 6.48, 11.78, 0.25, { fontSize: 9.5, color: C.muted, align: "center" });
  notes(slide, slideData);
}

function addClosing(slideData) {
  const slide = pptx.addSlide();
  slide.background = { color: C.navy };
  line(slide, 0.75, 0.72, 0.55, 0, C.cyan, 4);
  tx(slide, slideData.kicker, 1.48, 0.57, 3.9, 0.35, { fontSize: 10, bold: true, color: C.cyan, charSpacing: 2 });
  tx(slide, slideData.title, 0.75, 1.38, 5.7, 0.72, { fontSize: 34, bold: true, color: C.white });
  tx(slide, slideData.takeaway, 0.77, 2.18, 5.6, 0.65, { fontSize: 18, color: "B8C7D9", valign: "top" });
  (slideData.memories || []).forEach((item, index) => {
    const y = 3.34 + index * 0.83;
    circle(slide, 0.79, y, 0.42, [C.blue, C.cyan, C.amber][index], `${index + 1}`, C.white, 10);
    tx(slide, item, 1.47, y - 0.02, 4.92, 0.47, { fontSize: 14, bold: true, color: C.white });
  });
  rect(slide, 7.32, 0.78, 5.23, 5.92, "142238", true);
  tx(slide, "Q&A", 7.77, 1.3, 4.34, 0.8, { fontSize: 36, bold: true, color: C.white, align: "center" });
  tx(slide, slideData.questionPrompt, 7.78, 2.32, 4.32, 0.62, { fontSize: 14, color: "B8C7D9", align: "center", valign: "top" });
  line(slide, 8.26, 3.23, 3.36, 0, "344964", 1);
  (slideData.contact || []).forEach((item, index) => {
    tx(slide, item.label, 8.02, 3.63 + index * 0.68, 0.88, 0.28, { fontSize: 9.5, bold: true, color: C.cyan });
    tx(slide, item.value, 9.03, 3.58 + index * 0.68, 2.84, 0.36, { fontSize: 12, color: C.white });
  });
  tx(slide, deck.meta.version, 11.26, 7.02, 1.28, 0.18, { fontSize: 8.5, color: "71849C", align: "right" });
  notes(slide, slideData);
}

const renderers = {
  cover: addCover,
  profile: addProfile,
  capability: addCapability,
  journey: addJourney,
  "early-work": addEarlyWork,
  portfolio: addPortfolio,
  breadth: addBreadth,
  system: addSystem,
  "data-training": addDataTraining,
  performance: addPerformance,
  deployment: addDeployment,
  debugging: addDebug,
  "training-flow": addTrainingFlow,
  "world-model": addWorldModel,
  engineering: addEngineering,
  fit: addFit,
  closing: addClosing,
};

for (const slideData of deck.slides) {
  const render = renderers[slideData.layout];
  if (!render) throw new Error(`Unsupported layout: ${slideData.layout} (${slideData.id})`);
  render(slideData);
}

const output = path.resolve(repoRoot, deck.meta.output);
fs.mkdirSync(path.dirname(output), { recursive: true });
await pptx.writeFile({ fileName: output, compression: true });
console.log(`Wrote ${deck.slides.length} slides to ${output}`);
