'use client';

import { useState, useEffect } from 'react';
import { Menu, X, Home, User, Award, Briefcase, FileText, Lightbulb, GraduationCap, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from './ThemeToggle';
import Link from 'next/link';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: '首页', href: '/', icon: <Home className="h-4 w-4" /> },
  { label: '个人信息', href: '#header', icon: <User className="h-4 w-4" /> },
  { label: '教育背景', href: '#education', icon: <GraduationCap className="h-4 w-4" /> },
  { label: '专业技能', href: '#skills', icon: <FileText className="h-4 w-4" /> },
  { label: '项目经历', href: '#projects', icon: <Briefcase className="h-4 w-4" /> },
  { label: '实践经历', href: '#experience', icon: <Briefcase className="h-4 w-4" /> },
  { label: '荣誉奖项', href: '#awards', icon: <Award className="h-4 w-4" /> },
  { label: '学业荣誉', href: '#honors', icon: <Award className="h-4 w-4" /> },
  { label: '专利成果', href: '#patents', icon: <Lightbulb className="h-4 w-4" /> },
];

export function MobileNav({ name }: { name: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('');

  // 监听滚动更新活动状态
  useEffect(() => {
    const handleScroll = () => {
      const sections = navItems.map(item => item.href.replace('#', '')).filter(Boolean);
      const scrollPosition = window.scrollY + 100;

      for (const sectionId of sections) {
        const element = document.getElementById(sectionId);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(`#${sectionId}`);
            break;
          }
        }
      }

      if (window.scrollY < 50) {
        setActiveSection('/');
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 阻止背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleClick = (href: string) => {
    setIsOpen(false);
    if (href.startsWith('#')) {
      const element = document.querySelector(href);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <>
      {/* 菜单按钮 */}
      <Button
        variant="ghost"
        size="icon"
        className="h-9 w-9 md:hidden"
        onClick={() => setIsOpen(true)}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* 遮罩层 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* 侧边栏 */}
      <div
        className={`fixed left-0 top-0 z-50 h-full w-[280px] transform bg-background shadow-2xl transition-transform duration-300 ease-in-out md:hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* 侧边栏头部 */}
        <div className="flex items-center justify-between border-b p-4">
          <span className="text-lg font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            {name}
          </span>
          <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 space-y-1 p-4">
          {navItems.map((item) => (
            <button
              key={item.label}
              onClick={() => handleClick(item.href)}
              className={`flex w-full items-center justify-between rounded-lg px-4 py-3 text-sm transition-colors ${
                activeSection === item.href
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-secondary'
              }`}
            >
              <div className="flex items-center gap-3">
                {item.icon}
                <span>{item.label}</span>
              </div>
              <ChevronRight className="h-4 w-4" />
            </button>
          ))}
        </nav>

        {/* 底部主题切换 */}
        <div className="border-t p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">主题</span>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </>
  );
}
