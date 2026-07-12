import { getResumeData } from '@/lib/resume';
import { Header } from '@/components/Header';
import { StatBand } from '@/components/StatBand';
import { SkillMatrix } from '@/components/SkillMatrix';
import { ProjectCard } from '@/components/ProjectCard';
import { EducationCard } from '@/components/EducationCard';
import { ExperienceCard } from '@/components/ExperienceCard';
import { AwardCard } from '@/components/AwardCard';
import { HonorCard } from '@/components/HonorCard';
import { PatentCard } from '@/components/PatentCard';
import { ThemeToggle } from '@/components/ThemeToggle';
import { MobileNav } from '@/components/MobileNav';
import { Separator } from '@/components/ui/separator';
import { JsonLd } from '@/components/JsonLd';
import { Sparkles, Zap } from 'lucide-react';

export default function Home() {
  const resumeData = getResumeData();

  return (
    <div className="relative min-h-screen bg-background">
      {/* JSON-LD 结构化数据 */}
      <JsonLd data={resumeData.personal} />
      
      {/* 动态背景装饰 */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* 渐变光斑 */}
        <div className="absolute -left-1/4 top-1/4 h-[500px] w-[500px] animate-pulse rounded-full bg-gradient-to-br from-primary/20 to-accent/20 blur-3xl" style={{ animationDuration: '4s' }} />
        <div className="absolute -right-1/4 bottom-1/4 h-[500px] w-[500px] animate-pulse rounded-full bg-gradient-to-tl from-cyan-500/15 to-blue-500/15 blur-3xl" style={{ animationDuration: '5s', animationDelay: '1s' }} />
        <div className="absolute left-1/2 top-1/2 h-[400px] w-[400px] -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-gradient-to-r from-purple-500/10 to-pink-500/10 blur-3xl" style={{ animationDuration: '6s', animationDelay: '2s' }} />
        
        {/* 网格装饰 */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.02)_1px,transparent_1px)] bg-[size:60px_60px]" />
      </div>

      {/* 顶部导航 */}
      <nav className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-2">
            <MobileNav />
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent">
              <Zap className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {resumeData.personal.name}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden text-xs text-muted-foreground md:inline-block">
              {resumeData.personal.title}
            </span>
            <ThemeToggle />
          </div>
        </div>
      </nav>

      {/* 主要内容 */}
      <main className="container mx-auto px-4 py-8 md:py-12 md:px-6">
        <div className="mx-auto max-w-6xl space-y-8">
          {/* 个人信息头部 */}
          <div id="header">
            <Header data={resumeData.personal} />
          </div>

          {/* 成果数字带 */}
          <div id="stats">
            <StatBand data={resumeData} />
          </div>

          <Separator className="opacity-30" />

          {/* 教育背景 */}
          <div id="education">
            <EducationCard data={resumeData.education} />
          </div>

          {/* 专业技能 */}
          <div id="skills">
            <SkillMatrix data={resumeData.skills} />
          </div>

          {/* 项目经历 */}
          <div id="projects">
            <ProjectCard data={resumeData.projects} />
          </div>

          {/* 科研成果 · 专利 */}
          <div id="patents">
            <PatentCard data={resumeData.patents} />
          </div>

          {/* 实践经历 */}
          <div id="experience">
            <ExperienceCard data={resumeData.experience} />
          </div>

          {/* 荣誉奖项 */}
          <div id="awards">
            <AwardCard data={resumeData.awards} />
          </div>

          {/* 学业荣誉 */}
          <div id="honors">
            <HonorCard data={resumeData.honors} />
          </div>
        </div>
      </main>

      {/* 页脚 */}
      <footer className="relative border-t bg-background/50 backdrop-blur-sm py-8">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <p className="text-center text-sm text-muted-foreground">
              © {new Date().getFullYear()} {resumeData.personal.name}. All rights reserved.
            </p>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Sparkles className="h-4 w-4" />
              <span>Built with Next.js & Tailwind CSS</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
