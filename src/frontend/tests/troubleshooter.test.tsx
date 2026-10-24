import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { TroubleshooterPage } from '../src/pages/TroubleshooterPage';
import { jsonResponse, renderWithClient, validationReport } from './testUtils';

const deployment = {
  id: '5g-sa', name: '5G - UERANSIM Simulation', description: '5G standalone', path: 'deployments/5g-sa', status: 'stopped', mode: 'simulation',
  supported_actions: ['start', 'stop', 'validate'], validation_checks: ['nrf', 'ue_registration'], rf_capable: false, components: ['nrf', 'amf'],
};

describe('TroubleshooterPage', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('turns failed and untested profile checks into prioritized repair steps', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url === '/api/deployments') return jsonResponse([deployment]);
      if (url === '/api/validation/latest') return jsonResponse(validationReport);
      return jsonResponse({});
    }));
    renderWithClient(<TroubleshooterPage />, '/troubleshooter?scenario=5g-sa');

    expect(await screen.findByRole('heading', { name: 'Troubleshooter' })).toBeInTheDocument();
    expect(await screen.findByText('Problems to resolve')).toBeInTheDocument();
    expect(screen.getAllByText('Likely cause').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Suggested fix').length).toBeGreaterThan(0);
    expect(screen.getAllByRole('link', { name: /Inspect this profile’s logs/ })[0]).toHaveAttribute('href', '/logs?scenario=5g-sa');
    expect(screen.getByRole('button', { name: /Run full diagnosis/ })).toBeInTheDocument();
  });
});
