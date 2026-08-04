'use client';

import { motion } from 'framer-motion';
import type { ResumeData } from '@/types/resume';

interface Props {
  data: ResumeData;
}

export function StatBand({ data }: Props) {
  const patentCount = (cat: string) =>
    data.patents
      .filter((p) => p.category === cat)
      .reduce((sum, p) => sum + (p.count ?? 0), 0);

  const nationalProjects = data.projects.filter(
    (p) => p.level && p.level.includes('国家级')
  ).length;

  const stats = [
    { value: nationalProjects, label: '国家级重点课题' },
    { value: patentCount('发明专利'), label: '发明专利' },
    { value: patentCount('实用新型'), label: '实用新型专利' },
    { value: patentCount('软著'), label: '软件著作权' },
    { value: data.awards.length, label: '学科竞赛获奖' },
  ].filter((stat) => stat.value > 0);

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.5 }}
      className="border-y border-foreground/15"
    >
      <div className="grid grid-cols-2 md:grid-cols-5">
        {stats.map((stat, index) => (
          <div
            key={stat.label}
            className={`relative px-4 py-5 md:px-6 md:py-7 ${
              index > 0 ? 'md:border-l md:border-foreground/15' : ''
            } ${index % 2 === 1 ? 'border-l border-foreground/15 md:border-l' : ''} ${
              index >= 2 ? 'border-t border-foreground/15 md:border-t-0' : ''
            }`}
          >
            <div className="font-mono text-[9px] tracking-[0.16em] text-muted-foreground">
              EVIDENCE / {String(index + 1).padStart(2, '0')}
            </div>
            <div className="mt-2 text-3xl font-black tracking-[-0.05em] md:text-4xl">
              {String(stat.value).padStart(2, '0')}
            </div>
            <div className="mt-1 text-xs text-muted-foreground md:text-sm">{stat.label}</div>
          </div>
        ))}
      </div>
    </motion.section>
  );
}
