'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listRuns, type RunSummary } from '@/lib/api';
import { RunCard } from '@/components/run-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Search, Plus, Loader2, BarChart3, Layers, CheckCircle2 } from 'lucide-react';

export default function DashboardPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRuns();
    // Poll every 10s for active runs
    const interval = setInterval(loadRuns, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadRuns() {
    try {
      const data = await listRuns();
      setRuns(data);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const completedRuns = runs.filter((r) => r.status === 'completed');
  const activeRuns = runs.filter((r) => r.status === 'running' || r.status === 'pending');
  const totalPlays = runs.reduce((sum, r) => sum + r.plays_count, 0);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-[hsl(var(--muted-foreground))] mt-1">
            AI-powered sales intelligence pipeline
          </p>
        </div>
        <Link href="/prospect/new">
          <Button>
            <Plus className="h-4 w-4" />
            New Prospect
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-pellera-100 dark:bg-pellera-900/30">
              <BarChart3 className="h-5 w-5 text-pellera-600 dark:text-pellera-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{runs.length}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Total Runs</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{completedRuns.length}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Completed</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <Layers className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalPlays}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Sales Plays Generated</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error state */}
      {error && (
        <Card className="border-red-200 dark:border-red-800">
          <CardContent className="p-5 text-sm text-red-600 dark:text-red-400">
            Unable to connect to API: {error}
          </CardContent>
        </Card>
      )}

      {/* Active Runs */}
      {activeRuns.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
            Active Runs
          </h2>
          <div className="space-y-3">
            {activeRuns.map((run) => (
              <RunCard key={run.run_id} run={run} />
            ))}
          </div>
        </div>
      )}

      {/* All Runs */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Recent Runs</h2>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-[hsl(var(--muted-foreground))]" />
          </div>
        ) : runs.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Search className="h-12 w-12 mx-auto mb-4 text-gray-300 dark:text-gray-700" />
              <h3 className="font-semibold mb-1">No prospecting runs yet</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                Start your first run to generate AI-powered sales intelligence.
              </p>
              <Link href="/prospect/new">
                <Button>
                  <Plus className="h-4 w-4" />
                  Start First Prospect
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {runs.map((run) => (
              <RunCard key={run.run_id} run={run} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
