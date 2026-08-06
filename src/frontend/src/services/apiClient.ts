import { ApiError, type ApiErrorResponse } from '../types/api';

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

export const API_BASE_URL = configuredBaseUrl || '';

export function buildApiPath(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(buildApiPath(path), {
    ...init,
    headers: {
      Accept: 'application/json',
      'Accept-Language': 'en',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  });

  const text = await response.text();
  const payload = text ? safeJson(text) : null;

  if (!response.ok) {
    throw toApiError(response.status, payload);
  }

  return payload as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function toApiError(status: number, payload: unknown): ApiError {
  const data = payload as ApiErrorResponse;
  if (typeof data?.detail === 'object' && data.detail !== null) {
    return new ApiError(data.detail.message || 'API error', status, data.detail.code, data.detail);
  }
  if (typeof data?.detail === 'string') {
    return new ApiError(data.detail, status, undefined, data);
  }
  return new ApiError('The request could not be completed', status, undefined, data);
}
