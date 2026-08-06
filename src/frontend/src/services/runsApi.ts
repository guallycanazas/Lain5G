import { apiRequest } from './apiClient';
import type { RunDetail, RunSummary } from '../types/run';

export const runsApi = {
  list: (filters?: { scenario?: string; status?: string; limit?: number }) => {
    const params = new URLSearchParams();
    if (filters?.scenario) params.set('scenario', filters.scenario);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.limit) params.set('limit', String(filters.limit));
    const query = params.toString();
    return apiRequest<RunSummary[]>(`/api/runs${query ? `?${query}` : ''}`);
  },
  latest: () => apiRequest<RunDetail>('/api/runs/latest'),
  detail: (runId: string) => apiRequest<RunDetail>(`/api/runs/${encodeURIComponent(runId)}`),
};
