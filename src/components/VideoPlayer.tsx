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
  showCaption?: boolean;
}

export function VideoPlayer({
  src,
  poster,
  title,
  className = '',
  showCaption = true,
}: VideoPlayerProps) {
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
      className={`group relative aspect-video overflow-hidden rounded-lg bg-black ${className}`}
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
              className="h-full w-full object-cover opacity-85 transition-transform duration-700 group-hover:scale-[1.01]"
            />
          )}
          
          {/* 播放按钮 */}
          <div className="absolute inset-0 flex items-center justify-center">
            <Button
              size="lg"
              type="button"
              aria-label={`播放${title || '项目演示视频'}`}
              className="h-16 w-16 rounded-none border border-white/35 bg-signal text-[#071419] shadow-[0_10px_40px_rgba(0,0,0,0.35)] transition-transform hover:bg-[#5eead4] group-hover:scale-105"
              onClick={handlePlay}
            >
              <Play className="h-8 w-8 fill-current" />
            </Button>
          </div>
          
          {/* 视频信息 */}
          {title && showCaption && (
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
