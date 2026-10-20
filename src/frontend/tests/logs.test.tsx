import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LogsPage } from '../src/pages/LogsPage';
import { deploymentStatus, jsonResponse, renderWithClient } from './testUtils';

describe('LogsPage', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('filters and fetches allow-listed scenario logs', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => url === '/api/deployments'
      ? jsonResponse([{ id: '5g-sa', name: 'Simulated 5G with UERANSIM', components: ['amf'] }])
      : url.includes('/status') ? jsonResponse(deploymentStatus) : jsonResponse({ id: '5g-sa', container: 'amf', tail: 500, command: { ...deploymentStatus.command, stdout: 'INFO amf ready\nERROR amf failed' } })));
    renderWithClient(<LogsPage />);
    await screen.findByRole('option', { name: 'amf' });
    await userEvent.selectOptions(await screen.findByLabelText('Service'), 'amf');
    await userEvent.selectOptions(screen.getByLabelText('Tail'), '500');
    await userEvent.selectOptions(screen.getByLabelText('Severity'), 'error');
    await userEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(await screen.findAllByText('ERROR amf failed')).not.toHaveLength(0);
    expect(screen.queryByText('INFO amf ready')).not.toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/deployments/5g-sa/logs?tail=500&container=amf', expect.any(Object)));
  });

  it('shows structured backend errors', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ detail: { code: 'DEPLOYMENT_LOGS_FAILED', message: 'Logs failed' } }, 500)));
    renderWithClient(<LogsPage />);
    expect(await screen.findByText('Backend error')).toBeInTheDocument();
  });
});
