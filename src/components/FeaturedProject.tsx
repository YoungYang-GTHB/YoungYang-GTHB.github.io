'use client';

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import {
  Rocket,
  Database,
  Brain,
  LineChart,
  Gauge,
  Bot,
  ChevronRight,
  ExternalLink,
  Sparkles,
  CalendarDays,
  Cpu,
  ScanEye,
  Workflow,
} from 'lucide-react';
import type { Featured } from '@/types/resume';
import { VideoPlayer } from '@/components/VideoPlayer';

interface Props {
  data: Featured;
}

// 全链路 pipeline 示意（自制，通用示意图，不含任何内部真实数据/画面）
const pipeline = [
  { icon: Database, label: '数据采集 · 遥操作', sub: 'DAgger / 双臂遥操' },
  { icon: Brain, label: 'VLA 策略训练', sub: 'π0.5 · JAX / PyTorch' },
  { icon: LineChart, label: '离线评测 · AWBC', sub: 'advantage 加权' },
  { icon: Gauge, label: '实时推理优化', sub: 'RTC · Triton' },
  { icon: Bot, label: '真机部署', sub: 'ROS2 · 双臂 Piper' },
];

export function FeaturedProject({ data }: Props) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      viewport={{ once: true }}
      className="relative overflow-hidden rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/10 via-card to-accent/10 shadow-2xl"
    >
      {/* 光晕装饰 */}
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-accent/20 blur-3xl" />

      <div className="relative p-6 md:p-9">
        {/* 旗舰标签 */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-accent px-4 py-1.5 text-sm font-semibold text-white shadow-lg">
            <Rocket className="h-4 w-4" />
            旗舰主项目
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/5 px-3 py-1 text-xs text-muted-foreground">
            <CalendarDays className="h-3.5 w-3.5 text-primary" />
            {data.period}
          </span>
        </div>

        {/* 标题 / 机构 / 角色 */}
        <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
          <span className="text-gradient text-gradient-primary">{data.title}</span>
        </h2>
        <p className="mt-2 text-sm font-medium text-primary/90 md:text-base">
          {data.org} · {data.role}
        </p>
        {data.tagline && (
          <p className="mt-1 text-sm text-muted-foreground">{data.tagline}</p>
        )}

        {/* 项目简介 */}
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted-foreground md:text-base">
          {data.summary}
        </p>

        {/* 真机演示：媒体存在时才由数据层启用 */}
        {data.demo && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08, duration: 0.45 }}
            viewport={{ once: true }}
            className="mt-7 grid overflow-hidden rounded-2xl border border-primary/20 bg-slate-950/[0.04] shadow-xl lg:grid-cols-[minmax(0,1.55fr)_minmax(17rem,0.8fr)] dark:bg-white/[0.04]"
          >
            <div className="bg-slate-950 p-2 md:p-3">
              <VideoPlayer
                src={data.demo.src}
                poster={data.demo.poster}
                title={data.demo.title}
                className="rounded-xl"
              />
            </div>

            <div className="flex flex-col justify-center p-5 md:p-6">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold tracking-[0.14em] text-emerald-700 dark:text-emerald-300">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                {data.demo.eyebrow || 'REAL-ROBOT DEMO'}
              </div>
              <h3 className="mt-4 text-xl font-bold tracking-tight md:text-2xl">
                {data.demo.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {data.demo.description}
              </p>

              <div className="mt-5 space-y-3 text-sm">
                {data.demo.model && (
                  <div className="flex items-start gap-3">
                    <Cpu className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <div>
                      <div className="text-xs text-muted-foreground">策略模型</div>
                      <div className="font-medium">{data.demo.model}</div>
                    </div>
                  </div>
                )}
                {data.demo.task && (
                  <div className="flex items-start gap-3">
                    <ScanEye className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <div>
                      <div className="text-xs text-muted-foreground">任务</div>
                      <div className="font-medium">{data.demo.task}</div>
                    </div>
                  </div>
                )}
                {data.demo.platform && (
                  <div className="flex items-start gap-3">
                    <Workflow className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <div>
                      <div className="text-xs text-muted-foreground">真机平台</div>
                      <div className="font-medium">{data.demo.platform}</div>
                    </div>
                  </div>
                )}
              </div>

              {data.demo.note && (
                <p className="mt-5 border-t border-primary/10 pt-4 text-xs leading-relaxed text-muted-foreground">
                  {data.demo.note}
                </p>
              )}
            </div>
          </motion.div>
        )}

        {/* 全链路 pipeline 示意图 */}
        <div className="mt-7">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Sparkles className="h-4 w-4 text-primary" />
            全链路方案（数据 → 训练 → 评测 → 实时推理 → 真机）
          </div>
          <div className="overflow-x-auto pb-2">
            <div className="flex min-w-max items-stretch gap-2 md:gap-3">
              {pipeline.map((stage, i) => {
                const Icon = stage.icon;
                return (
                  <div key={stage.label} className="flex items-center gap-2 md:gap-3">
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.1 + i * 0.08, duration: 0.3 }}
                      viewport={{ once: true }}
                      className="flex w-32 flex-col items-center gap-2 rounded-2xl border bg-card/70 p-3 text-center backdrop-blur-sm md:w-36"
                    >
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-md">
                        <Icon className="h-5 w-5 text-white" />
                      </div>
                      <div className="text-xs font-semibold leading-tight md:text-sm">
                        {stage.label}
                      </div>
                      <div className="text-[11px] leading-tight text-muted-foreground">
                        {stage.sub}
                      </div>
                    </motion.div>
                    {i < pipeline.length - 1 && (
                      <ChevronRight className="h-5 w-5 flex-shrink-0 text-primary/50" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* 核心成果亮点 */}
        <div className="mt-7 grid gap-3 sm:grid-cols-2">
          {data.highlights.map((h, i) => (
            <motion.div
              key={h.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.08, duration: 0.3 }}
              viewport={{ once: true }}
              className="group rounded-2xl border bg-card/60 p-4 backdrop-blur-sm transition-all hover:border-primary/40 hover:shadow-lg"
            >
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-primary to-accent text-xs font-bold text-white">
                  {i + 1}
                </span>
                <h3 className="text-sm font-bold md:text-base">{h.title}</h3>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{h.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* 技术栈 */}
        <div className="mt-6 flex flex-wrap gap-2">
          {data.stack.map((tech) => (
            <Badge
              key={tech}
              variant="secondary"
              className="border-0 bg-gradient-to-r from-primary/15 to-accent/15 px-3 py-1 text-xs font-medium text-foreground/80"
            >
              {tech}
            </Badge>
          ))}
        </div>

        {/* 深入了解 · 公开参考项目跳转 */}
        {data.links?.length > 0 && (
          <div className="mt-7 border-t border-primary/10 pt-5">
            <div className="mb-3 text-sm font-semibold text-muted-foreground">
              深入了解技术背景（公开参考项目）
            </div>
            <div className="flex flex-wrap gap-2.5">
              {data.links.map((link) => (
                <a
                  key={link.name}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group inline-flex items-center gap-2 rounded-xl border bg-card/70 px-3.5 py-2 text-sm transition-all hover:border-primary hover:bg-primary hover:text-primary-foreground hover:shadow-md"
                >
                  <ExternalLink className="h-4 w-4 transition-transform group-hover:scale-110" />
                  <span className="font-medium">{link.name}</span>
                  {link.desc && (
                    <span className="text-xs opacity-70">· {link.desc}</span>
                  )}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.section>
  );
}
