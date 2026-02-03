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
  project_id?: string;
}

export interface RunDetail extends RunSummary {
  project_id?: string;
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

export interface ProjectSummary {
  project_id: string;
  client_name: string;
  created_at: string;
  updated_at: string;
  iteration_count: number;
  latest_status: 'pending' | 'running' | 'completed' | 'failed' | null;
  saved_plays_count: number;
  tags: string[];
}

export interface SavedPlay {
  play_id: string;
  iteration_id: string;
  play_data: {
    title: string;
    challenge: string;
    market_standard: string;
    proposed_solution: string;
    business_outcome: string;
    technical_stack: string[];
    confidence_score: number;
    citations: Array<{ title: string; url: string; snippet: string }>;
  };
  notes: string;
  saved_at: string;
}

export interface ProjectDetail extends ProjectSummary {
  notes: string;
  iterations: RunSummary[];
  saved_plays: SavedPlay[];
}

export interface IterateRequest {
  past_sales_history?: string;
  base_research_prompt?: string;
  parent_iteration_id?: string;
  build_on_previous?: boolean;
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

// --- Project API ---

export async function listProjects(): Promise<ProjectSummary[]> {
  return apiFetch<ProjectSummary[]>('/api/projects');
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  return apiFetch<ProjectDetail>(`/api/projects/${projectId}`);
}

export async function createProject(data: {
  client_name: string;
  tags?: string[];
  notes?: string;
}): Promise<ProjectSummary> {
  return apiFetch<ProjectSummary>('/api/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(
  projectId: string,
  data: { client_name?: string; notes?: string; tags?: string[] },
): Promise<ProjectSummary> {
  return apiFetch<ProjectSummary>(`/api/projects/${projectId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiFetch<void>(`/api/projects/${projectId}`, { method: 'DELETE' });
}

export async function startIteration(
  projectId: string,
  req: IterateRequest,
): Promise<RunSummary> {
  return apiFetch<RunSummary>(`/api/projects/${projectId}/iterate`, {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function savePlay(
  projectId: string,
  data: { iteration_id: string; play_index: number; notes?: string },
): Promise<SavedPlay> {
  return apiFetch<SavedPlay>(`/api/projects/${projectId}/plays`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function removeSavedPlay(
  projectId: string,
  playId: string,
): Promise<void> {
  await apiFetch<void>(`/api/projects/${projectId}/plays/${playId}`, {
    method: 'DELETE',
  });
}
