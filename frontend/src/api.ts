export type Report = {
  id: string; external_id: string; title: string; content: string;
  language: string; source_type: string; source_name: string;
  location: { latitude: number; longitude: number };
  observed_at: string; ingested_at: string; status: string;
};

export type Case = {
  id: string; title: string; summary: string; report_ids: string[];
  report_titles: string[]; created_at: string;
};

export type Approval = {
  id: string; case_id: string; case_title: string; action_description: string;
  status: 'pending' | 'approved' | 'rejected'; requested_by: string;
  decided_by: string | null; decision_reason: string | null;
  created_at: string; decided_at: string | null;
};

export type AuditEvent = {
  id: string; case_id: string; approval_id: string; actor_id: string;
  event_type: string; details: string; occurred_at: string;
};

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

async function checkedResponse(path: string, options?: RequestInit): Promise<Response> {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new ApiError(typeof detail === 'string' ? detail : detail?.message ?? `Request failed (${response.status})`, response.status);
  }
  return response;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await checkedResponse(path, options);
  return response.json() as Promise<T>;
}

export const api = {
  reports: async (params: { query?: string; language?: string; limit?: number; offset?: number } = {}) => {
    const search = new URLSearchParams();
    if (params.query) search.set('query', params.query);
    if (params.language && params.language !== 'all') search.set('language', params.language);
    search.set('limit', String(params.limit ?? 10));
    search.set('offset', String(params.offset ?? 0));
    const response = await checkedResponse(`/api/v1/reports?${search}`);
    return { items: await response.json() as Report[], total: Number(response.headers.get('X-Total-Count') ?? 0) };
  },
  languages: () => request<string[]>('/api/v1/reports/languages'),
  cases: () => request<Case[]>('/api/v1/cases'),
  approvals: (actor: string) => request<Approval[]>('/api/v1/approvals', {
    headers: { 'X-Demo-Actor': actor },
  }),
  auditEvents: (actor: string) => request<AuditEvent[]>('/api/v1/audit-events', {
    headers: { 'X-Demo-Actor': actor },
  }),
  requestApproval: (caseId: string, actionDescription: string, actor: string) =>
    request<Approval>(`/api/v1/cases/${caseId}/approvals`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Demo-Actor': actor },
      body: JSON.stringify({ action_description: actionDescription }),
    }),
  decideApproval: (id: string, decision: 'approved' | 'rejected', reason: string, actor: string) =>
    request<Approval>(`/api/v1/approvals/${id}/decision`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Demo-Actor': actor },
      body: JSON.stringify({ decision, reason }),
    }),
  createCase: (data: { title: string; summary: string; report_ids: string[] }) =>
    request<Case>('/api/v1/cases', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    }),
  createReport: (data: object) => request<Report>('/api/v1/reports', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  }),
};
