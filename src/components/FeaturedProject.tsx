'use client';

import { motion } from 'framer-motion';
import {
  ArrowUpRight,
  Bot,
  Brain,
  CalendarDays,
  Cpu,
  Database,
  Gauge,
  LineChart,
  ScanEye,
  Workflow,
} from 'lucide-react';
import type { Featured } from '@/types/resume';
import { VideoPlayer } from '@/components/VideoPlayer';

interface Props {
  data: Featured;
}

const pipeline = [
  { icon: Database, label: '数据采集', sub: 'DAgger / 双臂遥操' },
  { icon: Brain, label: '策略训练', sub: 'π0.5 · JAX / PyTorch' },
  { icon: LineChart, label: '离线评测', sub: 'AWBC · advantage' },
  { icon: Gauge, label: '实时推理', sub: 'RTC · Triton' },
  { icon: Bot, label: '真机部署', sub: 'ROS2 · Piper' },
];

export function FeaturedProject({ data }: Props) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.65, ease: [0.2, 0.8, 0.2, 1] }}
      viewport={{ once: true, margin: '-60px' }}
      className="relative overflow-hidden bg-[#14211e] text-[#f7f3e8] shadow-[0_28px_80px_rgba(20,33,30,0.2)]"
    >
      <div className="absolute inset-0 bg-[linear-gradient(rgba(242,245,240,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(242,245,240,0.035)_1px,transparent_1px)] bg-[size:44px_44px]" />

      <div className="relative p-4 sm:p-6 md:p-9 lg:p-11">
        <header className="flex flex-col gap-6 border-b border-white/15 pb-7 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3 font-mono text-[10px] tracking-[0.17em] text-white/55">
              <span className="bg-signal px-2 py-1 font-bold text-[#071419]">FIELD NOTE / 01</span>
              <span>FLAGSHIP REAL-ROBOT SYSTEM</span>
            </div>
            <h2 className="mt-5 max-w-4xl font-display text-3xl font-bold leading-tight tracking-[-0.035em] sm:text-4xl lg:text-5xl">
              {data.title}
            </h2>
            <p className="mt-3 text-sm text-white/62 md:text-base">
              {data.org} · {data.role}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2 font-mono text-[10px] tracking-[0.12em] text-white/55">
            <CalendarDays className="h-4 w-4 text-signal" />
            {data.period}
          </div>
        </header>

        {data.demo && (
          <div className="mt-7">
            <div className="flex items-center justify-between border-x border-t border-white/15 bg-black/25 px-3 py-2 font-mono text-[9px] tracking-[0.14em] text-white/55 md:px-4">
              <span className="flex items-center gap-2 text-signal">
                <span className="h-1.5 w-1.5 animate-pulse bg-signal" />
                REAL ROBOT / VERIFIED
              </span>
              <span className="hidden sm:inline">TASK: GARMENT FOLDING · 00:48 · RGB</span>
            </div>
            <div className="relative border border-white/15 bg-black p-1.5 md:p-2.5">
              <VideoPlayer
                src={data.demo.src}
                poster={data.demo.poster}
                title={data.demo.title}
                showCaption={false}
                className="rounded-none"
              />
              <span className="pointer-events-none absolute left-4 top-4 h-7 w-7 border-l-2 border-t-2 border-signal" />
              <span className="pointer-events-none absolute right-4 top-4 h-7 w-7 border-r-2 border-t-2 border-signal" />
              <span className="pointer-events-none absolute bottom-4 left-4 h-7 w-7 border-b-2 border-l-2 border-signal" />
              <span className="pointer-events-none absolute bottom-4 right-4 h-7 w-7 border-b-2 border-r-2 border-signal" />
            </div>
          </div>
        )}

        <div className="grid border-x border-b border-white/15 lg:grid-cols-[minmax(0,1.45fr)_minmax(17rem,0.55fr)]">
          <div className="p-5 md:p-7 lg:border-r lg:border-white/15">
            <div className="font-mono text-[9px] tracking-[0.16em] text-white/45">PROJECT THESIS</div>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-white/72 md:text-base md:leading-8">
              {data.summary}
            </p>
            {data.tagline && (
              <p className="mt-4 border-l-2 border-signal pl-4 text-sm font-semibold text-white/90">
                {data.tagline}
              </p>
            )}
          </div>

          {data.demo && (
            <dl className="grid grid-cols-1 divide-y divide-white/10 p-5 md:grid-cols-3 md:divide-x md:divide-y-0 lg:grid-cols-1 lg:divide-x-0 lg:divide-y lg:p-7">
              {[
                { icon: Cpu, label: '策略模型', value: data.demo.model },
                { icon: ScanEye, label: '任务', value: data.demo.task },
                { icon: Workflow, label: '真机平台', value: data.demo.platform },
              ].map(({ icon: Icon, label, value }) =>
                value ? (
                  <div key={label} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0 md:px-4 md:first:pl-0 md:last:pr-0 lg:px-0">
                    <Icon className="mt-0.5 h-4 w-4 shrink-0 text-signal" />
                    <div>
                      <dt className="font-mono text-[9px] tracking-[0.12em] text-white/42">{label}</dt>
                      <dd className="mt-1 text-sm font-semibold text-white/88">{value}</dd>
                    </div>
                  </div>
                ) : null
              )}
            </dl>
          )}
        </div>

        <div className="mt-10">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div className="font-mono text-[9px] tracking-[0.16em] text-white/42">SYSTEM PATH</div>
              <h3 className="mt-1 text-sm font-semibold">从数据到真机的完整闭环</h3>
            </div>
            <span className="hidden font-mono text-[9px] tracking-[0.12em] text-white/35 sm:inline">LEFT → RIGHT</span>
          </div>
          <div className="overflow-x-auto border-y border-white/15">
            <div className="grid min-w-[760px] grid-cols-5">
              {pipeline.map((stage, index) => {
                const Icon = stage.icon;
                return (
                  <div key={stage.label} className="relative border-r border-white/15 p-4 last:border-r-0 md:p-5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-signal">0{index + 1}</span>
                      <Icon className="h-4 w-4 text-white/45" />
                    </div>
                    <div className="mt-5 text-sm font-bold">{stage.label}</div>
                    <div className="mt-1 font-mono text-[9px] leading-4 text-white/42">{stage.sub}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="mt-10 grid border-y border-white/15 sm:grid-cols-2">
          {data.highlights.map((highlight, index) => (
            <div
              key={highlight.title}
              className={`p-5 md:p-6 ${index % 2 === 1 ? 'sm:border-l sm:border-white/15' : ''} ${index >= 2 ? 'border-t border-white/15' : ''}`}
            >
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-[10px] text-signal">R{String(index + 1).padStart(2, '0')}</span>
                <h3 className="font-bold">{highlight.title}</h3>
              </div>
              <p className="mt-3 text-sm leading-6 text-white/58">{highlight.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-7 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 font-mono text-[9px] tracking-[0.16em] text-white/42">TOOLCHAIN</div>
            <div className="flex flex-wrap gap-x-4 gap-y-2 font-mono text-[10px] text-white/62">
              {data.stack.map((tech) => (
                <span key={tech} className="border-b border-white/20 pb-1">{tech}</span>
              ))}
            </div>
          </div>

          {data.links?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {data.links.map((link) => (
                <a
                  key={link.name}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 border border-white/18 px-3 py-2 text-xs text-white/65 transition-colors hover:border-signal hover:text-signal"
                >
                  {link.name}
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              ))}
            </div>
          )}
        </div>

        {data.demo?.note && (
          <p className="mt-6 font-mono text-[9px] leading-5 tracking-[0.08em] text-white/35">
            DISCLOSURE / {data.demo.note}
          </p>
        )}
      </div>
    </motion.section>
  );
}
