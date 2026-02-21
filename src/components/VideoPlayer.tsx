'use client';

import { useState, useRef } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface VideoPlayerProps {
  src: string;
  poster?: string;
  title?: string;
}

export function VideoPlayer({ src, poster, title }: VideoPlayerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handlePlay = () => {
    setHasStarted(true);
    setIsPlaying(true);
    if (videoRef.current) {
      videoRef.current.play();
    }
  };

  const handleLoadedData = () => {
    setIsLoading(false);
  };

  const handleWaiting = () => {
    setIsLoading(true);
  };

  return (
    <div className="relative aspect-video overflow-hidden rounded-lg bg-black group">
      {/* 视频元素 */}
      {hasStarted ? (
        <video
          ref={videoRef}
          src={src}
          controls
          className="h-full w-full"
          poster={poster}
          onLoadedData={handleLoadedData}
          onWaiting={handleWaiting}
          onPlaying={() => setIsLoading(false)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />
      ) : (
        <>
          {/* 封面图 */}
          {poster && (
            <img
              src={poster}
              alt={title || '视频封面'}
              className="h-full w-full object-cover opacity-60"
            />
          )}
          
          {/* 播放按钮 */}
          <div className="absolute inset-0 flex items-center justify-center">
            <Button
              size="lg"
              className="h-16 w-16 rounded-full bg-primary/90 hover:bg-primary transition-all group-hover:scale-110"
              onClick={handlePlay}
            >
              <Play className="h-8 w-8 fill-current" />
            </Button>
          </div>
          
          {/* 视频信息 */}
          {title && (
            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
              <p className="text-white text-sm font-medium">{title}</p>
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
