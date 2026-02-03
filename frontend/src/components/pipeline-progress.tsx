'use client';

import { cn } from '@/lib/utils';
import {
  FileInput,
  Search,
  GitMerge,
  Shield,
  Lightbulb,
  Filter,
  FileText,
  Database,
  CheckCircle2,
  Loader2,
  Circle,
  XCircle,
} from 'lucide-react';

const PIPELINE_NODES = [
  { id: 'input_processor', label: 'Input Processing', icon: FileInput },
  { id: 'deep_research', label: 'Deep Research', icon: Search },
  { id: 'context_merger', label: 'Context Merge', icon: GitMerge },
  { id: 'competitor_scout', label: 'Competitor Scout', icon: Shield },
  { id: 'divergent_ideation', label: 'Divergent Ideation', icon: Lightbulb },
  { id: 'convergent_refinement', label: 'Convergent Refinement', icon: Filter },
  { id: 'asset_generator', label: 'Asset Generation', icon: FileText },
  { id: 'knowledge_capture', label: 'Knowledge Capture', icon: Database },
];

interface NodeStatus {
  [nodeId: string]: 'pending' | 'started' | 'completed' | 'failed';
}

interface PipelineProgressProps {
  nodeStatuses: NodeStatus;
  className?: string;
}

export function PipelineProgress({ nodeStatuses, className }: PipelineProgressProps) {
  return (
    <div className={cn('space-y-2', className)}>
      <h3 className="text-sm font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wide mb-3">
        Pipeline Progress
      </h3>
      <div className="space-y-1">
        {PIPELINE_NODES.map((node) => {
          const status = nodeStatuses[node.id] || 'pending';
          const Icon = node.icon;

          return (
            <div
              key={node.id}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all',
                status === 'completed' && 'text-emerald-700 dark:text-emerald-400',
                status === 'started' && 'text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30',
                status === 'failed' && 'text-red-700 dark:text-red-400',
                status === 'pending' && 'text-gray-400 dark:text-gray-600',
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span className="flex-1">{node.label}</span>
              <StatusIcon status={status} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
    case 'started':
      return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Circle className="h-3 w-3 text-gray-300 dark:text-gray-700" />;
  }
}
