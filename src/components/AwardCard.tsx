'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, Medal, Star, Trophy } from 'lucide-react';
import type { Award } from '@/types/resume';
import { SectionHeading } from '@/components/SectionHeading';

interface Props {
  data: Award[];
}

export function AwardCard({ data }: Props) {
  const levelOrder: Record<string, number> = {
    国家级: 0,
    省级: 1,
    华中赛区: 2,
    西部赛区: 3,
  };

  const sortedAwards = [...data].sort((a, b) => {
    const aLevel = Object.keys(levelOrder).find((level) => a.level.includes(level)) || '';
    const bLevel = Object.keys(levelOrder).find((level) => b.level.includes(level)) || '';
    return (levelOrder[aLevel] ?? 99) - (levelOrder[bLevel] ?? 99);
  });

  return (
    <Card className="overflow-hidden rounded-none border-x-0 border-y border-foreground/20 bg-transparent shadow-none">
      <CardHeader className="border-b border-foreground/15 bg-transparent px-0 py-6 md:px-0">
        <SectionHeading code="07" title="荣誉奖项" icon={Trophy} />
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid gap-px bg-border md:grid-cols-2">
          {sortedAwards.map((award, index) => (
            <motion.article
              key={award.name}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.07, duration: 0.35 }}
              viewport={{ once: true }}
              className="bg-card p-5"
            >
              <div className="flex items-center justify-between">
                <div className="flex h-9 w-9 items-center justify-center border border-primary/20 bg-primary/5 text-primary">
                  <Medal className="h-4.5 w-4.5" />
                </div>
                <span className="font-mono text-[9px] text-muted-foreground">AWARD / 0{index + 1}</span>
              </div>
              <h3 className="mt-5 font-bold leading-6">{award.name}</h3>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className="rounded-none border-primary/25 bg-primary/5 text-primary">
                  <Star className="mr-1 h-3 w-3" /> {award.level}
                </Badge>
                {award.rank && <span className="text-xs text-muted-foreground">个人排名：{award.rank}</span>}
              </div>
              <div className="mt-3 flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
                <Calendar className="h-3 w-3 text-primary" /> {award.year}
              </div>
            </motion.article>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
