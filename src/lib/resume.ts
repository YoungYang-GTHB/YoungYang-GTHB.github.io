import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { ResumeData } from '@/types/resume';

export function getResumeData(): ResumeData {
  const filePath = path.join(process.cwd(), 'content', 'resume.yaml');
  const fileContents = fs.readFileSync(filePath, 'utf8');
  const data = yaml.load(fileContents) as ResumeData;
  return data;
}
