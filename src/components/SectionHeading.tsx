import type { LucideIcon } from 'lucide-react';

interface Props {
  code: string;
  title: string;
  icon: LucideIcon;
}

export function SectionHeading({ code, title, icon: Icon }: Props) {
  return (
    <div className="flex w-full items-center gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center bg-primary text-primary-foreground">
        <Icon className="h-4.5 w-4.5" />
      </div>
      <div>
        <div className="font-mono text-[9px] tracking-[0.16em] text-muted-foreground">
          RESUME / {code}
        </div>
        <h2 className="mt-0.5 text-xl font-bold tracking-[-0.025em] md:text-2xl">{title}</h2>
      </div>
      <div className="ml-auto hidden items-center gap-2 font-mono text-[9px] tracking-[0.14em] text-muted-foreground sm:flex">
        <span className="h-1.5 w-1.5 bg-signal" />
        STRUCTURED RECORD
      </div>
    </div>
  );
}
