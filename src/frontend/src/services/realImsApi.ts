import { apiRequest } from './apiClient';
import type {
  RealImsActionResponse,
  RealImsMode,
  RealImsProvisionPayload,
  RealImsReport,
  RealImsSubscriberList,
  RealImsStartPayload,
  RealImsStopPayload,
} from '../types/realIms';

const basePath = '/api/ims-real';

function post<T>(path: string, body: unknown) {
  return apiRequest<T>(`${basePath}${path}`, { method: 'POST', body: JSON.stringify(body) });
}

export const realImsApi = {
  preflight: (mode: RealImsMode) => apiRequest<RealImsReport>(`${basePath}/preflight?${new URLSearchParams({ mode })}`),
  status: (mode: RealImsMode, imsi: string) => {
    const params = new URLSearchParams({ mode });
    if (imsi) params.set('imsi', imsi);
    return apiRequest<RealImsReport>(`${basePath}/status?${params}`);
  },
  subscribers: (mode: RealImsMode) => apiRequest<RealImsSubscriberList>(`${basePath}/subscribers?${new URLSearchParams({ mode })}`),
  images: (execute: boolean) => post<RealImsActionResponse>('/images', { execute }),
  start: (payload: RealImsStartPayload) => post<RealImsActionResponse>('/start', payload),
  stop: (payload: RealImsStopPayload) => post<RealImsActionResponse>('/stop', payload),
  provision: (payload: RealImsProvisionPayload) => {
    const { mode, execute, mcc, mnc, sqn, ...subscriber } = payload;
    return post<RealImsActionResponse>('/provision', {
      mode,
      execute,
      mcc,
      mnc,
      subscriber: { ...subscriber, sqn: Number.parseInt(sqn, 16) },
    });
  },
};
