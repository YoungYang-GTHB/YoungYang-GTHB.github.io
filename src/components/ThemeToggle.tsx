'use client';

import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEffect, useSyncExternalStore } from 'react';

type Theme = 'light' | 'dark';

const THEME_CHANGE_EVENT = 'portfolio-theme-change';

function subscribeToTheme(callback: () => void) {
  window.addEventListener(THEME_CHANGE_EVENT, callback);
  return () => window.removeEventListener(THEME_CHANGE_EVENT, callback);
}

function getThemeSnapshot(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

function getServerThemeSnapshot(): Theme {
  return 'light';
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(
    subscribeToTheme,
    getThemeSnapshot,
    getServerThemeSnapshot
  );

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', initialTheme === 'dark');
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
  };

  return (
    <Button
      variant="outline"
      size="sm"
      className="group relative h-9 w-9 overflow-hidden rounded-none border-foreground/15 text-foreground transition-all hover:border-signal hover:text-signal"
      onClick={toggleTheme}
    >
      {/* 背景渐变 */}
      <div className="absolute inset-0 bg-signal/8 opacity-0 transition-opacity group-hover:opacity-100" />
      
      {/* 图标动画 */}
      <div className="relative flex items-center justify-center">
        <Moon className="h-4 w-4 transition-all duration-500 dark:rotate-90 dark:scale-0" />
        <Sun className="absolute h-4 w-4 transition-all duration-500 -rotate-90 scale-0 dark:rotate-0 dark:scale-100" />
      </div>
      
      <span className="sr-only">切换主题</span>
    </Button>
  );
}
