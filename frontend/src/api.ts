export type Report = {
  id: string; external_id: string; title: string; content: string;
  language: string; source_type: string; source_name: string;
  location: { latitude: number; longitude: number };
  observed_at: string; ingested_at: string; status: string;
};

export type Case = {
  id: string; title: string; summary: string; report_ids: string[]; created_at: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  reports: () => request<Report[]>('/api/v1/reports'),
  cases: () => request<Case[]>('/api/v1/cases'),
  createCase: (data: { title: string; summary: string; report_ids: string[] }) =>
    request<Case>('/api/v1/cases', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    }),
  createReport: (data: object) => request<Report>('/api/v1/reports', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  }),
};
