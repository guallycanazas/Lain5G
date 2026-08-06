import { apiRequest } from './apiClient';
import type { ProfileApplyResult, ProfileConfig, ProfileDiff, ProfileSummary, ProfileValidation } from '../types/profile';

export const profilesApi = {
  list: () => apiRequest<ProfileSummary[]>('/api/profiles'),
  detail: (profile: string) => apiRequest<ProfileConfig>(`/api/profiles/${encodeURIComponent(profile)}`),
  update: (profile: string, payload: ProfileConfig) => apiRequest<ProfileConfig>(`/api/profiles/${encodeURIComponent(profile)}`, { method: 'PUT', body: JSON.stringify(payload) }),
  validate: (profile: string) => apiRequest<ProfileValidation>(`/api/profiles/${encodeURIComponent(profile)}/validate`, { method: 'POST' }),
  diff: (profile: string) => apiRequest<ProfileDiff>(`/api/profiles/${encodeURIComponent(profile)}/diff`),
  apply: (profile: string) => apiRequest<ProfileApplyResult>(`/api/profiles/${encodeURIComponent(profile)}/apply`, { method: 'POST' }),
  restore: (profile: string) => apiRequest<ProfileApplyResult>(`/api/profiles/${encodeURIComponent(profile)}/restore`, { method: 'POST' }),
};
