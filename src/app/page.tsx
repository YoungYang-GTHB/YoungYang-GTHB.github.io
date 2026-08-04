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
        <div className="absolute inset-0 lab-grid opacity-55" />
        <div className="absolute -right-40 top-20 h-[34rem] w-[34rem] rounded-full bg-[radial-gradient(circle,rgba(203,198,76,0.16),transparent_68%)]" />
      </div>

      {/* 顶部导航 */}
      <nav className="sticky top-0 z-50 w-full border-b border-foreground/10 bg-background/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-8">
          <div className="flex items-center gap-3">
            <MobileNav />
            <div className="flex h-8 w-8 items-center justify-center bg-foreground text-background">
              <Bot className="h-4 w-4" />
            </div>
            <div className="leading-none">
              <span className="block text-sm font-bold tracking-tight">{resumeData.personal.name}</span>
              <span className="font-mono text-[9px] tracking-[0.18em] text-muted-foreground">EMBODIED AI / 2027</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden items-center gap-5 text-xs font-medium md:flex">
              <a href="#featured" className="transition-colors hover:text-primary">真机项目</a>
              <a href="#experience" className="transition-colors hover:text-primary">经历</a>
              <a href="#projects" className="transition-colors hover:text-primary">项目</a>
              <a href={`mailto:${resumeData.personal.email}`} className="inline-flex items-center gap-1 text-primary">
                联系我 <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </nav>

      {/* 主要内容 */}
      <main className="mx-auto max-w-7xl px-4 py-8 md:px-8 md:py-12">
        <div className="space-y-12 md:space-y-16">
          {/* 个人信息头部 */}
          <div id="header">
            <Header data={resumeData.personal} />
          </div>

          {/* 旗舰主项目 · 实习工作 */}
          {resumeData.featured && (
            <div id="featured" className="scroll-mt-20">
              <FeaturedProject data={resumeData.featured} />
            </div>
          )}

          {/* 成果数字带 */}
          <div id="stats">
            <StatBand data={resumeData} />
          </div>

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
      <footer className="relative mt-20 border-t border-foreground/10 py-8">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
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
