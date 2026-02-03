'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  getProject,
  getRunStatus,
  savePlay,
  removeSavedPlay,
  type ProjectDetail,
  type RunDetail,
  type SavedPlay,
} from '@/lib/api';
import { IterationTimeline } from '@/components/iteration-timeline';
import { SavedPlaysList } from '@/components/saved-plays-list';
import { ProjectNotes } from '@/components/project-notes';
import { IterateDialog } from '@/components/iterate-dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate, downloadMarkdown, cn } from '@/lib/utils';
import {
  ArrowLeft,
  Rocket,
  Loader2,
  Layers,
  Star,
  FileText,
  Shield,
  BookOpen,
  StickyNote,
  ChevronDown,
  Download,
  BarChart3,
  Target,
} from 'lucide-react';

const TABS = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'iterations', label: 'Iterations', icon: Layers },
  { id: 'research', label: 'Research', icon: BookOpen },
  { id: 'plays', label: 'Plays', icon: Target },
  { id: 'intel', label: 'Intel', icon: Shield },
  { id: 'assets', label: 'Assets', icon: FileText },
  { id: 'notes', label: 'Notes', icon: StickyNote },
] as const;

type TabId = (typeof TABS)[number]['id'];

function statusVariant(status: string | null) {
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

export default function ProjectWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [iterateOpen, setIterateOpen] = useState(false);
  const [iterationDetails, setIterationDetails] = useState<Record<string, RunDetail>>({});

  const loadProject = useCallback(async () => {
    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch {
      // fail silently on poll
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
    const interval = setInterval(loadProject, 10000);
    return () => clearInterval(interval);
  }, [loadProject]);

  // Load iteration details for research/plays/intel/assets tabs
  useEffect(() => {
    if (!project) return;
    const completedIterations = project.iterations.filter((i) => i.status === 'completed');
    completedIterations.forEach(async (iter) => {
      if (iterationDetails[iter.run_id]) return;
      try {
        const detail = await getRunStatus(iter.run_id);
        setIterationDetails((prev) => ({ ...prev, [iter.run_id]: detail }));
      } catch {
        // ignore
      }
    });
  }, [project, iterationDetails]);

  async function handleSavePlay(iterationId: string, playIndex: number) {
    try {
      await savePlay(projectId, { iteration_id: iterationId, play_index: playIndex });
      loadProject();
    } catch {
      // ignore
    }
  }

  async function handleRemovePlay(playId: string) {
    try {
      await removeSavedPlay(projectId, playId);
      loadProject();
    } catch {
      // ignore
    }
  }

  function handleIterateSuccess(runId: string) {
    loadProject();
    router.push(`/prospect/${runId}`);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-pellera-500" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold mb-2">Project not found</h2>
        <Link href="/" className="text-pellera-600 hover:underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const latestIteration = project.iterations.length > 0
    ? [...project.iterations].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )[0]
    : null;

  const allIterationDetails = Object.values(iterationDetails).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            {project.client_name}
            {project.latest_status && (
              <Badge variant={statusVariant(project.latest_status)}>
                {project.latest_status}
              </Badge>
            )}
          </h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
            {project.iteration_count} iteration{project.iteration_count !== 1 ? 's' : ''}
            {project.saved_plays_count > 0 && ` • ${project.saved_plays_count} saved plays`}
            {project.tags.length > 0 && (
              <span className="ml-2">
                {project.tags.map((t) => (
                  <Badge key={t} variant="outline" className="text-[10px] ml-1 px-1.5 py-0">
                    {t}
                  </Badge>
                ))}
              </span>
            )}
          </p>
        </div>
        <Button onClick={() => setIterateOpen(true)}>
          <Rocket className="h-4 w-4" />
          New Iteration
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-0 -mb-px overflow-x-auto">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
                  isActive
                    ? 'border-pellera-600 text-pellera-700 dark:text-pellera-300'
                    : 'border-transparent text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:border-gray-300 dark:hover:border-gray-600',
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in">
        {activeTab === 'overview' && (
          <OverviewTab
            project={project}
            latestIteration={latestIteration ? iterationDetails[latestIteration.run_id] : undefined}
          />
        )}
        {activeTab === 'iterations' && (
          <IterationTimeline iterations={project.iterations} />
        )}
        {activeTab === 'research' && (
          <ResearchTab details={allIterationDetails} />
        )}
        {activeTab === 'plays' && (
          <PlaysTab
            savedPlays={project.saved_plays}
            iterationDetails={allIterationDetails}
            onSavePlay={handleSavePlay}
            onRemovePlay={handleRemovePlay}
            savedPlayIds={new Set(project.saved_plays.map((p) => `${p.iteration_id}-${p.play_data.title}`))}
          />
        )}
        {activeTab === 'intel' && (
          <IntelTab details={allIterationDetails} />
        )}
        {activeTab === 'assets' && (
          <AssetsTab details={allIterationDetails} />
        )}
        {activeTab === 'notes' && (
          <ProjectNotes projectId={projectId} initialNotes={project.notes || ''} />
        )}
      </div>

      {/* Iterate Dialog */}
      <IterateDialog
        open={iterateOpen}
        onClose={() => setIterateOpen(false)}
        projectId={projectId}
        parentIterationId={latestIteration?.run_id}
        onSuccess={handleIterateSuccess}
      />
    </div>
  );
}

