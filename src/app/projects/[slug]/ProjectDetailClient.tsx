'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Calendar, User, Award, ExternalLink, FileText, ZoomIn } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VideoPlayer } from '@/components/VideoPlayer';
import { ImageLightbox } from '@/components/ImageLightbox';
import type { Project } from '@/types/resume';

interface Props {
  project: Project;
}

export function ProjectDetailClient({ project }: Props) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  // 可点击的图片组件
  const ClickableImage = ({ src, alt }: { src: string; alt: string }) => (
    <div
      className="group relative cursor-pointer overflow-hidden rounded-lg bg-secondary"
      onClick={() => setSelectedImage(src)}
    >
      <div className="aspect-video overflow-hidden">
        <img
          src={src}
          alt={alt}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
      </div>
      {/* 放大提示 */}
      <div className="absolute inset-0 flex items-center justify-center bg-black/0 opacity-0 transition-all group-hover:bg-black/30 group-hover:opacity-100">
        <div className="flex items-center gap-2 rounded-full bg-white/90 px-4 py-2 text-sm font-medium text-foreground shadow-lg">
          <ZoomIn className="h-4 w-4" />
          点击查看大图
        </div>
      </div>
    </div>
  );

  return (
    <div className="relative min-h-screen bg-background">
      {/* 动态背景装饰 */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -left-1/4 top-1/4 h-[500px] w-[500px] animate-pulse rounded-full bg-gradient-to-br from-primary/20 to-accent/20 blur-3xl" style={{ animationDuration: '4s' }} />
        <div className="absolute -right-1/4 bottom-1/4 h-[500px] w-[500px] animate-pulse rounded-full bg-gradient-to-tl from-cyan-500/15 to-blue-500/15 blur-3xl" style={{ animationDuration: '5s', animationDelay: '1s' }} />
      </div>

      {/* 顶部导航 */}
      <nav className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-xl">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-primary">
            <ArrowLeft className="h-4 w-4" />
            返回主页
          </Link>
          <span className="text-sm font-semibold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            {project.title}
          </span>
          <div className="w-20" />
        </div>
      </nav>

      {/* 主要内容 */}
      <main className="container mx-auto px-4 py-8 md:py-12">
        <div className="mx-auto max-w-5xl space-y-8">
          {/* 项目标题卡片 */}
          <Card className="overflow-hidden border-0 bg-gradient-to-br from-card via-card to-primary/5 shadow-xl">
            <CardHeader className="border-b bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 pb-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <CardTitle className="text-3xl font-bold">{project.title}</CardTitle>
                {project.level && (
                  <Badge className="w-fit bg-gradient-to-r from-primary to-accent text-white border-0 px-4 py-2">
                    <Award className="mr-2 h-4 w-4" />
                    {project.level}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Calendar className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">项目时间</p>
                    <p className="font-medium">{project.period}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <User className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">担任角色</p>
                    <p className="font-medium">{project.role}</p>
                  </div>
                </div>
              </div>

              <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
                {project.description}
              </p>
            </CardContent>
          </Card>

          {/* 技术栈 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">技术栈</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {project.technologies.map((tech) => (
                  <Badge key={tech} variant="secondary" className="px-3 py-1.5 text-sm">
                    {tech}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 项目成就 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">主要成就</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {project.achievements.map((achievement, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <div className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-primary" />
                    <span className="text-muted-foreground">{achievement}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* 相关资料 - 使用 Tabs 组织 */}
          {project.detail && (project.detail.generations || project.detail.images || project.detail.videos || project.detail.documents || project.detail.patents) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">相关资料</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="images" className="w-full">
                  <TabsList className="grid w-full grid-cols-3 md:w-fit md:grid-cols-4">
                    {project.detail?.generations && (
                      <TabsTrigger value="generations">产品代际</TabsTrigger>
                    )}
                    <TabsTrigger value="images">图片</TabsTrigger>
                    <TabsTrigger value="videos">视频</TabsTrigger>
                    <TabsTrigger value="docs">文档</TabsTrigger>
                  </TabsList>

                  {/* 产品代际 */}
                  {project.detail?.generations && (
                    <TabsContent value="generations" className="space-y-6">
                      {project.detail.generations.map((gen, index) => (
                        <div key={gen.slug} className="space-y-4">
                          <h3 className="text-lg font-bold">{gen.name}</h3>

                          {/* 图片网格 */}
                          {gen.images && gen.images.length > 0 && (
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                              {gen.images.map((img, i) => (
                                <ClickableImage
                                  key={i}
                                  src={img}
                                  alt={`${gen.name} - 图片 ${i + 1}`}
                                />
                              ))}
                            </div>
                          )}

                          {/* 视频播放器 */}
                          {gen.videos && gen.videos.length > 0 && (
                            <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
                              {gen.videos.map((video, i) => (
                                <VideoPlayer
                                  key={i}
                                  src={video}
                                  title={`视频 ${i + 1}`}
                                />
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </TabsContent>
                  )}

                  {/* 图片 */}
                  {project.detail?.images && project.detail.images.length > 0 && (
                    <TabsContent value="images">
                      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {project.detail.images.map((img, i) => (
                          <ClickableImage
                            key={i}
                            src={img}
                            alt={`图片 ${i + 1}`}
                          />
                        ))}
                      </div>
                    </TabsContent>
                  )}

                  {/* 视频 */}
                  {project.detail?.videos && project.detail.videos.length > 0 && (
                    <TabsContent value="videos">
                      <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
                        {project.detail.videos.map((video, i) => (
                          <VideoPlayer
                            key={i}
                            src={video}
                            title={`视频 ${i + 1}`}
                          />
                        ))}
                      </div>
                    </TabsContent>
                  )}

                  {/* 文档 */}
                  {(project.detail?.documents || project.detail?.patents) && (
                    <TabsContent value="docs">
                      <div className="space-y-4">
                        {/* 文档 */}
                        {project.detail?.documents && project.detail.documents.length > 0 && (
                          <div>
                            <h3 className="mb-3 flex items-center gap-2 font-semibold">
                              <FileText className="h-5 w-5 text-primary" />
                              文档资料
                            </h3>
                            <div className="space-y-2">
                              {project.detail.documents.map((doc, i) => (
                                <a
                                  key={i}
                                  href={doc.url}
                                  className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-secondary"
                                >
                                  <div className="flex items-center gap-3">
                                    <FileText className="h-5 w-5 text-primary" />
                                    <span className="font-medium">{doc.name}</span>
                                  </div>
                                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                                </a>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* 专利 */}
                        {project.detail?.patents && project.detail.patents.length > 0 && (
                          <div>
                            <h3 className="mb-3 flex items-center gap-2 font-semibold">
                              <Award className="h-5 w-5 text-primary" />
                              相关专利
                            </h3>
                            <div className="space-y-2">
                              {project.detail.patents.map((patent, i) => (
                                <a
                                  key={i}
                                  href={patent.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-secondary"
                                >
                                  <div className="flex items-center gap-3">
                                    <Award className="h-5 w-5 text-primary" />
                                    <span className="font-medium">{patent.name}</span>
                                  </div>
                                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  )}
                </Tabs>
              </CardContent>
            </Card>
          )}

          {/* 返回按钮 */}
          <div className="flex justify-center pt-8">
            <Button asChild size="lg" className="gap-2">
              <Link href="/">
                <ArrowLeft className="h-4 w-4" />
                返回主页
              </Link>
            </Button>
          </div>
        </div>
      </main>

      {/* 图片放大弹窗 */}
      {selectedImage && (
        <ImageLightbox
          src={selectedImage}
          alt="查看大图"
          onClose={() => setSelectedImage(null)}
        />
      )}
    </div>
  );
}
