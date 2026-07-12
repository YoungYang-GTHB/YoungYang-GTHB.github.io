'use client';

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Mail, Phone, MapPin, Github, Linkedin, Download, Sparkles, Home, Flag, Calendar, User } from 'lucide-react';
import type { PersonalInfo } from '@/types/resume';

interface Props {
  data: PersonalInfo;
}

export function Header({ data }: Props) {
  return (
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      className="relative overflow-hidden rounded-3xl border bg-card/50 backdrop-blur-xl"
    >
      {/* 动态渐变背景 */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute -left-1/4 -top-1/4 h-[70%] w-[70%] animate-pulse rounded-full bg-gradient-to-br from-primary/40 to-accent/40 blur-3xl" />
        <div className="absolute -right-1/4 -bottom-1/4 h-[70%] w-[70%] animate-pulse rounded-full bg-gradient-to-tl from-cyan-500/30 to-blue-500/30 blur-3xl" style={{ animationDelay: '1s' }} />
      </div>

      {/* 网格装饰 */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:40px_40px]" />

      <div className="relative p-8 md:p-12 lg:p-16">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:gap-12">
          {/* 头像区域 */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="flex justify-center lg:flex-shrink-0"
          >
            <div className="relative">
              {/* 头像光晕 */}
              <div className="absolute -inset-1 rounded-full bg-gradient-to-br from-primary via-accent to-primary opacity-70 blur-lg animate-pulse" />

              {/* 头像容器 - 圆形裁剪 */}
              <div className="relative h-48 w-48 overflow-hidden rounded-full border-4 border-background shadow-2xl lg:h-56 lg:w-56">
                <img
                  src="/profile/个人照片白底.jpg"
                  alt={data.name}
                  className="h-full w-full object-cover"
                />
              </div>

              {/* 状态指示器 */}
              <div className="absolute -bottom-1 -right-1 flex h-8 w-8 items-center justify-center rounded-full border-4 border-background bg-green-500 shadow-lg">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
            </div>
          </motion.div>

          {/* 信息区域 */}
          <div className="flex-1 text-center lg:text-left">
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              <h1 className="text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
                <span className="text-gradient text-gradient-primary">{data.name}</span>
              </h1>
              
              <div className="mt-4 flex flex-col items-center gap-2 lg:flex-row lg:justify-center lg:gap-4">
                <Badge variant="secondary" className="px-4 py-2 text-base font-medium">
                  {data.title}
                </Badge>
                <span className="hidden text-muted-foreground lg:inline">•</span>
                <p className="text-lg text-muted-foreground">{data.subtitle}</p>
              </div>

              {data.tagline && (
                <p className="mt-3 text-sm font-medium tracking-wide text-primary/80 lg:text-base">
                  {data.tagline}
                </p>
              )}
            </motion.div>

            {/* 联系方式 */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.5 }}
              className="mt-6 flex flex-wrap justify-center gap-4 lg:justify-start"
            >
              <a
                href={`mailto:${data.email}`}
                className="group flex items-center gap-2 rounded-full bg-secondary/50 px-4 py-2 text-sm transition-all hover:bg-primary hover:text-primary-foreground"
              >
                <Mail className="h-4 w-4 transition-transform group-hover:scale-110" />
                {data.email}
              </a>
              <a
                href={`tel:${data.phone}`}
                className="group flex items-center gap-2 rounded-full bg-secondary/50 px-4 py-2 text-sm transition-all hover:bg-primary hover:text-primary-foreground"
              >
                <Phone className="h-4 w-4 transition-transform group-hover:scale-110" />
                {data.phone}
              </a>
              <span className="flex items-center gap-2 rounded-full bg-secondary/50 px-4 py-2 text-sm">
                <MapPin className="h-4 w-4" />
                {data.location}
              </span>
            </motion.div>

            {/* 详细信息 */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              className="mt-4 flex flex-wrap justify-center gap-3 lg:justify-start"
            >
              {data.hometown && (
                <span className="flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm border border-primary/20">
                  <Home className="h-4 w-4 text-primary" />
                  {data.hometown}
                </span>
              )}
              {data.politicalStatus && (
                <span className="flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm border border-primary/20">
                  <Flag className="h-4 w-4 text-primary" />
                  {data.politicalStatus}
                </span>
              )}
              {data.birthday && (
                <span className="flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm border border-primary/20">
                  <Calendar className="h-4 w-4 text-primary" />
                  {data.birthday}
                </span>
              )}
            </motion.div>

            {/* 社交链接和按钮 */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              className="mt-6 flex flex-wrap justify-center gap-3 lg:justify-start"
            >
              {data.github && (
                <Button
                  variant="outline"
                  size="sm"
                  asChild
                  className="group gap-2 transition-all hover:border-primary hover:bg-primary hover:text-primary-foreground hover:shadow-lg"
                >
                  <a href={data.github} target="_blank" rel="noopener noreferrer">
                    <Github className="h-4 w-4 transition-transform group-hover:scale-110" />
                    GitHub
                  </a>
                </Button>
              )}
              {data.linkedin && (
                <Button
                  variant="outline"
                  size="sm"
                  asChild
                  className="group gap-2 transition-all hover:border-primary hover:bg-primary hover:text-primary-foreground hover:shadow-lg"
                >
                  <a href={data.linkedin} target="_blank" rel="noopener noreferrer">
                    <Linkedin className="h-4 w-4 transition-transform group-hover:scale-110" />
                    LinkedIn
                  </a>
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                className="group gap-2 transition-all hover:border-primary hover:bg-primary hover:text-primary-foreground hover:shadow-lg"
              >
                <Download className="h-4 w-4 transition-transform group-hover:scale-110" />
                下载简历
              </Button>
            </motion.div>
          </div>
        </div>

        {/* 个人简介 */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="relative mx-auto mt-10 max-w-3xl"
        >
          <div className="relative overflow-hidden rounded-2xl border bg-gradient-to-br from-primary/5 via-accent/5 to-primary/5 p-6 backdrop-blur-sm">
            <div className="absolute -left-10 -top-10 h-32 w-32 rounded-full bg-primary/10 blur-2xl" />
            <div className="absolute -right-10 -bottom-10 h-32 w-32 rounded-full bg-accent/10 blur-2xl" />
            
            <p className="relative text-center text-lg leading-relaxed text-muted-foreground">
              {data.summary}
            </p>
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
}
