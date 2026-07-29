import { apiRequest } from './apiClient';
import type { ComponentPullJob, PreparationReport, ProfileComponentStatus } from '../types/preparation';


export const preparationApi = {
  report: () => apiRequest<PreparationReport>('/api/preparation'),
  profile: (profileId: string, coreOnly = false) => apiRequest<ProfileComponentStatus>(
    `/api/preparation/profiles/${encodeURIComponent(profileId)}?core_only=${coreOnly}`,
  ),
  pull: (profileId: string, coreOnly = false) => apiRequest<ComponentPullJob>(
    `/api/preparation/profiles/${encodeURIComponent(profileId)}/pull`,
    { method: 'POST', body: JSON.stringify({ core_only: coreOnly }) },
  ),
  pullJob: (jobId: string) => apiRequest<ComponentPullJob>(`/api/preparation/pulls/${encodeURIComponent(jobId)}`),
  activePull: () => apiRequest<ComponentPullJob | null>('/api/preparation/pulls/active'),
};
