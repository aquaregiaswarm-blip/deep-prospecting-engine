'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listProjects, type ProjectSummary } from '@/lib/api';
import { ProjectCard } from '@/components/project-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FolderPlus, Loader2, BarChart3, Layers, Star, Search } from 'lucide-react';

export default function DashboardPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
    const interval = setInterval(loadProjects, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadProjects() {
    try {
      const data = await listProjects();
      setProjects(data);
      setError(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  const totalProjects = projects.length;
  const activeIterations = projects.filter(
    (p) => p.latest_status === 'running' || p.latest_status === 'pending',
  ).length;
  const totalPlays = projects.reduce((sum, p) => sum + p.saved_plays_count, 0);

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
        <Link href="/project/new">
          <Button>
            <FolderPlus className="h-4 w-4" />
            New Project
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
              <p className="text-2xl font-bold">{totalProjects}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Total Projects</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
              <Layers className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{activeIterations}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Active Iterations</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <Star className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalPlays}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Saved Plays</p>
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

      {/* Projects */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Projects</h2>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-[hsl(var(--muted-foreground))]" />
          </div>
        ) : projects.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Search className="h-12 w-12 mx-auto mb-4 text-gray-300 dark:text-gray-700" />
              <h3 className="font-semibold mb-1">No projects yet</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                Create your first project to start generating AI-powered sales intelligence.
              </p>
              <Link href="/project/new">
                <Button>
                  <FolderPlus className="h-4 w-4" />
                  Create First Project
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {projects.map((project) => (
              <ProjectCard key={project.project_id} project={project} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
