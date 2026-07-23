import { apiRequest } from './apiClient';
import type { ComponentPullResponse, PreparationReport, ProfileComponentStatus } from '../types/preparation';


export const preparationApi = {
  report: () => apiRequest<PreparationReport>('/api/preparation'),
  profile: (profileId: string, coreOnly = false) => apiRequest<ProfileComponentStatus>(
    `/api/preparation/profiles/${encodeURIComponent(profileId)}?core_only=${coreOnly}`,
  ),
  pull: (profileId: string, coreOnly = false) => apiRequest<ComponentPullResponse>(
    `/api/preparation/profiles/${encodeURIComponent(profileId)}/pull`,
    { method: 'POST', body: JSON.stringify({ core_only: coreOnly }) },
  ),
};
