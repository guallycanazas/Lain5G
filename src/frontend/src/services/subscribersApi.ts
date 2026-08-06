import { apiRequest } from './apiClient';
import type {
  SubscriberClonePayload,
  SubscriberConnectionStatus,
  SubscriberDetail,
  SubscriberFormPayload,
  SubscriberListResponse,
  SubscriberOperationResponse,
  SubscriberValidationResult,
} from '../types/subscriber';

export const subscribersApi = {
  connection: () => apiRequest<SubscriberConnectionStatus>('/api/subscribers/connection'),
  list: (params: { limit: number; offset: number; search?: string }) => {
    const query = new URLSearchParams({ limit: String(params.limit), offset: String(params.offset) });
    if (params.search?.trim()) query.set('search', params.search.trim());
    return apiRequest<SubscriberListResponse>(`/api/subscribers?${query.toString()}`);
  },
  detail: (imsi: string) => apiRequest<SubscriberDetail>(`/api/subscribers/${encodeURIComponent(imsi)}`),
  validate: (payload: SubscriberFormPayload) => apiRequest<SubscriberValidationResult>('/api/subscribers/validate', { method: 'POST', body: JSON.stringify(payload) }),
  create: (payload: SubscriberFormPayload) => apiRequest<SubscriberOperationResponse>('/api/subscribers', { method: 'POST', body: JSON.stringify(payload) }),
  update: (imsi: string, payload: SubscriberFormPayload) => apiRequest<SubscriberOperationResponse>(`/api/subscribers/${encodeURIComponent(imsi)}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  clone: (imsi: string, payload: SubscriberClonePayload) => apiRequest<SubscriberOperationResponse>(`/api/subscribers/${encodeURIComponent(imsi)}/clone`, { method: 'POST', body: JSON.stringify(payload) }),
  delete: (imsi: string, confirm: boolean) => apiRequest<SubscriberOperationResponse>(`/api/subscribers/${encodeURIComponent(imsi)}`, { method: 'DELETE', body: JSON.stringify({ confirm }) }),
};
