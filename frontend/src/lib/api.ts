/**
 * API client for the Deep Prospecting Engine backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RunSummary {
  run_id: string;
  client_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_step: string;
  created_at: string;
  completed_at: string | null;
  plays_count: number;
  error: string | null;
}

export interface RunDetail extends RunSummary {
  deep_research_report: string;
  client_vertical: string;
  client_domain: string;
  digital_maturity_summary: string;
  competitor_proofs: Array<{
    competitor_name: string;
    vertical: string;
    use_case: string;
    outcome: string;
  }>;
  refined_plays: Array<{
    title: string;
    challenge: string;
    market_standard: string;
    proposed_solution: string;
    business_outcome: string;
    technical_stack: string[];
    confidence_score: number;
    citations: Array<{ title: string; url: string; snippet: string }>;
  }>;
  one_pagers: Record<string, string>;
  strategic_plan: string;
  errors: string[];
}

export interface NodeProgress {
  run_id: string;
  node: string;
  status: string;
  timestamp: string;
  detail?: string;
  done?: boolean;
}

export interface ProspectRequest {
  client_name: string;
  past_sales_history?: string;
  base_research_prompt?: string;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function healthCheck() {
  return apiFetch<{ status: string; version: string }>('/api/health');
}

export async function startProspect(req: ProspectRequest): Promise<RunSummary> {
  return apiFetch<RunSummary>('/api/prospect', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function getRunStatus(runId: string): Promise<RunDetail> {
  return apiFetch<RunDetail>(`/api/prospect/${runId}/status`);
}

export async function listRuns(): Promise<RunSummary[]> {
  return apiFetch<RunSummary[]>('/api/runs');
}

/**
 * Subscribe to SSE stream for a run. Returns an EventSource.
 */
export function streamRun(
  runId: string,
  onEvent: (event: NodeProgress) => void,
  onDone: () => void,
  onError?: (err: Event) => void,
): EventSource {
  const source = new EventSource(`${API_BASE}/api/prospect/${runId}/stream`);

  source.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.done) {
      onDone();
      source.close();
      return;
    }
    onEvent(data as NodeProgress);
  };

  source.onerror = (e) => {
    onError?.(e);
    source.close();
  };

  return source;
}
