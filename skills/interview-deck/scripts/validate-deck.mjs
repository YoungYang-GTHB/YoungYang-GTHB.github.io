#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
if (!args[0]) {
  console.error("Usage: validate-deck.mjs <content.json> [--peer <content.json>]");
  process.exit(2);
}

const sourcePath = path.resolve(args[0]);
const peerIndex = args.indexOf("--peer");
const peerPath = peerIndex >= 0 && args[peerIndex + 1] ? path.resolve(args[peerIndex + 1]) : null;
const errors = [];
const warnings = [];

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    errors.push(`${filePath}: ${error.message}`);
    return null;
  }
}

const deck = readJson(sourcePath);
if (!deck) process.exit(1);

const requiredMeta = ["language", "version", "title", "author", "targetRole", "durationMinutes", "output", "assets"];
for (const key of requiredMeta) {
  if (deck.meta?.[key] === undefined || deck.meta?.[key] === "") errors.push(`meta.${key} is required`);
}
if (!Array.isArray(deck.slides) || deck.slides.length === 0) errors.push("slides must be a non-empty array");

const ids = new Set();
for (const [index, slide] of (deck.slides || []).entries()) {
  const at = `slides[${index}]`;
  for (const key of ["id", "layout", "title", "takeaway", "notes"]) {
    if (!slide[key]) errors.push(`${at}.${key} is required`);
  }
  if (slide.id && ids.has(slide.id)) errors.push(`${at}.id duplicates ${slide.id}`);
  ids.add(slide.id);
  if (typeof slide.notes === "string" && slide.notes.length < 35) warnings.push(`${slide.id}: speaker notes look too short`);
  if (slide.title?.length > (deck.meta.language === "zh-CN" ? 34 : 90)) warnings.push(`${slide.id}: title may wrap`);
  if ((slide.metrics || slide.stages || slide.results) && !(slide.boundary || slide.footnote)) {
    warnings.push(`${slide.id}: quantitative content has no boundary or footnote`);
  }
}

for (const [name, relPath] of Object.entries(deck.meta?.assets || {})) {
  const resolved = path.resolve(process.cwd(), relPath);
  if (!fs.existsSync(resolved)) errors.push(`meta.assets.${name} does not exist: ${resolved}`);
}

if (peerPath) {
  const peer = readJson(peerPath);
  if (peer) {
    const ownIds = (deck.slides || []).map((slide) => slide.id);
    const peerIds = (peer.slides || []).map((slide) => slide.id);
    if (JSON.stringify(ownIds) !== JSON.stringify(peerIds)) {
      errors.push("peer slide IDs/order do not match");
    }
    for (let i = 0; i < Math.min(deck.slides.length, peer.slides.length); i += 1) {
      const metricKeys = Object.keys(deck.slides[i].metrics || {}).sort();
      const peerMetricKeys = Object.keys(peer.slides[i].metrics || {}).sort();
      if (JSON.stringify(metricKeys) !== JSON.stringify(peerMetricKeys)) {
        errors.push(`${deck.slides[i].id}: peer metric keys do not match`);
      }
    }
  }
}

for (const warning of warnings) console.warn(`WARN: ${warning}`);
if (errors.length) {
  for (const error of errors) console.error(`ERROR: ${error}`);
  process.exit(1);
}

console.log(`Validated ${deck.slides.length} slides (${deck.meta.language}, ${deck.meta.version})`);
if (warnings.length) console.log(`${warnings.length} warning(s); visual review still required`);
