'use client';

import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate, statusColor } from '@/lib/utils';
import type { RunSummary } from '@/lib/api';
import { ArrowRight, Building2, Clock, Layers } from 'lucide-react';

function statusVariant(status: string) {
  switch (status) {
    case 'completed': return 'success' as const;
    case 'running': return 'default' as const;
    case 'failed': return 'danger' as const;
    default: return 'outline' as const;
  }
}

export function RunCard({ run }: { run: RunSummary }) {
  return (
    <Link href={`/prospect/${run.run_id}`}>
      <Card className="group hover:shadow-md hover:border-pellera-300 dark:hover:border-pellera-700 transition-all cursor-pointer">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                <h3 className="font-semibold text-base">{run.client_name}</h3>
              </div>
              <div className="flex items-center gap-4 text-xs text-[hsl(var(--muted-foreground))]">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(run.created_at)}
                </span>
                {run.plays_count > 0 && (
                  <span className="flex items-center gap-1">
                    <Layers className="h-3 w-3" />
                    {run.plays_count} plays
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={statusVariant(run.status)}>
                {run.status}
              </Badge>
              <ArrowRight className="h-4 w-4 text-gray-300 group-hover:text-pellera-500 transition-colors" />
            </div>
          </div>
          {run.error && (
            <p className="mt-2 text-xs text-red-600 dark:text-red-400 truncate">
              {run.error}
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
