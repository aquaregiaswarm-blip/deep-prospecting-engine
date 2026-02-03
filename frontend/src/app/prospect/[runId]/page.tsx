'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getRunStatus, streamRun, type RunDetail, type NodeProgress } from '@/lib/api';
import { PipelineProgress } from '@/components/pipeline-progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate, downloadMarkdown, cn } from '@/lib/utils';
import {
  ArrowLeft,
  Building2,
  Globe,
  Gauge,
  Target,
  Download,
  FileText,
  Shield,
  Loader2,
  AlertTriangle,
  ChevronDown,
} from 'lucide-react';

export default function RunDetailPage() {
  const params = useParams();
  const runId = params.runId as string;
  const [run, setRun] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, 'pending' | 'started' | 'completed' | 'failed'>>({});
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['plays']));

  const toggleSection = useCallback((section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  }, []);

  // Load initial data + start SSE if running
  useEffect(() => {
    let source: EventSource | null = null;

    async function init() {
      try {
        const data = await getRunStatus(runId);
        setRun(data);
        setLoading(false);

        if (data.status === 'running' || data.status === 'pending') {
          source = streamRun(
            runId,
            (event: NodeProgress) => {
              setNodeStatuses((prev) => ({ ...prev, [event.node]: event.status as 'pending' | 'started' | 'completed' | 'failed' }));
            },
            async () => {
              // Refetch full status on completion
              const updated = await getRunStatus(runId);
              setRun(updated);
            },
          );
        }
      } catch {
        setLoading(false);
      }
    }

    init();

    // Poll status while running
    const interval = setInterval(async () => {
      try {
        const data = await getRunStatus(runId);
        setRun(data);
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval);
          source?.close();
        }
      } catch {}
    }, 5000);

    return () => {
      clearInterval(interval);
      source?.close();
    };
  }, [runId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-pellera-500" />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold mb-2">Run not found</h2>
        <Link href="/" className="text-pellera-600 hover:underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const isActive = run.status === 'running' || run.status === 'pending';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back + header */}
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            {run.client_name}
            <Badge
              variant={
                run.status === 'completed'
                  ? 'success'
                  : run.status === 'failed'
                  ? 'danger'
                  : 'default'
              }
            >
              {run.status}
            </Badge>
          </h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
            Started {formatDate(run.created_at)}
            {run.completed_at && ` • Completed ${formatDate(run.completed_at)}`}
          </p>
        </div>
      </div>

      {/* Errors */}
      {run.errors.length > 0 && (
        <Card className="border-amber-200 dark:border-amber-800">
          <CardContent className="p-4">
            {run.errors.map((err, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-amber-700 dark:text-amber-400">
                <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                {err}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Progress + Client info */}
        <div className="space-y-6">
          {/* Pipeline progress */}
          {isActive && (
            <Card>
              <CardContent className="p-5">
                <PipelineProgress nodeStatuses={nodeStatuses} />
              </CardContent>
            </Card>
          )}

          {/* Client profile card */}
          {run.client_vertical && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Client Profile
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <InfoRow icon={Globe} label="Vertical" value={run.client_vertical} />
                <InfoRow icon={Globe} label="Domain" value={run.client_domain} />
                <InfoRow icon={Gauge} label="Digital Maturity" value={run.digital_maturity_summary} />
              </CardContent>
            </Card>
          )}

          {/* Competitor analysis */}
          {run.competitor_proofs.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Competitor Intelligence
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {run.competitor_proofs.map((proof, i) => (
                  <div key={i} className="text-sm space-y-0.5">
                    <p className="font-medium">{proof.competitor_name}</p>
                    <p className="text-[hsl(var(--muted-foreground))]">
                      {proof.use_case} → {proof.outcome}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column: Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Sales Plays */}
          {run.refined_plays.length > 0 && (
            <CollapsibleSection
              title={`Sales Plays (${run.refined_plays.length})`}
              icon={Target}
              expanded={expandedSections.has('plays')}
              onToggle={() => toggleSection('plays')}
            >
              <div className="space-y-4">
                {run.refined_plays.map((play, i) => (
                  <Card key={i} className="border-l-4 border-l-pellera-500">
                    <CardContent className="p-5 space-y-3">
                      <div className="flex items-start justify-between">
                        <h4 className="font-semibold">{play.title}</h4>
                        <Badge variant="outline">
                          {Math.round(play.confidence_score * 100)}% confidence
                        </Badge>
                      </div>
                      <div className="grid gap-2 text-sm">
                        <Detail label="Challenge" value={play.challenge} />
                        <Detail label="Solution" value={play.proposed_solution} />
                        <Detail label="Outcome" value={play.business_outcome} />
                        {play.technical_stack.length > 0 && (
                          <div>
                            <span className="font-medium text-[hsl(var(--muted-foreground))]">Stack: </span>
                            <div className="inline-flex flex-wrap gap-1 mt-1">
                              {play.technical_stack.map((t) => (
                                <Badge key={t} variant="outline" className="text-xs">
                                  {t}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      {/* Confidence bar */}
                      <div className="h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-pellera-500 transition-all duration-500"
                          style={{ width: `${play.confidence_score * 100}%` }}
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* One-Pagers */}
          {Object.keys(run.one_pagers).length > 0 && (
            <CollapsibleSection
              title="One-Pagers"
              icon={FileText}
              expanded={expandedSections.has('one_pagers')}
              onToggle={() => toggleSection('one_pagers')}
            >
              <div className="space-y-3">
                {Object.entries(run.one_pagers).map(([title, content]) => (
                  <Card key={title}>
                    <CardContent className="p-5">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-sm">{title}</h4>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            downloadMarkdown(
                              content,
                              `${title.toLowerCase().replace(/\s+/g, '_')}_one_pager.md`
                            )
                          }
                        >
                          <Download className="h-3 w-3" />
                          Download
                        </Button>
                      </div>
                      <pre className="text-xs bg-[hsl(var(--muted))] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap font-mono max-h-60 overflow-y-auto">
                        {content}
                      </pre>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* Strategic Plan */}
          {run.strategic_plan && (
            <CollapsibleSection
              title="Strategic Account Plan"
              icon={FileText}
              expanded={expandedSections.has('strategic_plan')}
              onToggle={() => toggleSection('strategic_plan')}
            >
              <Card>
                <CardContent className="p-5">
                  <div className="flex justify-end mb-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        downloadMarkdown(
                          run.strategic_plan,
                          `${run.client_name.toLowerCase().replace(/\s+/g, '_')}_strategic_plan.md`
                        )
                      }
                    >
                      <Download className="h-3 w-3" />
                      Download
                    </Button>
                  </div>
                  <pre className="text-xs bg-[hsl(var(--muted))] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                    {run.strategic_plan}
                  </pre>
                </CardContent>
              </Card>
            </CollapsibleSection>
          )}

          {/* Deep Research Report */}
          {run.deep_research_report && (
            <CollapsibleSection
              title="Deep Research Report"
              icon={FileText}
              expanded={expandedSections.has('research')}
              onToggle={() => toggleSection('research')}
            >
              <Card>
                <CardContent className="p-5">
                  <pre className="text-xs bg-[hsl(var(--muted))] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                    {run.deep_research_report}
                  </pre>
                </CardContent>
              </Card>
            </CollapsibleSection>
          )}

          {/* Empty state when no results yet */}
          {isActive && run.refined_plays.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <Loader2 className="h-10 w-10 animate-spin mx-auto mb-4 text-pellera-500" />
                <h3 className="font-semibold mb-1">Pipeline Running</h3>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">
                  Results will appear here as each stage completes.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Utility components ---

function InfoRow({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2 text-sm">
      <Icon className="h-4 w-4 mt-0.5 text-[hsl(var(--muted-foreground))] flex-shrink-0" />
      <div>
        <span className="text-[hsl(var(--muted-foreground))]">{label}:</span>{' '}
        <span className="font-medium">{value}</span>
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="font-medium text-[hsl(var(--muted-foreground))]">{label}: </span>
      <span>{value}</span>
    </div>
  );
}

function CollapsibleSection({
  title,
  icon: Icon,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  icon: any;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="flex items-center gap-2 w-full text-left mb-3 group"
      >
        <Icon className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
        <h2 className="text-lg font-semibold flex-1">{title}</h2>
        <ChevronDown
          className={cn(
            'h-4 w-4 text-[hsl(var(--muted-foreground))] transition-transform',
            expanded && 'rotate-180'
          )}
        />
      </button>
      {expanded && <div className="animate-slide-up">{children}</div>}
    </div>
  );
}
