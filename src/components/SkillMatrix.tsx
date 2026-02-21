'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Skills } from '@/types/resume';
import { Code2, Cpu, Monitor, Wrench } from 'lucide-react';

interface Props {
  data: Skills;
}

const categoryIcons = {
  programming: Code2,
  embedded: Cpu,
  os: Monitor,
  tools: Wrench,
};

const categoryNames = {
  programming: '编程语言',
  embedded: '嵌入式开发',
  os: '操作系统',
  tools: '开发工具',
};

const categoryGradients = {
  programming: 'from-blue-500 to-cyan-500',
  embedded: 'from-purple-500 to-pink-500',
  os: 'from-orange-500 to-red-500',
  tools: 'from-green-500 to-emerald-500',
};

export function SkillMatrix({ data }: Props) {
  const categories = Object.entries(data) as Array<[keyof Skills, Skills[keyof Skills]]>;

  return (
    <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-primary/5 shadow-xl">
      <CardHeader className="border-b bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 pb-6">
        <CardTitle className="flex items-center gap-3 text-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg">
            <Code2 className="h-6 w-6 text-primary-foreground" />
          </div>
          <span className="text-gradient text-gradient-primary">专业技能</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid gap-6 md:grid-cols-2">
          {categories.map(([category, skills], index) => {
            const Icon = categoryIcons[category];
            const gradient = categoryGradients[category];
            return (
              <motion.div
                key={category}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.4 }}
                viewport={{ once: true }}
                className="group relative overflow-hidden rounded-2xl border bg-card/50 p-5 backdrop-blur-sm transition-all hover:shadow-lg card-hover"
              >
                {/* 渐变装饰条 */}
                <div className={`absolute left-0 top-0 h-full w-1 bg-gradient-to-b ${gradient}`} />
                
                {/* 角标装饰 */}
                <div className={`absolute -right-6 -top-6 h-20 w-20 rounded-full bg-gradient-to-br ${gradient} opacity-10 blur-xl transition-opacity group-hover:opacity-20`} />
                
                <div className="relative">
                  <div className="mb-4 flex items-center gap-2">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${gradient} shadow-md`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <span className="text-lg font-semibold">{categoryNames[category]}</span>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill, skillIndex) => (
                      <motion.div
                        key={skill.name}
                        initial={{ scale: 0.9, opacity: 0 }}
                        whileInView={{ scale: 1, opacity: 1 }}
                        transition={{ delay: index * 0.1 + skillIndex * 0.05, duration: 0.2 }}
                        viewport={{ once: true }}
                      >
                        <Badge
                          variant="secondary"
                          className={`cursor-default px-3 py-2 text-sm transition-all hover:scale-105 hover:shadow-md bg-gradient-to-r ${gradient} text-white border-0`}
                          title={skill.description}
                        >
                          <span className="font-medium">{skill.name}</span>
                          <span className="ml-1.5 opacity-80">·</span>
                          <span className="ml-1.5 opacity-90">{skill.level}</span>
                        </Badge>
                      </motion.div>
                    ))}
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
