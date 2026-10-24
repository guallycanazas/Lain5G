import { apiRequest } from './apiClient';
import type {
  SubscriberClonePayload,
  SubscriberConnectionStatus,
  SubscriberDetail,
  SubscriberFormPayload,
  SubscriberListResponse,
  SubscriberOperationResponse,
  SubscriberValidationResult,
  SubscriberProfile,
} from '../types/subscriber';

const profileQuery = (profile: SubscriberProfile) => `profile=${encodeURIComponent(profile)}`;

export const subscribersApi = {
  connection: (profile: SubscriberProfile = '4g-lte-x310') => apiRequest<SubscriberConnectionStatus>(`/api/subscribers/connection?${profileQuery(profile)}`),
  list: (params: { limit: number; offset: number; search?: string; profile?: SubscriberProfile }) => {
    const query = new URLSearchParams({ limit: String(params.limit), offset: String(params.offset), profile: params.profile || '4g-lte-x310' });
    if (params.search?.trim()) query.set('search', params.search.trim());
    return apiRequest<SubscriberListResponse>(`/api/subscribers?${query.toString()}`);
  },
  detail: (imsi: string, profile: SubscriberProfile = '4g-lte-x310') => apiRequest<SubscriberDetail>(`/api/subscribers/${encodeURIComponent(imsi)}?${profileQuery(profile)}`),
  validate: (payload: SubscriberFormPayload) => apiRequest<SubscriberValidationResult>('/api/subscribers/validate', { method: 'POST', body: JSON.stringify(payload) }),
  create: (payload: SubscriberFormPayload, profile: SubscriberProfile = '4g-lte-x310') => apiRequest<SubscriberOperationResponse>(`/api/subscribers?${profileQuery(profile)}`, { method: 'POST', body: JSON.stringify(payload) }),
  update: (imsi: string, payload: SubscriberFormPayload, profile: SubscriberProfile = '4g-lte-x310') => apiRequest<SubscriberOperationResponse>(`/api/subscribers/${encodeURIComponent(imsi)}?${profileQuery(profile)}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  clone: (imsi: string, payload: SubscriberClonePayload, profile: SubscriberProfile = '4g-lte-x310') => apiRequest<SubscriberOperationResponse>(`/api/subscribers/${encodeURIComponent(imsi)}/clone?${profileQuery(profile)}`, { method: 'POST', body: JSON.stringify(payload) }),
  delete: (imsi: string, confirm: boolean, profile: SubscriberProfile = '4g-lte-x310') => apiRequest<SubscriberOperationResponse>(`/api/subscribers/${encodeURIComponent(imsi)}?${profileQuery(profile)}`, { method: 'DELETE', body: JSON.stringify({ confirm }) }),
};
