import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiRequest, buildApiPath } from '../src/services/apiClient';
import { jsonResponse } from './testUtils';

describe('apiClient', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('builds relative API paths by default', () => {
    expect(buildApiPath('/api/health')).toBe('/api/health');
  });

  it('handles successful JSON responses', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ status: 'ok' })));

    await expect(apiRequest('/api/health')).resolves.toEqual({ status: 'ok' });
    expect(fetch).toHaveBeenCalledWith('/api/health', expect.objectContaining({ headers: expect.objectContaining({ 'Accept-Language': 'en' }) }));
  });

  it('handles backend errors with structured detail', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ detail: { code: 'DEPLOYMENT_CONFLICT', message: 'Already running' } }, 409)));

    await expect(apiRequest('/api/deployments/5g-sa/start')).rejects.toMatchObject({ status: 409, code: 'DEPLOYMENT_CONFLICT' });
  });

  it('does not include secrets in requests by default', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ ok: true })));
    await apiRequest('/api/health');
    const [, init] = vi.mocked(fetch).mock.calls[0];

    expect(JSON.stringify(init)).not.toContain('SUBSCRIBER_KEY');
    expect(JSON.stringify(init)).not.toContain('OPC');
  });
});
