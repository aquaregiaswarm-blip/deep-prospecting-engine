'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createProject } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ArrowLeft, Building2, Tag, FileText, Loader2, FolderPlus } from 'lucide-react';

export default function NewProjectPage() {
  const router = useRouter();
  const [clientName, setClientName] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!clientName.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const tags = tagsInput
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);

      const project = await createProject({
        client_name: clientName.trim(),
        tags: tags.length > 0 ? tags : undefined,
        notes: notes || undefined,
      });
      router.push(`/project/${project.project_id}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to create project';
      setError(msg);
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      {/* Back link */}
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">New Project</h1>
        <p className="text-[hsl(var(--muted-foreground))] mt-1">
          Create a project workspace for iterative prospecting
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Client Information
            </CardTitle>
            <CardDescription>Who are you prospecting?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">
                Client Name <span className="text-red-500">*</span>
              </label>
              <Input
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                placeholder="e.g., Acme Corporation"
                required
                autoFocus
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              Tags
            </CardTitle>
            <CardDescription>Comma-separated labels for organization</CardDescription>
          </CardHeader>
          <CardContent>
            <Input
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="e.g., enterprise, manufacturing, priority"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Initial Notes
            </CardTitle>
            <CardDescription>Optional context or strategy notes</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g., Key contacts, known pain points, strategic priorities…"
              rows={5}
            />
          </CardContent>
        </Card>

        {error && (
          <div className="rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-400">
            {error}
          </div>
        )}

        <div className="flex justify-end">
          <Button type="submit" size="lg" disabled={submitting || !clientName.trim()}>
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating…
              </>
            ) : (
              <>
                <FolderPlus className="h-4 w-4" />
                Create Project
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
