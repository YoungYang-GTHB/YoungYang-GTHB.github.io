'use client';

import { useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ZoomIn, ZoomOut, Maximize, Minimize } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

interface ImageLightboxProps {
  src: string;
  alt: string;
  onClose: () => void;
}

export function ImageLightbox({ src, alt, onClose }: ImageLightboxProps) {
  const [scale, setScale] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 关闭弹窗
  const handleClose = useCallback(() => {
    setScale(1);
    setIsFullscreen(false);
    onClose();
  }, [onClose]);

  // 键盘事件
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
      if (e.key === '+' || e.key === '=') setScale((prev) => Math.min(prev + 0.25, 3));
      if (e.key === '-') setScale((prev) => Math.max(prev - 0.25, 0.5));
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleClose]);

  // 阻止滚动
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, []);

  const handleZoomIn = () => setScale((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setScale((prev) => Math.max(prev - 0.25, 0.5));
  const handleReset = () => setScale(1);
  const handleFullscreen = () => setIsFullscreen(!isFullscreen);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
        onClick={handleClose}
      >
        {/* 工具栏 */}
        <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            className="h-10 w-10 rounded-full bg-white/10 text-white border-white/20 hover:bg-white/20"
            onClick={(e) => { e.stopPropagation(); handleZoomIn(); }}
            title="放大 (+)"
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-10 w-10 rounded-full bg-white/10 text-white border-white/20 hover:bg-white/20"
            onClick={(e) => { e.stopPropagation(); handleZoomOut(); }}
            title="缩小 (-)"
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-10 w-10 rounded-full bg-white/10 text-white border-white/20 hover:bg-white/20"
            onClick={(e) => { e.stopPropagation(); handleReset(); }}
            title="重置 (100%)"
          >
            <Maximize className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-10 w-10 rounded-full bg-white/10 text-white border-white/20 hover:bg-white/20"
            onClick={(e) => { e.stopPropagation(); handleFullscreen(); }}
            title={isFullscreen ? '退出全屏' : '全屏'}
          >
            {isFullscreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-10 w-10 rounded-full bg-white/10 text-white border-white/20 hover:bg-red-500/50"
            onClick={(e) => { e.stopPropagation(); handleClose(); }}
            title="关闭 (Esc)"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* 缩放信息 */}
        <div className="absolute bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-full bg-white/10 px-4 py-2 text-sm text-white/80 backdrop-blur-sm">
          {Math.round(scale * 100)}% · {alt}
        </div>

        {/* 图片容器 */}
        <motion.div
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          exit={{ scale: 0.9 }}
          className="relative h-full w-full p-4 md:p-8"
          onClick={(e) => e.stopPropagation()}
        >
          <div className={`flex h-full w-full items-center justify-center ${isFullscreen ? '' : ''}`}>
            <motion.img
              src={src}
              alt={alt}
              className="h-auto w-auto max-h-full max-w-full object-contain"
              style={{ 
                scale,
                cursor: scale > 1 ? 'grab' : 'default',
              }}
              drag={scale > 1}
              dragMomentum={false}
            />
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
