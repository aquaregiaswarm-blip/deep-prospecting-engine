'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { startProspect } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ArrowLeft, Rocket, Loader2, Building2, ClipboardList, Beaker } from 'lucide-react';
import Link from 'next/link';

export default function NewProspectPage() {
  const router = useRouter();
  const [clientName, setClientName] = useState('');
  const [salesHistory, setSalesHistory] = useState('');
  const [researchPrompt, setResearchPrompt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!clientName.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const run = await startProspect({
        client_name: clientName.trim(),
        past_sales_history: salesHistory,
        base_research_prompt: researchPrompt,
      });
      router.push(`/prospect/${run.run_id}`);
    } catch (e: any) {
      setError(e.message);
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
        <h1 className="text-3xl font-bold tracking-tight">New Prospect</h1>
        <p className="text-[hsl(var(--muted-foreground))] mt-1">
          Configure and launch a deep prospecting analysis
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
            <CardDescription>
              Who are you prospecting?
            </CardDescription>
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
              <ClipboardList className="h-5 w-5" />
              Sales History
            </CardTitle>
            <CardDescription>
              Past relationship context to improve recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={salesHistory}
              onChange={(e) => setSalesHistory(e.target.value)}
              placeholder="e.g., 2023: Sold 500 Cloud Storage licenses. 2024: Sold 200 Compute instances..."
              rows={5}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Beaker className="h-5 w-5" />
              Research Prompt
            </CardTitle>
            <CardDescription>
              Optional — customize the research focus area
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={researchPrompt}
              onChange={(e) => setResearchPrompt(e.target.value)}
              placeholder="e.g., Focus on supply chain and logistics AI use cases..."
              rows={4}
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
                Launching...
              </>
            ) : (
              <>
                <Rocket className="h-4 w-4" />
                Launch Prospecting
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
