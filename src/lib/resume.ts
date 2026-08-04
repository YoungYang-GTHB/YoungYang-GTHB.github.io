import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { ResumeData } from '@/types/resume';

function resolvePublicAsset(assetPath: string): string | null {
  const publicDirectory = path.resolve(process.cwd(), 'public');
  const candidate = path.resolve(publicDirectory, assetPath.replace(/^\/+/, ''));

  if (!candidate.startsWith(`${publicDirectory}${path.sep}`)) {
    return null;
  }

  return fs.existsSync(candidate) ? candidate : null;
}

export function getResumeData(): ResumeData {
  const filePath = path.join(process.cwd(), 'content', 'resume.yaml');
  const fileContents = fs.readFileSync(filePath, 'utf8');
  const data = yaml.load(fileContents) as ResumeData;

  // 媒体文件未放入 public 时不渲染演示区，避免部署后出现空播放器或 404。
  if (data.featured?.demo && !resolvePublicAsset(data.featured.demo.src)) {
    data.featured.demo = undefined;
  } else if (
    data.featured?.demo?.poster &&
    !resolvePublicAsset(data.featured.demo.poster)
  ) {
    data.featured.demo.poster = undefined;
  }

  return data;
}
