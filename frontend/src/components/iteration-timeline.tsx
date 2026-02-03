'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import type { RunSummary } from '@/lib/api';
import { CheckCircle2, Circle, Loader2, XCircle, Layers, ArrowRight } from 'lucide-react';

function statusVariant(status: string) {
  switch (status) {
    case 'completed':
      return 'success' as const;
    case 'running':
      return 'default' as const;
    case 'failed':
      return 'danger' as const;
    default:
      return 'outline' as const;
  }
}

function StatusDot({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
    case 'running':
      return <Loader2 className="h-5 w-5 text-pellera-500 animate-spin" />;
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return <Circle className="h-5 w-5 text-gray-400" />;
  }
}

interface IterationTimelineProps {
  iterations: RunSummary[];
}

export function IterationTimeline({ iterations }: IterationTimelineProps) {
  if (iterations.length === 0) {
    return (
      <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
        <Layers className="h-10 w-10 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No iterations yet. Start your first one!</p>
      </div>
    );
  }

  // Show newest first
  const sorted = [...iterations].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-[9px] top-3 bottom-3 w-0.5 bg-[hsl(var(--border))]" />

      <div className="space-y-0">
        {sorted.map((iteration, index) => {
          const iterationNum = iterations.length - iterations.indexOf(iteration);
          return (
            <Link
              key={iteration.run_id}
              href={`/prospect/${iteration.run_id}`}
              className="group block"
            >
              <div className="relative flex items-start gap-4 py-4 px-2 rounded-lg hover:bg-[hsl(var(--muted))] transition-colors">
                {/* Dot on timeline */}
                <div className="relative z-10 flex-shrink-0 bg-[hsl(var(--surface))]">
                  <StatusDot status={iteration.status} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm">Iteration #{iterationNum}</span>
                    <Badge variant={statusVariant(iteration.status)} className="text-[10px]">
                      {iteration.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    {formatDate(iteration.created_at)}
                    {iteration.completed_at && ` → ${formatDate(iteration.completed_at)}`}
                  </p>
                  {iteration.plays_count > 0 && (
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                      {iteration.plays_count} play{iteration.plays_count !== 1 ? 's' : ''} generated
                    </p>
                  )}
                  {iteration.current_step && iteration.status === 'running' && (
                    <p className="text-xs text-pellera-600 dark:text-pellera-400 mt-1">
                      {iteration.current_step}
                    </p>
                  )}
                </div>

                <ArrowRight className="h-4 w-4 text-gray-300 group-hover:text-pellera-500 transition-colors mt-1 flex-shrink-0" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
