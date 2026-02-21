'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Briefcase, Calendar, Building2 } from 'lucide-react';
import type { Experience } from '@/types/resume';

interface Props {
  data: Experience[];
}

const typeColors: Record<string, string> = {
  '实习': 'from-blue-500 to-cyan-500',
  '培训': 'from-purple-500 to-pink-500',
  '工作': 'from-green-500 to-emerald-500',
};

export function ExperienceCard({ data }: Props) {
  return (
    <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-blue-500/5 shadow-xl">
      <CardHeader className="border-b bg-gradient-to-r from-blue-500/10 via-cyan-500/10 to-blue-500/10 pb-6">
        <CardTitle className="flex items-center gap-3 text-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg">
            <Briefcase className="h-6 w-6 text-white" />
          </div>
          <span className="text-gradient" style={{ backgroundImage: 'var(--gradient-ocean)' }}>实践经历</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-8">
          {data.map((exp, index) => {
            const typeColor = typeColors[exp.type || '工作'] || 'from-blue-500 to-cyan-500';
            const isLeft = index % 2 === 0;

            return (
              <motion.div
                key={exp.company}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                viewport={{ once: true }}
                className="relative flex items-center"
              >
                {/* 左侧内容 */}
                {isLeft ? (
                  <>
                    <div className="flex w-1/2 justify-end md:flex">
                      <div className="hidden flex-1 flex-col items-end gap-2 md:flex">
                        <div className="rounded-2xl border bg-card/80 p-5 backdrop-blur-sm card-hover md:text-right">
                          <div className="flex items-center justify-end gap-2">
                            <h3 className="text-lg font-bold">{exp.company}</h3>
                            {exp.type && (
                              <Badge className={`bg-gradient-to-r ${typeColor} text-white border-0 text-xs`}>
                                {exp.type}
                              </Badge>
                            )}
                          </div>
                          <p className="mt-1 text-sm font-medium text-blue-500">{exp.role}</p>
                          <p className="mt-3 text-sm leading-relaxed text-muted-foreground md:text-right">
                            {exp.description}
                          </p>
                          {exp.achievements && exp.achievements.length > 0 && (
                            <ul className="mt-3 space-y-1.5">
                              {exp.achievements.map((item, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground md:justify-end">
                                  <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-blue-500" />
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* 时间线节点 */}
                    <div className="relative z-10 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg">
                      <Building2 className="h-5 w-5 text-white" />
                    </div>
                    
                    <div className="hidden w-1/2 md:block" />
                  </>
                ) : (
                  <>
                    <div className="hidden w-1/2 md:block" />
                    
                    {/* 时间线节点 */}
                    <div className="relative z-10 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg">
                      <Building2 className="h-5 w-5 text-white" />
                    </div>
                    
                    <div className="flex w-1/2 md:flex">
                      <div className="hidden flex-1 flex-col items-start gap-2 md:flex">
                        <div className="rounded-2xl border bg-card/80 p-5 backdrop-blur-sm card-hover">
                          <div className="flex items-center gap-2">
                            <h3 className="text-lg font-bold">{exp.company}</h3>
                            {exp.type && (
                              <Badge className={`bg-gradient-to-r ${typeColor} text-white border-0 text-xs`}>
                                {exp.type}
                              </Badge>
                            )}
                          </div>
                          <p className="mt-1 text-sm font-medium text-blue-500">{exp.role}</p>
                          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                            {exp.description}
                          </p>
                          {exp.achievements && exp.achievements.length > 0 && (
                            <ul className="mt-3 space-y-1.5">
                              {exp.achievements.map((item, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                                  <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-blue-500" />
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* 时间显示 - 居中显示在节点上方 */}
                <div className="absolute left-1/2 top-0 z-20 -translate-x-1/2 -translate-y-3 md:static md:left-auto md:translate-x-0 md:translate-y-0">
                  <div className="rounded-full bg-gradient-to-r from-blue-500/20 to-cyan-500/20 px-4 py-2 text-sm font-medium backdrop-blur-sm border border-blue-500/30 whitespace-nowrap shadow-lg">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-blue-500" />
                      {exp.period}
                    </div>
                  </div>
                </div>

                {/* 移动端内容 */}
                <div className="mt-4 w-full md:hidden">
                  <div className="rounded-2xl border bg-card/80 p-5 backdrop-blur-sm">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-bold">{exp.company}</h3>
                      {exp.type && (
                        <Badge className={`bg-gradient-to-r ${typeColor} text-white border-0 text-xs`}>
                          {exp.type}
                        </Badge>
                      )}
                    </div>
                    <p className="mt-1 text-sm font-medium text-blue-500">{exp.role}</p>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {exp.description}
                    </p>
                    {exp.achievements && exp.achievements.length > 0 && (
                      <ul className="mt-3 space-y-1.5">
                        {exp.achievements.map((item, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                            <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-blue-500" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
