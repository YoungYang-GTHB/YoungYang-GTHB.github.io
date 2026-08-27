import type { LucideIcon } from 'lucide-react';

interface Props {
  code: string;
  title: string;
  icon: LucideIcon;
}

export function SectionHeading({ code, title, icon: Icon }: Props) {
  return (
    <div className="flex w-full items-end gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center text-primary">
        <Icon className="h-4.5 w-4.5" strokeWidth={1.6} />
      </div>
      <div>
        <div className="font-mono text-[9px] tracking-[0.16em] text-muted-foreground">
          RESUME / {code}
        </div>
        <h2 className="mt-1 font-display text-2xl font-bold tracking-[-0.025em] md:text-3xl">{title}</h2>
      </div>
      <div className="mb-1 ml-auto hidden h-px max-w-72 flex-1 bg-foreground/15 sm:block" />
    </div>
  );
}
