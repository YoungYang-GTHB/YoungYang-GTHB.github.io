'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import type { Honor } from '@/types/resume';
import { Medal, Star } from 'lucide-react';
import { SectionHeading } from '@/components/SectionHeading';

interface Props {
  data: Honor[];
}

export function HonorCard({ data }: Props) {
  return (
    <Card className="overflow-hidden rounded-none border-foreground/15 bg-card shadow-none">
      <CardHeader className="border-b border-foreground/12 bg-secondary/45 px-5 py-4 md:px-7">
        <SectionHeading code="08" title="学业荣誉" icon={Star} />
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid gap-px bg-border md:grid-cols-3">
          {data.map((honor, index) => (
            <motion.article
              key={honor.name}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.07, duration: 0.35 }}
              viewport={{ once: true }}
              className="bg-card p-5"
            >
              <div className="flex items-center justify-between">
                <div className="flex h-9 w-9 items-center justify-center border border-primary/20 bg-primary/5 text-primary">
                  <Star className="h-4.5 w-4.5" />
                </div>
                <span className="font-mono text-[9px] text-muted-foreground">HONOR / 0{index + 1}</span>
              </div>
              <h3 className="mt-5 font-bold leading-6">{honor.name}</h3>
              <div className="mt-3 flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
                <Medal className="h-3.5 w-3.5 text-primary" /> {honor.year}
              </div>
            </motion.article>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
