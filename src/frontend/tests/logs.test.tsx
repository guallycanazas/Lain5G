import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LogsPage } from '../src/pages/LogsPage';
import { deploymentStatus, jsonResponse, renderWithClient } from './testUtils';

describe('LogsPage', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('filters and fetches allow-listed scenario logs', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => url.endsWith('/api/deployments')
      ? jsonResponse([{ id: '5g-sa', name: '5G - UERANSIM Simulation', components: ['mongo', 'amf'] }])
      : url.includes('/status')
        ? jsonResponse({ ...deploymentStatus, containers: [] })
        : jsonResponse({ id: '5g-sa', container: 'amf', tail: 500, command: { ...deploymentStatus.command, stdout: 'INFO amf ready\nERROR amf failed' } })));
    renderWithClient(<LogsPage />);
    await screen.findByRole('option', { name: 'amf' });
    expect(screen.getByRole('heading', { name: '5G - UERANSIM Simulation · all services' })).toBeInTheDocument();
    await userEvent.selectOptions(await screen.findByLabelText('Service'), 'amf');
    await userEvent.selectOptions(screen.getByLabelText('Latest'), '500');
    await userEvent.selectOptions(screen.getByLabelText('Level'), 'error');
    await userEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(await screen.findByText('ERROR amf failed')).toBeInTheDocument();
    expect(screen.queryByText('INFO amf ready')).not.toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/deployments/5g-sa/logs?tail=500&container=amf', expect.any(Object)));
  });

  it('shows structured backend errors', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ detail: { code: 'DEPLOYMENT_LOGS_FAILED', message: 'Logs failed' } }, 500)));
    renderWithClient(<LogsPage />);
    expect(await screen.findByText('Backend error')).toBeInTheDocument();
  });

  it('explains how to restore logs when Docker access is missing', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => url.endsWith('/api/deployments')
      ? jsonResponse([{ id: '5g-sa', name: '5G - UERANSIM Simulation', components: ['mongo', 'amf'] }])
      : url.includes('/status')
        ? jsonResponse({ ...deploymentStatus, containers: [] })
        : jsonResponse({ detail: { code: 'DEPLOYMENT_LOGS_FAILED', message: 'Logs could not be collected.', stderr: 'failed to connect to the docker API at unix:///var/run/docker.sock' } }, 500)));
    renderWithClient(<LogsPage />);
    expect(await screen.findByText('Docker access unavailable')).toBeInTheDocument();
    expect(screen.getByText(/start it with \.\/lain5g app start --operations/i)).toBeInTheDocument();
  });
});
