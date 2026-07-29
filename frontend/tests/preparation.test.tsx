import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PreparationPage } from '../src/pages/PreparationPage';
import { jsonResponse, renderRoute } from './testUtils';


const missingProfile = {
  profile: '5g-sa',
  name: '5G SA simulation',
  rf_capable: false,
  core_only: false,
  ready: false,
  installed_count: 2,
  total_count: 3,
  images: [
    { local_image: 'lain5g-lab/open5gs:local', source_image: 'gually/lain5g-open5gs:2.7.5-lain1', description: 'Core Open5GS 4G/5G', installed: true },
    { local_image: 'lain5g-lab/ueransim:local', source_image: 'gually/lain5g-ueransim:3.2.6-lain1', description: 'Simulated 5G gNB and UE', installed: false },
    { local_image: 'mongo@sha256:8b6d8f5bbedb25cb73517b65cf99f13aeb75ad5b157a56c479287a840bbad3ac', source_image: 'mongo@sha256:8b6d8f5bbedb25cb73517b65cf99f13aeb75ad5b157a56c479287a840bbad3ac', description: 'Official runtime image', installed: true },
  ],
};


describe('Preparation workspace', () => {
  afterEach(() => vi.restoreAllMocks());

  it('shows diagnostics and downloads missing images without starting deployments', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/preparation' && !init?.method) return jsonResponse({
        checked_at: '2026-07-16T14:00:00Z',
        ready: false,
        diagnostics: [{ id: 'docker', label: 'Docker Engine', status: 'PASS', detail: '28.3.2' }],
        profiles: [missingProfile],
      });
      if (url === '/api/preparation/pulls/active') return jsonResponse(null);
      if (url === '/api/preparation/profiles/5g-sa/pull' && init?.method === 'POST') return jsonResponse({
        job_id: 'pull-5g-sa',
        scope: '5g-sa',
        core_only: false,
        state: 'succeeded',
        images: [{ local_image: 'lain5g-lab/ueransim:local', source_image: 'gually/lain5g-ueransim:3.2.6-lain1', description: 'Simulated 5G gNB and UE', state: 'succeeded', error_code: null, error_message: null }],
        current_image: null,
        current_index: 1,
        completed_count: 1,
        total_count: 1,
        overall_percent: 100,
        pulled: ['gually/lain5g-ueransim:3.2.6-lain1'],
        created_at: '2026-07-16T14:01:00Z',
        started_at: '2026-07-16T14:01:00Z',
        finished_at: '2026-07-16T14:01:02Z',
        error_code: null,
        error_message: null,
      });
      return jsonResponse({});
    }));

    renderRoute('/preparation', <PreparationPage />);
    expect(await screen.findByText('Docker Engine')).toBeInTheDocument();
    expect(screen.getByText('gually/lain5g-ueransim:3.2.6-lain1')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Download missing' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/preparation/profiles/5g-sa/pull', expect.objectContaining({ method: 'POST', body: '{"core_only":false}' })));
    expect(await screen.findByText('Components ready')).toBeInTheDocument();
    expect(vi.mocked(fetch).mock.calls.some(([url]) => String(url).includes('/api/deployments/') && String(url).endsWith('/start'))).toBe(false);
  });

  it('requires confirmation before downloading all unique missing components', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/preparation' && !init?.method) return jsonResponse({ checked_at: '2026-07-16T14:00:00Z', ready: false, diagnostics: [], profiles: [missingProfile] });
      if (url === '/api/preparation/pulls/active') return jsonResponse(null);
      if (url === '/api/preparation/profiles/all/pull' && init?.method === 'POST') return jsonResponse({
        job_id: 'pull-all', scope: 'all', core_only: false, state: 'succeeded',
        images: [{ local_image: 'lain5g-lab/ueransim:local', source_image: 'gually/lain5g-ueransim:3.2.6-lain1', description: 'Simulated 5G gNB and UE', state: 'succeeded', error_code: null, error_message: null }],
        current_image: null, current_index: 1, completed_count: 1, total_count: 1, overall_percent: 100,
        pulled: ['gually/lain5g-ueransim:3.2.6-lain1'], created_at: '2026-07-16T14:00:00Z', started_at: '2026-07-16T14:00:00Z', finished_at: '2026-07-16T14:00:02Z', error_code: null, error_message: null,
      });
      return jsonResponse({});
    }));

    renderRoute('/preparation', <PreparationPage />);
    await userEvent.click(await screen.findByRole('button', { name: 'Download all missing (1)' }));
    expect(fetch).not.toHaveBeenCalledWith('/api/preparation/profiles/all/pull', expect.anything());
    await userEvent.click(screen.getByRole('button', { name: 'Download components' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/preparation/profiles/all/pull', expect.objectContaining({ method: 'POST' })));
    expect(await screen.findByText('Components ready')).toBeInTheDocument();
  });
});
