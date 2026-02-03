'use client';

import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import type { ProjectSummary } from '@/lib/api';
import { ArrowRight, Building2, Clock, Layers, Star, Tag } from 'lucide-react';

function statusVariant(status: ProjectSummary['latest_status']) {
  switch (status) {
    case 'completed':
      return 'success' as const;
    case 'running':
      return 'default' as const;
    case 'failed':
      return 'danger' as const;
    case 'pending':
      return 'warning' as const;
    default:
      return 'outline' as const;
  }
}

export function ProjectCard({ project }: { project: ProjectSummary }) {
  return (
    <Link href={`/project/${project.project_id}`}>
      <Card className="group hover:shadow-md hover:border-pellera-300 dark:hover:border-pellera-700 transition-all cursor-pointer">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-[hsl(var(--muted-foreground))] flex-shrink-0" />
                <h3 className="font-semibold text-base truncate">{project.client_name}</h3>
              </div>
              <div className="flex items-center gap-4 text-xs text-[hsl(var(--muted-foreground))]">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(project.updated_at)}
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="h-3 w-3" />
                  {project.iteration_count} iteration{project.iteration_count !== 1 ? 's' : ''}
                </span>
                {project.saved_plays_count > 0 && (
                  <span className="flex items-center gap-1">
                    <Star className="h-3 w-3 text-amber-500" />
                    {project.saved_plays_count} saved
                  </span>
                )}
              </div>
              {project.tags.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap">
                  {project.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-[10px] px-1.5 py-0">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0 ml-3">
              {project.latest_status && (
                <Badge variant={statusVariant(project.latest_status)}>
                  {project.latest_status}
                </Badge>
              )}
              <ArrowRight className="h-4 w-4 text-gray-300 group-hover:text-pellera-500 transition-colors" />
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