// --- Tab Components ---

function OverviewTab({
  project,
  latestIteration,
}: {
  project: ProjectDetail;
  latestIteration?: RunDetail;
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Quick stats */}
      <div className="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Iterations" value={project.iteration_count} />
        <StatCard label="Saved Plays" value={project.saved_plays_count} />
        <StatCard
          label="Total Plays"
          value={project.iterations.reduce((s, i) => s + i.plays_count, 0)}
        />
        <StatCard label="Latest Status" value={project.latest_status || 'N/A'} />
      </div>

      {/* Latest iteration summary */}
      {latestIteration && (
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-semibold">Latest Iteration Results</h3>
          {latestIteration.refined_plays.length > 0 ? (
            <div className="space-y-3">
              {latestIteration.refined_plays.slice(0, 3).map((play, i) => (
                <Card key={i} className="border-l-4 border-l-pellera-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <h4 className="font-medium text-sm">{play.title}</h4>
                      <Badge variant="outline" className="text-xs">
                        {Math.round(play.confidence_score * 100)}%
                      </Badge>
                    </div>
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                      {play.proposed_solution}
                    </p>
                  </CardContent>
                </Card>
              ))}
              {latestIteration.refined_plays.length > 3 && (
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  +{latestIteration.refined_plays.length - 3} more plays
                </p>
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="p-6 text-center text-sm text-[hsl(var(--muted-foreground))]">
                No plays generated yet in this iteration.
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Recent activity / saved plays */}
      <div className="space-y-4">
        <h3 className="font-semibold">Saved Plays</h3>
        {project.saved_plays.length > 0 ? (
          <div className="space-y-2">
            {project.saved_plays.slice(0, 5).map((play) => (
              <div
                key={play.play_id}
                className="flex items-center gap-2 text-sm p-2 rounded-lg bg-[hsl(var(--muted))]"
              >
                <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500 flex-shrink-0" />
                <span className="truncate">{play.play_data.title}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            No saved plays yet. Star plays from iterations to save them.
          </p>
        )}
      </div>

      {!latestIteration && project.iterations.length === 0 && (
        <div className="lg:col-span-3">
          <Card>
            <CardContent className="p-12 text-center">
              <Rocket className="h-10 w-10 mx-auto mb-4 text-gray-300 dark:text-gray-700" />
              <h3 className="font-semibold mb-1">No iterations yet</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Start your first iteration to generate AI-powered sales intelligence.
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="p-4 text-center">
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-[hsl(var(--muted-foreground))]">{label}</p>
      </CardContent>
    </Card>
  );
}

function ResearchTab({ details }: { details: RunDetail[] }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const withResearch = details.filter((d) => d.deep_research_report);
  if (withResearch.length === 0) {
    return (
      <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
        <BookOpen className="h-10 w-10 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No research reports yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {withResearch.map((detail) => (
        <Card key={detail.run_id}>
          <CardContent className="p-5">
            <button
              onClick={() =>
                setExpanded((prev) => {
                  const next = new Set(prev);
                  if (next.has(detail.run_id)) next.delete(detail.run_id);
                  else next.add(detail.run_id);
                  return next;
                })
              }
              className="flex items-center justify-between w-full text-left"
            >
              <div>
                <h4 className="font-semibold text-sm">{detail.client_name}</h4>
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  {formatDate(detail.created_at)}
                </p>
              </div>
              <ChevronDown
                className={cn(
                  'h-4 w-4 text-[hsl(var(--muted-foreground))] transition-transform',
                  expanded.has(detail.run_id) && 'rotate-180',
                )}
              />
            </button>
            {expanded.has(detail.run_id) && (
              <pre className="mt-4 text-xs bg-[hsl(var(--muted))] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                {detail.deep_research_report}
              </pre>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function PlaysTab({
  savedPlays,
  iterationDetails,
  onSavePlay,
  onRemovePlay,
  savedPlayIds,
}: {
  savedPlays: SavedPlay[];
  iterationDetails: RunDetail[];
  onSavePlay: (iterationId: string, playIndex: number) => void;
  onRemovePlay: (playId: string) => void;
  savedPlayIds: Set<string>;
}) {
  return (
    <div className="space-y-6">
      {/* Saved plays section */}
      {savedPlays.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Star className="h-4 w-4 text-amber-500" />
            Saved Plays
          </h3>
          <SavedPlaysList plays={savedPlays} onRemove={onRemovePlay} />
        </div>
      )}

      {/* All plays from iterations */}
      {iterationDetails.map((detail) => {
        if (detail.refined_plays.length === 0) return null;
        return (
          <div key={detail.run_id}>
            <h3 className="font-semibold mb-3 text-sm text-[hsl(var(--muted-foreground))]">
              {formatDate(detail.created_at)} — {detail.refined_plays.length} plays
            </h3>
            <div className="space-y-3">
              {detail.refined_plays.map((play, i) => {
                const isSaved = savedPlayIds.has(`${detail.run_id}-${play.title}`);
                return (
                  <Card key={i} className="border-l-4 border-l-pellera-500">
                    <CardContent className="p-5 space-y-3">
                      <div className="flex items-start justify-between">
                        <h4 className="font-semibold">{play.title}</h4>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {Math.round(play.confidence_score * 100)}%
                          </Badge>
                          <button
                            onClick={() => onSavePlay(detail.run_id, i)}
                            className={cn(
                              'transition-colors',
                              isSaved
                                ? 'text-amber-500'
                                : 'text-gray-300 hover:text-amber-500',
                            )}
                            title={isSaved ? 'Already saved' : 'Save play'}
                          >
                            <Star
                              className={cn('h-4 w-4', isSaved && 'fill-amber-500')}
                            />
                          </button>
                        </div>
                      </div>
                      <div className="grid gap-2 text-sm">
                        <div>
                          <span className="font-medium text-[hsl(var(--muted-foreground))]">Challenge: </span>
                          {play.challenge}
                        </div>
                        <div>
                          <span className="font-medium text-[hsl(var(--muted-foreground))]">Solution: </span>
                          {play.proposed_solution}
                        </div>
                        <div>
                          <span className="font-medium text-[hsl(var(--muted-foreground))]">Outcome: </span>
                          {play.business_outcome}
                        </div>
                      </div>
                      <div className="h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-pellera-500 transition-all duration-500"
                          style={{ width: `${play.confidence_score * 100}%` }}
                        />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        );
      })}

      {savedPlays.length === 0 && iterationDetails.every((d) => d.refined_plays.length === 0) && (
        <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
          <Target className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p className="text-sm">No plays generated yet.</p>
        </div>
      )}
    </div>
  );
}

function IntelTab({ details }: { details: RunDetail[] }) {
  const allProofs = details.flatMap((d) =>
    d.competitor_proofs.map((p) => ({ ...p, run_id: d.run_id, date: d.created_at })),
  );

  if (allProofs.length === 0) {
    return (
      <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
        <Shield className="h-10 w-10 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No competitor intelligence yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {allProofs.map((proof, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold text-sm">{proof.competitor_name}</h4>
                <p className="text-xs text-[hsl(var(--muted-foreground))]">{proof.vertical}</p>
              </div>
              <span className="text-xs text-[hsl(var(--muted-foreground))]">
                {formatDate(proof.date)}
              </span>
            </div>
            <p className="text-sm mt-2">
              <span className="font-medium text-[hsl(var(--muted-foreground))]">Use case:</span>{' '}
              {proof.use_case}
            </p>
            <p className="text-sm">
              <span className="font-medium text-[hsl(var(--muted-foreground))]">Outcome:</span>{' '}
              {proof.outcome}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function AssetsTab({ details }: { details: RunDetail[] }) {
  const withAssets = details.filter(
    (d) => Object.keys(d.one_pagers).length > 0 || d.strategic_plan,
  );

  if (withAssets.length === 0) {
    return (
      <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
        <FileText className="h-10 w-10 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No assets generated yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {withAssets.map((detail) => (
        <div key={detail.run_id}>
          <h3 className="font-semibold mb-3 text-sm text-[hsl(var(--muted-foreground))]">
            {formatDate(detail.created_at)}
          </h3>
          <div className="space-y-3">
            {Object.entries(detail.one_pagers).map(([title, content]) => (
              <Card key={title}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-sm">{title}</h4>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">One-Pager</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      downloadMarkdown(
                        content,
                        `${title.toLowerCase().replace(/\s+/g, '_')}_one_pager.md`,
                      )
                    }
                  >
                    <Download className="h-3 w-3" />
                    Download
                  </Button>
                </CardContent>
              </Card>
            ))}
            {detail.strategic_plan && (
              <Card>
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-sm">Strategic Account Plan</h4>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">
                      Full strategic plan
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      downloadMarkdown(
                        detail.strategic_plan,
                        `${detail.client_name.toLowerCase().replace(/\s+/g, '_')}_strategic_plan.md`,
                      )
                    }
                  >
                    <Download className="h-3 w-3" />
                    Download
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
