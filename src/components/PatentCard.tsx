'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Patent } from '@/types/resume';
import { Award, FileText, Lightbulb } from 'lucide-react';
import { SectionHeading } from '@/components/SectionHeading';

interface Props {
  data: Patent[];
}

const categoryIcons = {
  发明专利: FileText,
  实用新型: Lightbulb,
  软著: Award,
};

export function PatentCard({ data }: Props) {
  return (
    <Card className="overflow-hidden rounded-none border-foreground/15 bg-card shadow-none">
      <CardHeader className="border-b border-foreground/12 bg-secondary/45 px-5 py-4 md:px-7">
        <SectionHeading code="05" title="专利成果" icon={FileText} />
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid gap-px bg-border md:grid-cols-3">
          {data.map((patent, index) => {
            const Icon = categoryIcons[patent.category as keyof typeof categoryIcons] || FileText;
            return (
              <motion.article
                key={patent.name}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08, duration: 0.35 }}
                viewport={{ once: true }}
                className="bg-card p-5 md:p-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-9 w-9 items-center justify-center border border-primary/20 bg-primary/5 text-primary">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <span className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">IP / 0{index + 1}</span>
                </div>
                <h3 className="mt-5 font-bold">{patent.name}</h3>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-4xl font-black tracking-[-0.05em]">{patent.count}</span>
                  <span className="text-sm text-muted-foreground">项</span>
                </div>
                {patent.ranks && patent.ranks.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {patent.ranks.map((rank, i) => (
                      <Badge key={i} variant="secondary" className="rounded-none font-mono text-[9px] font-normal">
                        排名 {rank}
                      </Badge>
                    ))}
                  </div>
                )}
              </motion.article>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
