'use client';

import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import {
  ArrowDownRight,
  Download,
  Github,
  Mail,
  MapPin,
  Phone,
} from 'lucide-react';
import type { PersonalInfo } from '@/types/resume';

interface Props {
  data: PersonalInfo;
}

export function Header({ data }: Props) {
  const heroSummary = data.summary.trim();

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.2, 0.8, 0.2, 1] }}
      className="relative border-b border-foreground/25 py-10 md:py-14 lg:py-0"
    >
      <div className={`grid lg:min-h-[34rem] ${data.photo ? 'lg:grid-cols-[minmax(0,1.25fr)_minmax(17rem,0.68fr)_minmax(12rem,0.38fr)]' : 'lg:grid-cols-[minmax(0,1fr)_18rem]'}`}>
        <div className="flex flex-col justify-center lg:pr-12 xl:pr-16">
          <h1 className="max-w-4xl font-display text-[clamp(3rem,6vw,6.4rem)] font-bold leading-[1.02] tracking-[-0.045em]">
            {data.title}
          </h1>

          <span className="mt-7 h-1 w-10 bg-signal" aria-hidden="true" />

          <p className="mt-7 max-w-2xl text-base leading-8 text-muted-foreground md:text-lg md:leading-9">
            {heroSummary}
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-x-7 gap-y-3">
            {data.resumeLinks?.length || data.photo ? (
              <Button asChild className="h-12 rounded-none px-7 text-sm shadow-none">
                <a href="#featured">
                  查看代表项目
                  <ArrowDownRight className="h-4 w-4" />
                </a>
              </Button>
            ) : null}
            {data.resumeLinks?.map((resume) => (
              <Button
                key={resume.href}
                variant="ghost"
                asChild
                className="h-12 rounded-none border-b border-primary px-1 text-primary hover:bg-transparent hover:text-signal"
              >
                <a href={resume.href} download={resume.download}>
                  {resume.primary && <Download className="h-4 w-4" />}
                  {resume.label}
                </a>
              </Button>
            ))}
          </div>
        </div>

        {data.photo && <motion.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.18, duration: 0.55 }}
          className="hidden border-l border-foreground/15 lg:block"
        >
          <div className="relative h-full overflow-hidden bg-muted">
              {/* 公开站点使用 ASCII 资源名，避免 React 预加载响应头编码问题。 */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={data.photo} alt={data.name} className="h-full w-full object-cover object-center" />
          </div>
        </motion.div>}

        <aside className="hidden border-l border-foreground/15 py-12 pl-6 lg:flex lg:flex-col lg:justify-center xl:pl-8">
          <dl className="divide-y divide-foreground/15 text-xs">
            <div className="pb-5">
              <dt className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">在读</dt>
              <dd className="mt-2 font-semibold leading-5">{data.subtitle}</dd>
            </div>
            {data.tagline && (
              <div className="py-5">
                <dt className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">研究方向</dt>
                <dd className="mt-2 leading-5">{data.tagline}</dd>
              </div>
            )}
            <div className="py-5">
              <dt className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">位置</dt>
              <dd className="mt-2 flex items-start gap-2 leading-5"><MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />{data.location}</dd>
            </div>
            <div className="py-5">
              <dt className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">联系</dt>
              <dd className="mt-2 space-y-2 leading-5">
                <a href={`mailto:${data.email}`} className="flex items-start gap-2 break-all hover:text-primary"><Mail className="mt-0.5 h-3.5 w-3.5 shrink-0" />{data.email}</a>
                <a href={`tel:${data.phone}`} className="flex items-center gap-2 hover:text-primary"><Phone className="h-3.5 w-3.5" />{data.phone}</a>
              </dd>
            </div>
          </dl>
          {data.github && <a href={data.github} target="_blank" rel="noopener noreferrer" className="mt-5 inline-flex items-center gap-2 text-xs font-semibold text-primary hover:text-signal"><Github className="h-4 w-4" />GitHub</a>}
        </aside>
      </div>
    </motion.section>
  );
}
