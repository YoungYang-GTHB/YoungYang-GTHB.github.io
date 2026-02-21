'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trophy, Medal, Calendar, Star } from 'lucide-react';
import type { Award } from '@/types/resume';

interface Props {
  data: Award[];
}

export function AwardCard({ data }: Props) {
  const levelOrder: Record<string, number> = {
    '国家级': 0,
    '省级': 1,
    '华中赛区': 2,
    '西部赛区': 3,
  };

  const sortedAwards = [...data].sort((a, b) => {
    const aLevel = Object.keys(levelOrder).find(level => a.level.includes(level)) || '';
    const bLevel = Object.keys(levelOrder).find(level => b.level.includes(level)) || '';
    return (levelOrder[aLevel] ?? 99) - (levelOrder[bLevel] ?? 99);
  });

  const medalColors = {
    '省级二等奖': 'from-slate-400 to-slate-600',
    '华中赛区一等奖': 'from-amber-400 to-yellow-600',
    '西部赛区二等奖': 'from-orange-400 to-orange-600',
  };

  return (
    <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-amber-500/5 shadow-xl">
      <CardHeader className="border-b bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 pb-6">
        <CardTitle className="flex items-center gap-3 text-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 shadow-lg">
            <Trophy className="h-6 w-6 text-white" />
          </div>
          <span className="text-gradient" style={{ backgroundImage: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>荣誉奖项</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sortedAwards.map((award, index) => {
            const medalColor = medalColors[award.level as keyof typeof medalColors] || 'from-yellow-500 to-orange-500';
            
            return (
              <motion.div
                key={award.name}
                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                whileInView={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ delay: index * 0.1, duration: 0.4 }}
                viewport={{ once: true }}
                className="group relative"
              >
                <div className="relative h-full overflow-hidden rounded-2xl border bg-card/50 p-5 backdrop-blur-sm transition-all card-hover">
                  {/* 光晕效果 */}
                  <div className="absolute -right-10 -top-10 h-24 w-24 rounded-full bg-gradient-to-br from-amber-500/20 to-orange-500/20 blur-2xl transition-opacity group-hover:opacity-70" />
                  
                  {/* 奖牌图标 */}
                  <div className={`absolute -right-4 -top-4 h-20 w-20 rounded-full bg-gradient-to-br ${medalColor} opacity-10 blur-xl`} />
                  
                  <div className="relative">
                    {/* 奖牌徽章 */}
                    <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br ${medalColor} shadow-lg`}>
                      <Medal className="h-6 w-6 text-white" />
                    </div>
                    
                    {/* 奖项名称 */}
                    <h3 className="font-bold leading-tight">{award.name}</h3>
                    
                    {/* 奖项等级 */}
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <Badge className={`bg-gradient-to-r ${medalColor} text-white border-0`}>
                        <Star className="mr-1 h-3 w-3" />
                        {award.level}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        个人排名：{award.rank}
                      </span>
                    </div>
                    
                    {/* 年份 */}
                    <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {award.year}
                    </div>
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
