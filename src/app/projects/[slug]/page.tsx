import { getResumeData } from '@/lib/resume';
import { notFound } from 'next/navigation';
import { ArrowLeft, Calendar, User, Award, ExternalLink, FileText, Play, ZoomIn } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VideoPlayer } from '@/components/VideoPlayer';
import { ProjectDetailClient } from './ProjectDetailClient';

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  const resumeData = getResumeData();
  return resumeData.projects.map((project) => ({
    slug: project.slug,
  }));
}

export default async function ProjectDetailPage({ params }: Props) {
  const { slug } = await params;
  const resumeData = getResumeData();
  const project = resumeData.projects.find((p) => p.slug === slug);

  if (!project) {
    notFound();
  }

  return <ProjectDetailClient project={project} />;
}
