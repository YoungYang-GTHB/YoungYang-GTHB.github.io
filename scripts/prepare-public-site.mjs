#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import yaml from 'js-yaml';

const projectRoot = path.resolve(import.meta.dirname, '..');
const privateSiteRoot = path.resolve(projectRoot, process.argv[2] || 'career/site');
const sourceData = path.join(privateSiteRoot, 'content', 'resume.yaml');
const sourcePublic = path.join(privateSiteRoot, 'public');
const outputData = path.resolve(projectRoot, process.argv[3] || 'content/resume.public.yaml');
const outputPublic = path.resolve(projectRoot, process.argv[4] || 'public');

if (!fs.existsSync(sourceData) || !fs.statSync(sourceData).isFile()) {
  throw new Error(`Private resume data not found: ${sourceData}`);
}
if (!fs.existsSync(sourcePublic) || !fs.statSync(sourcePublic).isDirectory()) {
  throw new Error(`Private asset root not found: ${sourcePublic}`);
}

const data = yaml.load(fs.readFileSync(sourceData, 'utf8'));
delete data.application;
for (const key of ['birthday', 'hometown', 'politicalStatus', 'accepts_city_transfer']) {
  delete data.personal?.[key];
}

// Certificates and patent originals remain private. Portfolio images and videos are
// published only when referenced by the sanitized profile.
for (const project of data.projects || []) {
  if (project.detail) {
    delete project.detail.documents;
    delete project.detail.patents;
  }
}

function pruneUnpublishableAssets(value) {
  if (Array.isArray(value)) {
    return value.map(pruneUnpublishableAssets).filter((item) => item !== undefined);
  }
  if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      const sanitized = pruneUnpublishableAssets(child);
      if (sanitized === undefined) delete value[key];
      else value[key] = sanitized;
    }
    return value;
  }
  if (typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')) {
    const relativePath = value.replace(/^\/+/, '');
    const source = path.resolve(sourcePublic, relativePath);
    if (!source.startsWith(`${sourcePublic}${path.sep}`) || !fs.existsSync(source) || !fs.statSync(source).isFile()) {
      return undefined;
    }
  }
  return value;
}
pruneUnpublishableAssets(data);

const assetPaths = new Set();
function collectAssets(value) {
  if (Array.isArray(value)) return value.forEach(collectAssets);
  if (value && typeof value === 'object') return Object.values(value).forEach(collectAssets);
  if (typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')) assetPaths.add(value.replace(/^\/+/, ''));
}
collectAssets(data);

fs.mkdirSync(path.dirname(outputData), { recursive: true });
fs.writeFileSync(outputData, yaml.dump(data, { lineWidth: 120, noRefs: true }), 'utf8');

for (const relativePath of assetPaths) {
  const source = path.resolve(sourcePublic, relativePath);
  const destination = path.resolve(outputPublic, relativePath);
  if (!source.startsWith(`${sourcePublic}${path.sep}`) || !destination.startsWith(`${outputPublic}${path.sep}`)) {
    throw new Error(`Rejected asset path outside the allowed roots: ${relativePath}`);
  }
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.copyFileSync(source, destination);
}

console.log(`Prepared sanitized profile with ${assetPaths.size} allowlisted assets.`);
