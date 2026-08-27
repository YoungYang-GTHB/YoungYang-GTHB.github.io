'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Education } from '@/types/resume';
import { Award, BookOpen, Calendar, GraduationCap, TrendingUp } from 'lucide-react';
import { SectionHeading } from '@/components/SectionHeading';

interface Props {
  data: Education[];
}

export function EducationCard({ data }: Props) {
  return (
    <Card className="overflow-hidden rounded-none border-x-0 border-y border-foreground/20 bg-transparent shadow-none">
      <CardHeader className="border-b border-foreground/15 bg-transparent px-0 py-6 md:px-0">
        <SectionHeading code="02" title="教育背景" icon={GraduationCap} />
      </CardHeader>
      <CardContent className="divide-y divide-foreground/12 p-0">
        {data.map((edu, index) => (
          <motion.article
            key={edu.school}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08, duration: 0.4 }}
            viewport={{ once: true }}
            className="grid gap-5 px-0 py-8 md:grid-cols-[minmax(0,1fr)_auto] md:px-0 md:py-10"
          >
            <div className="flex gap-4">
              <span className="pt-1 font-mono text-[10px] text-primary">0{index + 1}</span>
              <div>
                <div className="flex flex-wrap items-center gap-2.5">
                  <h3 className="text-xl font-bold tracking-[-0.02em]">{edu.school}</h3>
                  {edu.tags?.map((tag) => (
                    <Badge key={tag} variant="outline" className="rounded-none border-primary/25 bg-primary/5 text-primary">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted-foreground">
                  <span className="inline-flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-primary" />
                    {edu.degree} · {edu.major}
                  </span>
                  {edu.direction && (
                    <span className="inline-flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-primary" />
                      {edu.direction}
                    </span>
                  )}
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {edu.gpa && (
                    <Badge variant="secondary" className="rounded-none gap-1.5 font-mono text-[10px]">
                      <Award className="h-3 w-3" /> {edu.gpa}
                    </Badge>
                  )}
                  {edu.rank && (
                    <Badge variant="secondary" className="rounded-none gap-1.5 font-mono text-[10px]">
                      <TrendingUp className="h-3 w-3" /> {edu.rank}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-start md:justify-end">
              <div className="inline-flex items-center gap-2 border border-foreground/12 bg-background px-3 py-2 font-mono text-[10px] tracking-[0.06em] text-muted-foreground">
                <Calendar className="h-3.5 w-3.5 text-primary" />
                {edu.period}
              </div>
            </div>
          </motion.article>
        ))}
      </CardContent>
    </Card>
  );
}
