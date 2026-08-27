'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { Project } from '@/types/resume';
import { ArrowUpRight, Calendar, CheckCircle2, Rocket, User } from 'lucide-react';
import Link from 'next/link';
import { SectionHeading } from '@/components/SectionHeading';

interface Props {
  data: Project[];
}

export function ProjectCard({ data }: Props) {
  return (
    <Card className="overflow-hidden rounded-none border-x-0 border-y border-foreground/20 bg-transparent shadow-none">
      <CardHeader className="border-b border-foreground/15 bg-transparent px-0 py-6 md:px-0">
        <SectionHeading code="04" title="项目经历" icon={Rocket} />
      </CardHeader>
      <CardContent className="divide-y divide-foreground/12 p-0">
        {data.map((project, index) => (
          <motion.article
            key={project.title}
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.07, duration: 0.4 }}
            viewport={{ once: true }}
            className="relative px-0 py-8 md:px-0 md:py-10"
          >
            <div className="grid gap-5 md:grid-cols-[3.5rem_minmax(0,1fr)]">
              <div className="font-mono text-[11px] text-primary">P-{String(index + 1).padStart(2, '0')}</div>
              <div>
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2.5">
                      <h3 className="text-xl font-bold tracking-[-0.02em]">{project.title}</h3>
                      {project.level && (
                        <Badge variant="outline" className="rounded-none border-primary/25 bg-primary/5 text-primary">
                          {project.level}
                        </Badge>
                      )}
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                      <User className="h-4 w-4 text-primary" />
                      {project.role}
                    </div>
                  </div>
                  <div className="inline-flex w-fit items-center gap-2 border border-foreground/12 bg-background px-3 py-2 font-mono text-[10px] text-muted-foreground">
                    <Calendar className="h-3.5 w-3.5 text-primary" />
                    {project.period}
                  </div>
                </div>

                <p className="mt-4 max-w-5xl text-sm leading-7 text-muted-foreground">{project.description}</p>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  {project.technologies.map((tech) => (
                    <Badge key={tech} variant="secondary" className="rounded-none px-2.5 py-1 font-mono text-[9px] font-normal">
                      {tech}
                    </Badge>
                  ))}
                </div>

                <ul className="mt-5 grid gap-x-8 gap-y-2.5 lg:grid-cols-2">
                  {project.achievements.map((achievement, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm leading-6 text-muted-foreground">
                      <CheckCircle2 className="mt-1 h-3.5 w-3.5 shrink-0 text-signal" />
                      <span>{achievement}</span>
                    </li>
                  ))}
                </ul>

                <div className="mt-5 flex justify-end">
                  <Button asChild variant="outline" size="sm" className="rounded-none border-foreground/15 bg-transparent hover:border-primary hover:bg-primary hover:text-primary-foreground">
                    <Link href={`/projects/${project.slug}`}>
                      查看详情 <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            </div>
          </motion.article>
        ))}
      </CardContent>
    </Card>
  );
}
