'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Education } from '@/types/resume';
import { GraduationCap, Calendar, Award, BookOpen, TrendingUp } from 'lucide-react';

interface Props {
  data: Education[];
}

export function EducationCard({ data }: Props) {
  return (
    <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-cyan-500/5 shadow-xl">
      <CardHeader className="border-b bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-cyan-500/10 pb-6">
        <CardTitle className="flex items-center gap-3 text-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 shadow-lg">
            <GraduationCap className="h-6 w-6 text-white" />
          </div>
          <span className="text-gradient" style={{ backgroundImage: 'var(--gradient-cyan)' }}>教育背景</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-6">
          {data.map((edu, index) => (
            <motion.div
              key={edu.school}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              viewport={{ once: true }}
              className="group relative"
            >
              <div className="relative flex flex-col gap-4 overflow-hidden rounded-2xl border bg-card/50 p-6 backdrop-blur-sm transition-all card-hover md:flex-row md:gap-6">
                {/* 左侧渐变装饰条 */}
                <div className="absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-cyan-500 to-blue-500 transition-all group-hover:w-1.5" />
                
                {/* 背景光晕 */}
                <div className="absolute -right-20 -top-20 h-40 w-40 rounded-full bg-gradient-to-br from-cyan-500/10 to-blue-500/10 blur-3xl transition-opacity group-hover:opacity-70" />
                
                {/* 图标 - 移动端顶部居中，桌面端左侧 */}
                <div className="relative z-10 flex-shrink-0">
                  <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 shadow-lg transition-transform group-hover:scale-110">
                    <GraduationCap className="h-8 w-8 text-white" />
                  </div>
                </div>
                
                {/* 内容区域 */}
                <div className="relative z-10 flex flex-1 flex-col gap-3">
                  {/* 学校名称和标签 */}
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="text-xl font-bold">{edu.school}</h3>
                    <div className="flex gap-2">
                      {edu.tags?.map((tag) => (
                        <Badge 
                          key={tag} 
                          className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white border-0"
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  {/* 专业和研究方向 */}
                  <div className="flex flex-wrap gap-4 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <BookOpen className="h-4 w-4 text-cyan-500" />
                      {edu.degree} · {edu.major}
                    </div>
                    {edu.direction && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <TrendingUp className="h-4 w-4 text-cyan-500" />
                        {edu.direction}
                      </div>
                    )}
                  </div>
                  
                  {/* 成绩和排名 */}
                  <div className="flex flex-wrap gap-3">
                    {edu.gpa && (
                      <Badge variant="secondary" className="gap-1 shadow-sm">
                        <Award className="h-3 w-3" />
                        {edu.gpa}
                      </Badge>
                    )}
                    {edu.rank && (
                      <Badge variant="secondary" className="gap-1 shadow-sm">
                        <TrendingUp className="h-3 w-3" />
                        {edu.rank}
                      </Badge>
                    )}
                    <div className="flex items-center gap-2 rounded-full bg-cyan-500/10 px-4 py-1.5 text-sm font-medium border border-cyan-500/20">
                      <Calendar className="h-4 w-4 text-cyan-500" />
                      {edu.period}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
