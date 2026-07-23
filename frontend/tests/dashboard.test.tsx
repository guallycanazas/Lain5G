import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardPage } from '../src/pages/DashboardPage';
import { deploymentStatus, healthResponse, jsonResponse, validationReport, renderWithClient } from './testUtils';

function stubDashboard(extra?: (url: string, init?: RequestInit) => Promise<Response> | undefined) {
  vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
    const overridden = extra?.(url, init); if (overridden) return overridden;
    if (url.includes('/api/health')) return jsonResponse(healthResponse);
    if (url.includes('/api/preparation/profiles/5g-sa')) return jsonResponse({ profile: '5g-sa', name: '5G SA simulation', rf_capable: false, core_only: false, ready: true, installed_count: 3, total_count: 3, images: [] });
    if (url.includes('/status')) return jsonResponse(deploymentStatus);
    if (url.includes('/validation/latest')) return jsonResponse(validationReport);
    if (url.includes('/api/runs')) return jsonResponse([]);
    return jsonResponse({});
  }));
}

describe('DashboardPage', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('shows operational summary from backend status and validation evidence', async () => {
    stubDashboard();
    renderWithClient(<DashboardPage />);
    expect(await screen.findByRole('heading', { name: 'Lain5G-Lab' })).toBeInTheDocument();
    expect(screen.getByText('Active services')).toBeInTheDocument();
    expect(screen.getByText('Validation pass rate')).toBeInTheDocument();
    expect(screen.getByText('Deployment stopped')).toBeInTheDocument();
  });

  it('starts deployment through the existing API contract', async () => {
    stubDashboard((url, init) => url.includes('/start') && init?.method === 'POST' ? jsonResponse({ id: '5g-sa', action: 'start', status: 'running', message: 'ok', command: deploymentStatus.command }) : undefined);
    renderWithClient(<DashboardPage />);
    await userEvent.click(await screen.findByRole('button', { name: 'Start' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/deployments/5g-sa/start', expect.objectContaining({ method: 'POST' })));
  });

  it('requires confirmation before stopping deployment', async () => {
    stubDashboard((url, init) => url.includes('/stop') && init?.method === 'POST' ? jsonResponse({ id: '5g-sa', action: 'stop', status: 'stopped', message: 'ok', command: deploymentStatus.command }) : undefined);
    renderWithClient(<DashboardPage />);
    await userEvent.click(await screen.findByRole('button', { name: 'Stop' }));
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Stop deployment' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/deployments/5g-sa/stop', expect.objectContaining({ method: 'POST' })));
  });
});
