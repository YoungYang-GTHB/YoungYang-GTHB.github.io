'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Honor } from '@/types/resume';
import { Trophy, Star, Medal } from 'lucide-react';

interface Props {
  data: Honor[];
}

export function HonorCard({ data }: Props) {
  return (
    <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-amber-500/5 shadow-xl">
      <CardHeader className="border-b bg-gradient-to-r from-amber-500/10 via-yellow-500/10 to-amber-500/10 pb-6">
        <CardTitle className="flex items-center gap-3 text-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-yellow-500 shadow-lg">
            <Trophy className="h-6 w-6 text-white" />
          </div>
          <span className="text-gradient" style={{ backgroundImage: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>学业荣誉</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.map((honor, index) => (
            <motion.div
              key={honor.name}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ delay: index * 0.1, duration: 0.4 }}
              viewport={{ once: true }}
              className="group relative"
            >
              <div className="relative h-full overflow-hidden rounded-2xl border bg-card/50 p-5 backdrop-blur-sm transition-all card-hover">
                {/* 背景光晕 */}
                <div className="absolute -right-10 -top-10 h-24 w-24 rounded-full bg-gradient-to-br from-amber-500/20 to-yellow-500/20 blur-2xl transition-opacity group-hover:opacity-70" />
                
                <div className="relative">
                  {/* 图标 */}
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/20 to-yellow-500/20">
                    <Star className="h-6 w-6 text-amber-500" />
                  </div>
                  
                  {/* 荣誉名称 */}
                  <h3 className="font-bold leading-tight">{honor.name}</h3>
                  
                  {/* 年份 */}
                  <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
                    <Medal className="h-4 w-4 text-amber-500" />
                    {honor.year}
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
