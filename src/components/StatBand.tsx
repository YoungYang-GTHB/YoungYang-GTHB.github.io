'use client';

import { motion } from 'framer-motion';
import { Landmark, Lightbulb, ShieldCheck, FileCode2, Trophy } from 'lucide-react';
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
    { icon: Landmark, value: nationalProjects, label: '国家级重点课题' },
    { icon: Lightbulb, value: patentCount('发明专利'), label: '发明专利' },
    { icon: ShieldCheck, value: patentCount('实用新型'), label: '实用新型专利' },
    { icon: FileCode2, value: patentCount('软著'), label: '软件著作权' },
    { icon: Trophy, value: data.awards.length, label: '学科竞赛获奖' },
  ].filter((s) => s.value > 0);

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.6 }}
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:gap-4 lg:grid-cols-5"
    >
      {stats.map((s, i) => {
        const Icon = s.icon;
        return (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08, duration: 0.5 }}
            className="group relative overflow-hidden rounded-2xl border bg-card/50 p-5 text-center backdrop-blur-xl transition-all hover:-translate-y-1 hover:shadow-lg md:p-6"
          >
            <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full bg-primary/10 blur-2xl transition-opacity group-hover:opacity-100 md:opacity-0" />
            <Icon className="mx-auto mb-2 h-5 w-5 text-primary/70" />
            <div className="text-gradient text-gradient-primary text-4xl font-bold tracking-tight md:text-5xl">
              {s.value}
            </div>
            <div className="mt-1.5 text-xs text-muted-foreground md:text-sm">
              {s.label}
            </div>
          </motion.div>
        );
      })}
    </motion.section>
  );
}
