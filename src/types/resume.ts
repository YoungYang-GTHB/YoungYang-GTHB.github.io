// 简历数据类型定义

export interface PersonalInfo {
  name: string;
  title: string;
  subtitle: string;
  tagline?: string;
  email: string;
  phone: string;
  location: string;
  hometown?: string;
  politicalStatus?: string;
  birthday?: string;
  github?: string;
  linkedin?: string;
  summary: string;
}

export interface Education {
  school: string;
  degree: string;
  major: string;
  period: string;
  gpa?: string;
  rank?: string;
  direction?: string;
  tags?: string[];
}

export interface SkillItem {
  name: string;
  level: string;
  description: string;
}

export interface Skills {
  ai: SkillItem[];
  programming: SkillItem[];
  embedded: SkillItem[];
  os: SkillItem[];
  tools: SkillItem[];
}

export interface ProjectGeneration {
  name: string;
  slug: string;
  images?: string[];
  videos?: string[];
}

export interface ProjectDetail {
  generations?: ProjectGeneration[];
  images?: string[];
  videos?: string[];
  documents?: { name: string; url: string }[];
  patents?: { name: string; url: string }[];
}

export interface Project {
  title: string;
  slug: string;
  period: string;
  role: string;
  level?: string;
  description: string;
  technologies: string[];
  achievements: string[];
  detail?: ProjectDetail;
}

export interface Experience {
  company: string;
  role: string;
  period: string;
  type?: string;
  description: string;
  achievements?: string[];
}

export interface Award {
  name: string;
  level: string;
  year: string;
  rank?: number;
  category: string;
}

export interface Honor {
  name: string;
  year: string;
  category: string;
}

export interface Patent {
  name: string;
  count: number;
  ranks: number[] | null;
  category: string;
}

export interface Certification {
  name: string;
  score: string;
}

export interface FeaturedLink {
  name: string;
  url: string;
  desc?: string;
}

export interface FeaturedHighlight {
  title: string;
  desc: string;
}

export interface FeaturedDemo {
  src: string;
  poster?: string;
  eyebrow?: string;
  title: string;
  description: string;
  model?: string;
  task?: string;
  platform?: string;
  note?: string;
}

export interface Featured {
  title: string;
  org: string;
  role: string;
  period: string;
  tagline?: string;
  summary: string;
  demo?: FeaturedDemo;
  highlights: FeaturedHighlight[];
  stack: string[];
  links: FeaturedLink[];
}

export interface ResumeData {
  personal: PersonalInfo;
  featured?: Featured;
  education: Education[];
  skills: Skills;
  projects: Project[];
  experience: Experience[];
  awards: Award[];
  honors: Honor[];
  patents: Patent[];
  certifications: Certification[];
}
