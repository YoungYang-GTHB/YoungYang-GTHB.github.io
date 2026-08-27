'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Skills } from '@/types/resume';
import { Brain, Code2, Cpu, Monitor, Wrench } from 'lucide-react';
import { SectionHeading } from '@/components/SectionHeading';

interface Props {
  data: Skills;
}

const categoryIcons = {
  ai: Brain,
  programming: Code2,
  embedded: Cpu,
  os: Monitor,
  tools: Wrench,
};

const categoryNames = {
  ai: 'AI · 具身智能',
  programming: '编程语言',
  embedded: '嵌入式开发',
  os: '机器人与系统',
  tools: '开发工具',
};

export function SkillMatrix({ data }: Props) {
  const categories = Object.entries(data) as Array<[keyof Skills, Skills[keyof Skills]]>;

  return (
    <Card className="overflow-hidden rounded-none border-x-0 border-y border-foreground/20 bg-transparent shadow-none">
      <CardHeader className="border-b border-foreground/15 bg-transparent px-0 py-6 md:px-0">
        <SectionHeading code="03" title="专业技能" icon={Code2} />
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid gap-px bg-border md:grid-cols-2">
          {categories.map(([category, skills], index) => {
            const Icon = categoryIcons[category];
            return (
              <motion.section
                key={category}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.06, duration: 0.35 }}
                viewport={{ once: true }}
                className="bg-background p-6 last:md:col-span-2 md:p-8"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center border border-primary/20 bg-primary/5 text-primary">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <div className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">
                      CAPABILITY / {String(index + 1).padStart(2, '0')}
                    </div>
                    <h3 className="mt-0.5 font-bold">{categoryNames[category]}</h3>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {skills.map((skill) => (
                    <Badge
                      key={skill.name}
                      variant="secondary"
                      className="cursor-default rounded-none border border-foreground/8 px-3 py-2 text-xs font-normal transition-colors hover:border-primary/30 hover:bg-primary/5"
                      title={skill.description}
                    >
                      <span className="font-semibold text-foreground">{skill.name}</span>
                      <span className="mx-1.5 text-muted-foreground">·</span>
                      <span className="font-mono text-[9px] text-primary">{skill.level}</span>
                    </Badge>
                  ))}
                </div>
              </motion.section>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
