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
      className="relative border-y border-foreground/15 py-9 md:py-12"
    >
      <div className="mb-8 flex items-center justify-between font-mono text-[10px] tracking-[0.18em] text-muted-foreground">
        <span>PROFILE / ROBOTICS ENGINEER</span>
        <span className="hidden sm:inline">{data.location}</span>
      </div>

      <div className={`grid gap-9 lg:items-start lg:gap-14 ${data.photo ? 'lg:grid-cols-[minmax(0,1fr)_14rem]' : ''}`}>
        <div>
          <div className="flex items-center gap-3 text-sm font-semibold text-primary">
            <span className="h-2 w-2 bg-signal" />
            {data.title}
          </div>

          <h1 className="mt-5 max-w-4xl text-5xl font-black leading-[0.95] tracking-[-0.055em] sm:text-6xl md:text-7xl lg:text-[5.5rem]">
            {data.name}
            <span className="mt-3 block text-[0.42em] font-semibold leading-tight tracking-[-0.025em] text-muted-foreground">
              {data.headline || data.tagline}
            </span>
          </h1>

          <p className="mt-7 max-w-3xl text-base leading-8 text-muted-foreground md:text-lg">
            {heroSummary}
          </p>

          <div className="mt-7 flex flex-wrap gap-x-5 gap-y-3 text-sm">
            <a href={`mailto:${data.email}`} className="inline-flex items-center gap-2 transition-colors hover:text-primary">
              <Mail className="h-4 w-4 text-primary" />
              {data.email}
            </a>
            <a href={`tel:${data.phone}`} className="inline-flex items-center gap-2 transition-colors hover:text-primary">
              <Phone className="h-4 w-4 text-primary" />
              {data.phone}
            </a>
            <span className="inline-flex items-center gap-2 text-muted-foreground">
              <MapPin className="h-4 w-4 text-primary" />
              {data.location}
            </span>
          </div>

          <div className="mt-8 flex flex-wrap gap-2.5">
            {data.resumeLinks?.length || data.photo ? (
              <Button asChild className="h-10 rounded-none px-5 shadow-none">
                <a href="#featured">
                  查看真机闭环
                  <ArrowDownRight className="h-4 w-4" />
                </a>
              </Button>
            ) : null}
            {data.github && (
              <Button variant="outline" asChild className="h-10 rounded-none border-foreground/20 bg-transparent px-4 shadow-none">
                <a href={data.github} target="_blank" rel="noopener noreferrer">
                  <Github className="h-4 w-4" /> GitHub
                </a>
              </Button>
            )}
            {data.resumeLinks?.map((resume) => (
              <Button
                key={resume.href}
                variant={resume.primary ? 'outline' : 'ghost'}
                asChild
                className="h-10 rounded-none px-3 text-muted-foreground"
              >
                <a href={resume.href} download={resume.download}>
                  {resume.primary && <Download className="h-4 w-4" />}
                  {resume.label}
                </a>
              </Button>
            ))}
          </div>
        </div>

        {data.photo && <motion.aside
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.18, duration: 0.55 }}
          className="hidden lg:block"
        >
          <div className="relative">
            <div className="absolute -inset-3 rounded-[1.75rem] bg-gradient-to-br from-primary/18 via-signal/12 to-transparent blur-[1px]" />
            <div className="relative overflow-hidden rounded-[1.35rem] border border-foreground/10 bg-card p-2 shadow-[0_22px_55px_rgba(40,59,92,0.16)] dark:shadow-[0_22px_55px_rgba(0,0,0,0.38)]">
              <div className="relative aspect-[4/5] overflow-hidden rounded-[1rem] bg-muted">
              {/* 公开站点使用 ASCII 资源名，避免 React 预加载响应头编码问题。 */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={data.photo}
                  alt={data.name}
                  className="h-full w-full object-cover"
                />
              </div>
            </div>
            <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-primary px-3 py-1.5 font-mono text-[9px] font-semibold tracking-[0.14em] text-primary-foreground shadow-[0_8px_22px_rgba(49,94,251,0.28)]">
              VLA · ROBOTICS
            </div>
          </div>

          <dl className="mt-7 space-y-2 border-l border-primary/30 pl-4 text-xs">
            <div>
              <dt className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">EDUCATION</dt>
              <dd className="mt-0.5 font-semibold">{data.subtitle}</dd>
            </div>
            {data.tagline && (
              <div>
                <dt className="font-mono text-[9px] tracking-[0.14em] text-muted-foreground">FOCUS</dt>
                <dd className="mt-0.5 leading-5">{data.tagline}</dd>
              </div>
            )}
          </dl>
        </motion.aside>}
      </div>
    </motion.section>
  );
}
