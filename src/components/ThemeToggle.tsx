'use client';

import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    setTheme(initialTheme);
    document.documentElement.classList.toggle('dark', initialTheme === 'dark');
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  if (!mounted) {
    return <Button variant="ghost" size="icon" className="h-9 w-9" disabled />;
  }

  return (
    <Button
      variant="outline"
      size="sm"
      className="group relative h-9 w-9 overflow-hidden transition-all hover:border-primary hover:shadow-md"
      onClick={toggleTheme}
    >
      {/* 背景渐变 */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/10 opacity-0 transition-opacity group-hover:opacity-100" />
      
      {/* 图标动画 */}
      <div className="relative flex items-center justify-center">
        <Moon className="h-4 w-4 transition-all duration-500 dark:rotate-90 dark:scale-0" />
        <Sun className="absolute h-4 w-4 transition-all duration-500 -rotate-90 scale-0 dark:rotate-0 dark:scale-100" />
      </div>
      
      <span className="sr-only">切换主题</span>
    </Button>
  );
}
