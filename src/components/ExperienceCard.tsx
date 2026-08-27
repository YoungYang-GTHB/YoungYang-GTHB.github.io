'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Briefcase, Building2, Calendar } from 'lucide-react';
import type { Experience } from '@/types/resume';
import { SectionHeading } from '@/components/SectionHeading';

interface Props {
  data: Experience[];
}

export function ExperienceCard({ data }: Props) {
  return (
    <Card className="overflow-hidden rounded-none border-x-0 border-y border-foreground/20 bg-transparent shadow-none">
      <CardHeader className="border-b border-foreground/15 bg-transparent px-0 py-6 md:px-0">
        <SectionHeading code="06" title="实践经历" icon={Briefcase} />
      </CardHeader>
      <CardContent className="divide-y divide-foreground/12 p-0">
        {data.map((exp, index) => (
          <motion.article
            key={`${exp.company}-${exp.period}`}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06, duration: 0.38 }}
            viewport={{ once: true }}
            className="grid gap-4 px-0 py-7 md:grid-cols-[12rem_minmax(0,1fr)] md:gap-10 md:px-0 md:py-9"
          >
            <div>
              <div className="inline-flex items-center gap-2 font-mono text-[10px] tracking-[0.04em] text-primary">
                <Calendar className="h-3.5 w-3.5" />
                {exp.period}
              </div>
              <div className="mt-2 font-mono text-[9px] tracking-[0.14em] text-muted-foreground">
                LOG / {String(index + 1).padStart(2, '0')}
              </div>
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <Building2 className="h-4.5 w-4.5 text-primary" />
                <h3 className="text-lg font-bold tracking-[-0.015em]">{exp.company}</h3>
                {exp.type && (
                  <Badge variant="outline" className="rounded-none border-primary/25 bg-primary/5 text-primary">
                    {exp.type}
                  </Badge>
                )}
              </div>
              <p className="mt-1 text-sm font-semibold text-primary">{exp.role}</p>
              <p className="mt-3 max-w-4xl text-sm leading-7 text-muted-foreground">{exp.description}</p>
              {exp.achievements && exp.achievements.length > 0 && (
                <ul className="mt-4 grid gap-x-8 gap-y-2 lg:grid-cols-2">
                  {exp.achievements.map((item, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm leading-6 text-muted-foreground">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 bg-signal" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </motion.article>
        ))}
      </CardContent>
    </Card>
  );
}
