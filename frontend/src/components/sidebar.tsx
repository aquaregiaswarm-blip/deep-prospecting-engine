'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useTheme } from '@/components/theme-provider';
import {
  LayoutDashboard,
  Search,
  Sun,
  Moon,
  Beaker,
} from 'lucide-react';

const navItems = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'New Prospect', href: '/prospect/new', icon: Search },
];

export function Sidebar() {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-[hsl(var(--surface))] p-4">
      {/* Brand */}
      <Link href="/" className="flex items-center gap-2 px-2 mb-8">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-pellera-600 text-white font-bold text-lg">
          🜆
        </div>
        <div>
          <p className="font-semibold text-sm leading-tight">Deep Prospecting</p>
          <p className="text-[10px] uppercase tracking-widest text-[hsl(var(--muted-foreground))]">
            by Pellera
          </p>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-pellera-50 text-pellera-700 dark:bg-pellera-950/50 dark:text-pellera-300'
                  : 'text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]'
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Theme toggle */}
      <button
        onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
        className="mt-auto flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] transition-colors"
      >
        {resolvedTheme === 'dark' ? (
          <Sun className="h-4 w-4" />
        ) : (
          <Moon className="h-4 w-4" />
        )}
        {resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
      </button>
    </aside>
  );
}
