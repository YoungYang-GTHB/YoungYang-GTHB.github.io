import { getResumeData } from '@/lib/resume';
import { Header } from '@/components/Header';
import { StatBand } from '@/components/StatBand';
import { FeaturedProject } from '@/components/FeaturedProject';
import { SkillMatrix } from '@/components/SkillMatrix';
import { ProjectCard } from '@/components/ProjectCard';
import { EducationCard } from '@/components/EducationCard';
import { ExperienceCard } from '@/components/ExperienceCard';
import { AwardCard } from '@/components/AwardCard';
import { HonorCard } from '@/components/HonorCard';
import { PatentCard } from '@/components/PatentCard';
import { ThemeToggle } from '@/components/ThemeToggle';
import { MobileNav } from '@/components/MobileNav';
import { JsonLd } from '@/components/JsonLd';
import { ArrowUpRight, Bot } from 'lucide-react';

export default function Home() {
  const resumeData = getResumeData();

  return (
    <div className="relative min-h-screen overflow-clip bg-background">
      {/* JSON-LD 结构化数据 */}
      <JsonLd data={resumeData.personal} />
      
      {/* 实验记录纸背景 */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 lab-grid opacity-45" />
      </div>

      {/* 顶部导航 */}
      <nav className="sticky top-0 z-50 w-full border-b border-foreground/12 bg-background/92 backdrop-blur-xl">
        <div className="mx-auto flex h-[4.75rem] max-w-[90rem] items-center justify-between px-5 md:px-10">
          <div className="flex items-center gap-3">
            <MobileNav name={resumeData.personal.name} />
            <div className="flex h-7 w-7 items-center justify-center bg-foreground text-background">
              <Bot className="h-4 w-4" />
            </div>
            <div className="leading-none">
              <span className="block text-sm font-bold tracking-tight">{resumeData.personal.name}</span>
              <span className="font-mono text-[9px] tracking-[0.18em] text-muted-foreground">EMBODIED AI / 2027</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden items-center gap-5 text-xs font-medium md:flex">
              <a href="#featured" className="transition-colors hover:text-signal">真机项目</a>
              <a href="#experience" className="transition-colors hover:text-primary">经历</a>
              <a href="#projects" className="transition-colors hover:text-primary">项目</a>
              <a href={`mailto:${resumeData.personal.email}`} className="inline-flex items-center gap-1 border-b border-signal/60 pb-0.5 text-primary">
                联系我 <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </nav>

      {/* 主要内容 */}
      <main className="mx-auto max-w-[90rem] px-5 md:px-10">
        <div className="space-y-16 md:space-y-24">
          {/* 个人信息头部 */}
          <div id="header">
            <Header data={resumeData.personal} />
          </div>

          {/* 成果数字带 */}
          <div id="stats" className="-mt-16 md:-mt-24">
            <StatBand data={resumeData} />
          </div>

          {/* 旗舰主项目 · 实习工作 */}
          {resumeData.featured && (
            <div id="featured" className="-mt-16 scroll-mt-20 md:-mt-24">
              <FeaturedProject data={resumeData.featured} />
            </div>
          )}

          {/* 实践经历 */}
          <div id="experience" className="scroll-mt-20">
            <ExperienceCard data={resumeData.experience} />
          </div>

          {/* 专业技能 */}
          <div id="skills" className="scroll-mt-20">
            <SkillMatrix data={resumeData.skills} />
          </div>

          {/* 项目经历 */}
          <div id="projects" className="scroll-mt-20">
            <ProjectCard data={resumeData.projects} />
          </div>

          {/* 教育背景 */}
          <div id="education" className="scroll-mt-20">
            <EducationCard data={resumeData.education} />
          </div>

          <div className="grid gap-12 lg:grid-cols-2">
            {/* 科研成果 · 专利 */}
            <div id="patents" className="scroll-mt-20">
              <PatentCard data={resumeData.patents} />
            </div>

            {/* 荣誉奖项 */}
            <div id="awards" className="scroll-mt-20">
              <AwardCard data={resumeData.awards} />
            </div>
          </div>

          {/* 学业荣誉 */}
          <div id="honors" className="scroll-mt-20">
            <HonorCard data={resumeData.honors} />
          </div>
        </div>
      </main>

      {/* 页脚 */}
      <footer className="relative mt-24 border-t border-foreground/15 py-8">
        <div className="mx-auto max-w-[90rem] px-5 md:px-10">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <p className="text-center text-sm text-muted-foreground">
              © {new Date().getFullYear()} {resumeData.personal.name}. All rights reserved.
            </p>
            <div className="font-mono text-[10px] tracking-[0.16em] text-muted-foreground">ROBOTS · VLA · EMBEDDED SYSTEMS</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
