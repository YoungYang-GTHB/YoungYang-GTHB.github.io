'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Patent } from '@/types/resume';
import { FileText, Lightbulb, Award } from 'lucide-react';

interface Props {
  data: Patent[];
}

const categoryIcons = {
  '发明专利': FileText,
  '实用新型': Lightbulb,
  '软著': Award,
};

const categoryGradients = {
  '发明专利': 'from-purple-500 to-indigo-500',
  '实用新型': 'from-orange-500 to-amber-500',
  '软著': 'from-cyan-500 to-blue-500',
};

export function PatentCard({ data }: Props) {
  return (
    <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-purple-500/5 shadow-xl">
      <CardHeader className="border-b bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-purple-500/10 pb-6">
        <CardTitle className="flex items-center gap-3 text-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-indigo-500 shadow-lg">
            <FileText className="h-6 w-6 text-white" />
          </div>
          <span className="text-gradient" style={{ backgroundImage: 'var(--gradient-primary)' }}>专利成果</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid gap-4 md:grid-cols-3">
          {data.map((patent, index) => {
            const Icon = categoryIcons[patent.category as keyof typeof categoryIcons] || FileText;
            const gradient = categoryGradients[patent.category as keyof typeof categoryGradients] || 'from-purple-500 to-indigo-500';
            
            return (
              <motion.div
                key={patent.name}
                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                whileInView={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ delay: index * 0.1, duration: 0.4 }}
                viewport={{ once: true }}
                className="group relative"
              >
                <div className="relative h-full overflow-hidden rounded-2xl border bg-card/50 p-6 backdrop-blur-sm transition-all card-hover">
                  {/* 背景光晕 */}
                  <div className={`absolute -right-10 -top-10 h-24 w-24 rounded-full bg-gradient-to-br ${gradient} opacity-10 blur-2xl transition-opacity group-hover:opacity-20`} />
                  
                  <div className="relative">
                    {/* 图标 */}
                    <div className={`mb-4 inline-flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
                      <Icon className="h-7 w-7 text-white" />
                    </div>
                    
                    {/* 专利名称 */}
                    <h3 className="text-lg font-bold">{patent.name}</h3>
                    
                    {/* 数量 */}
                    <div className="mt-3 flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-gradient bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                        {patent.count}
                      </span>
                      <span className="text-sm text-muted-foreground">项</span>
                    </div>
                    
                    {/* 排名信息 */}
                    {patent.ranks && patent.ranks.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-1.5">
                        {patent.ranks.map((rank, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            排名：{rank}
                          </Badge>
                        ))}
                      </div>
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
