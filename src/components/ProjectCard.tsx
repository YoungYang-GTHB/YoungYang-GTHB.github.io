'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import type { Project } from '@/types/resume';
import { Rocket, Calendar, User, CheckCircle2, ArrowRight, ArrowUpRight } from 'lucide-react';
import Link from 'next/link';

interface Props {
  data: Project[];
}

export function ProjectCard({ data }: Props) {
  return (
    <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-accent/5 shadow-xl">
      <CardHeader className="border-b bg-gradient-to-r from-accent/10 via-primary/10 to-accent/10 pb-6">
        <CardTitle className="flex items-center gap-3 text-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-primary shadow-lg">
            <Rocket className="h-6 w-6 text-primary-foreground" />
          </div>
          <span className="text-gradient text-gradient-cyan">项目经历</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-8">
          {data.map((project, index) => (
            <motion.div
              key={project.title}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              viewport={{ once: true }}
              className="group relative"
            >
              {/* 卡片容器 - 添加点击跳转 */}
              <div className="relative overflow-hidden rounded-2xl border bg-card/50 p-6 backdrop-blur-sm transition-all card-hover">
                {/* 渐变装饰 */}
                <div className="absolute -right-20 -top-20 h-40 w-40 rounded-full bg-gradient-to-br from-primary/10 to-accent/10 blur-3xl transition-opacity group-hover:opacity-70" />

                <div className="relative">
                  {/* 标题和日期 */}
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="text-xl font-bold text-gradient bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                          {project.title}
                        </h3>
                        {project.level && (
                          <Badge className="bg-gradient-to-r from-primary to-accent text-white border-0 text-xs">
                            {project.level}
                          </Badge>
                        )}
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                        <User className="h-4 w-4" />
                        {project.role}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 rounded-full bg-secondary/50 px-4 py-2 text-sm font-medium">
                      <Calendar className="h-4 w-4 text-primary" />
                      {project.period}
                    </div>
                  </div>

                  {/* 项目描述 */}
                  <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                    {project.description}
                  </p>

                  {/* 技术栈标签 */}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {project.technologies.map((tech, techIndex) => (
                      <motion.div
                        key={tech}
                        initial={{ scale: 0.9, opacity: 0 }}
                        whileInView={{ scale: 1, opacity: 1 }}
                        transition={{ delay: index * 0.1 + techIndex * 0.05, duration: 0.2 }}
                        viewport={{ once: true }}
                      >
                        <Badge
                          variant="outline"
                          className="group/badge relative overflow-hidden px-3 py-1.5 text-xs font-medium transition-all hover:border-primary hover:bg-primary/10 hover:shadow-md"
                        >
                          <span className="relative z-10">{tech}</span>
                          <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform group-hover/badge:translate-x-full" />
                        </Badge>
                      </motion.div>
                    ))}
                  </div>

                  {/* 成就列表 */}
                  <ul className="mt-5 space-y-3">
                    {project.achievements.map((achievement, i) => (
                      <motion.li
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 + i * 0.05, duration: 0.3 }}
                        viewport={{ once: true }}
                        className="flex items-start gap-3"
                      >
                        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                        <span className="text-sm leading-relaxed text-muted-foreground">
                          {achievement}
                        </span>
                      </motion.li>
                    ))}
                  </ul>

                  {/* 查看详情按钮 */}
                  <div className="mt-6 flex justify-end">
                    <Button
                      asChild
                      variant="outline"
                      size="sm"
                      className="group/btn gap-2 transition-all hover:border-primary hover:bg-primary hover:text-primary-foreground"
                    >
                      <Link href={`/projects/${project.slug}`}>
                        查看详情
                        <ArrowUpRight className="h-4 w-4 transition-transform group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </div>

              {index < data.length - 1 && (
                <div className="relative py-6">
                  <Separator className="opacity-50" />
                  <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center justify-center">
                    <div className="rounded-full bg-background p-2">
                      <ArrowRight className="h-4 w-4 rotate-90 text-muted-foreground" />
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
