'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Play, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface VideoPlayerProps {
  src: string;
  poster?: string;
  title?: string;
  className?: string;
}

export function VideoPlayer({ src, poster, title, className = '' }: VideoPlayerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasStarted, setHasStarted] = useState(false);

  const handlePlay = () => {
    setHasStarted(true);
  };

  const handleLoadedData = () => {
    setIsLoading(false);
  };

  const handleWaiting = () => {
    setIsLoading(true);
  };

  return (
    <div
      className={`group relative aspect-video overflow-hidden rounded-lg bg-gradient-to-br from-slate-950 via-slate-900 to-primary/30 ${className}`}
    >
      {/* 视频元素 */}
      {hasStarted ? (
        <video
          src={src}
          controls
          autoPlay
          playsInline
          preload="metadata"
          aria-label={title || '项目演示视频'}
          className="h-full w-full object-contain"
          poster={poster}
          onLoadedData={handleLoadedData}
          onWaiting={handleWaiting}
          onPlaying={() => setIsLoading(false)}
        />
      ) : (
        <>
          {/* 封面图 */}
          {poster && (
            <Image
              src={poster}
              alt={title || '视频封面'}
              fill
              sizes="(min-width: 1024px) 60vw, 100vw"
              className="h-full w-full object-cover opacity-60"
            />
          )}
          
          {/* 播放按钮 */}
          <div className="absolute inset-0 flex items-center justify-center">
            <Button
              size="lg"
              type="button"
              aria-label={`播放${title || '项目演示视频'}`}
              className="h-16 w-16 rounded-full bg-primary/90 transition-all hover:bg-primary group-hover:scale-110"
              onClick={handlePlay}
            >
              <Play className="h-8 w-8 fill-current" />
            </Button>
          </div>
          
          {/* 视频信息 */}
          {title && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
              <p className="text-sm font-medium text-white">{title}</p>
            </div>
          )}
        </>
      )}

      {/* 加载指示器 */}
      {isLoading && hasStarted && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <Loader2 className="h-8 w-8 animate-spin text-white" />
        </div>
      )}
    </div>
  );
}
