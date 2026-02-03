'use client';

import { useState } from 'react';
import { startIteration, type IterateRequest } from '@/lib/api';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogContent, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Rocket, Loader2, ToggleLeft, ToggleRight } from 'lucide-react';

interface IterateDialogProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  parentIterationId?: string;
  defaultResearchPrompt?: string;
  defaultSalesHistory?: string;
  onSuccess: (runId: string) => void;
}

export function IterateDialog({
  open,
  onClose,
  projectId,
  parentIterationId,
  defaultResearchPrompt = '',
  defaultSalesHistory = '',
  onSuccess,
}: IterateDialogProps) {
  const [researchPrompt, setResearchPrompt] = useState(defaultResearchPrompt);
  const [salesHistory, setSalesHistory] = useState(defaultSalesHistory);
  const [buildOnPrevious, setBuildOnPrevious] = useState(!!parentIterationId);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const req: IterateRequest = {
        base_research_prompt: researchPrompt || undefined,
        past_sales_history: salesHistory || undefined,
        build_on_previous: buildOnPrevious,
        parent_iteration_id: parentIterationId,
      };
      const run = await startIteration(projectId, req);
      onSuccess(run.run_id);
      onClose();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to start iteration';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-xl">
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>New Iteration</DialogTitle>
          <DialogDescription>
            Launch a new prospecting iteration for this project.
            {parentIterationId && ' Building on previous results.'}
          </DialogDescription>
        </DialogHeader>
        <DialogContent className="space-y-4">
          {/* Build on previous toggle */}
          <button
            type="button"
            onClick={() => setBuildOnPrevious(!buildOnPrevious)}
            className="flex items-center gap-3 w-full rounded-lg border p-3 text-sm hover:bg-[hsl(var(--muted))] transition-colors text-left"
          >
            {buildOnPrevious ? (
              <ToggleRight className="h-5 w-5 text-pellera-600 flex-shrink-0" />
            ) : (
              <ToggleLeft className="h-5 w-5 text-[hsl(var(--muted-foreground))] flex-shrink-0" />
            )}
            <div>
              <span className="font-medium">Build on previous research</span>
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">
                Use findings from prior iterations to deepen the analysis
              </p>
            </div>
          </button>

          {/* Research prompt */}
          <div>
            <label className="block text-sm font-medium mb-1.5">Research Prompt</label>
            <Textarea
              value={researchPrompt}
              onChange={(e) => setResearchPrompt(e.target.value)}
              placeholder="e.g., Focus on AI/ML use cases in supply chain…"
              rows={4}
            />
          </div>

          {/* Sales history */}
          <div>
            <label className="block text-sm font-medium mb-1.5">Sales History</label>
            <Textarea
              value={salesHistory}
              onChange={(e) => setSalesHistory(e.target.value)}
              placeholder="e.g., 2023: Sold 500 licenses…"
              rows={3}
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          )}
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Launching…
              </>
            ) : (
              <>
                <Rocket className="h-4 w-4" />
                Launch Iteration
              </>
            )}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}
