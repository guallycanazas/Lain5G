import { useQuery } from '@tanstack/react-query';
import { runsApi } from '../services/runsApi';

export function useRuns(filters?: { scenario?: string; status?: string; limit?: number }) {
  return useQuery({ queryKey: ['runs', filters], queryFn: () => runsApi.list(filters) });
}

export function useRunDetail(runId?: string) {
  return useQuery({ queryKey: ['runs', runId], queryFn: () => runsApi.detail(runId || ''), enabled: Boolean(runId) });
}
