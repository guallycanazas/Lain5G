import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ScenarioDetailPage } from '../src/pages/ScenarioDetailPage';
import { jsonResponse, renderRoute } from './testUtils';

const profiles = [
  { id: '4g-lte-sim', name: '4G - srsRAN ZMQ Simulation', rf: false, failedCheck: 'mme', detail: 'container is not running' },
  { id: '5g-sa', name: '5G - UERANSIM Simulation', rf: false, failedCheck: 'nrf', detail: 'container is not running' },
  { id: '4g-lte-x310', name: '4G - Guarded LTE RF', rf: true, failedCheck: 'epc_services', detail: 'One or more required LTE core services are not running.' },
  { id: '5g-sa-x310', name: '5G - Guarded SA RF', rf: true, failedCheck: 'core_services', detail: 'One or more required 5G core services are not running.' },
  { id: '5g-nsa-x310', name: '5G NSA - Guarded EN-DC RF', rf: true, failedCheck: 'epc_services', detail: 'One or more required LTE core services are not running.' },
];

function mockProfile(profile: typeof profiles[number]) {
  const deployment = {
    id: profile.id, name: profile.name, description: 'Synthetic troubleshooting case', path: `deployments/${profile.id}`,
    status: 'stopped', mode: profile.rf ? 'rf-controlled' : 'simulation',
    supported_actions: profile.rf
      ? ['stop', 'status', 'logs', 'validate', 'hardware-check', 'preflight', 'start-core', 'start-rf', 'emergency-stop']
      : ['start', 'stop', 'restart', 'status', 'logs', 'validate'],
    validation_checks: [profile.failedCheck], rf_capable: profile.rf, components: ['mongo', profile.rf ? 'ran-x310' : 'ran'],
  };
  let remediated = false;
  const requests: Array<{ url: string; method: string }> = [];
  const checks = (status: 'FAIL' | 'PASS') => [{ id: profile.failedCheck, status, detail: status === 'FAIL' ? profile.detail : 'service is healthy' }];
  const report = (status: 'FAIL' | 'PASS') => ({
    run_id: `synthetic-${profile.id}`, scenario: profile.id, status, checked_at: '2026-10-24T16:00:00Z',
    validation: { [profile.failedCheck]: status }, checks: checks(status),
  });

  vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method || 'GET';
    requests.push({ url, method });
    if (url === '/api/deployments') return jsonResponse([deployment]);
    if (url === `/api/deployments/${profile.id}`) return jsonResponse(deployment);
    if (url === `/api/deployments/${profile.id}/status`) return jsonResponse({
      id: profile.id, status: 'stopped', containers: [], checked_at: '2026-10-24T16:00:00Z', output: '',
      command: { command: [], cwd: '.', exit_code: 0, stdout: '', stderr: '', started_at: '', finished_at: '', duration_ms: 0, timed_out: false, dry_run: false },
    });
    if (url.startsWith(`/api/preparation/profiles/${profile.id}?`)) return jsonResponse({ profile: profile.id, name: profile.name, rf_capable: profile.rf, core_only: url.includes('core_only=true'), ready: true, installed_count: 1, total_count: 1, images: [] });
    if (url.startsWith(`/api/runs?scenario=${profile.id}`)) return jsonResponse([{ run_id: `synthetic-${profile.id}`, scenario: profile.id, status: remediated ? 'PASS' : 'FAIL' }]);
    if (url === `/api/runs/synthetic-${profile.id}`) return jsonResponse({
      run_id: `synthetic-${profile.id}`, metadata: { scenario: profile.id, status: remediated ? 'PASS' : 'FAIL', started_at: '2026-10-24T16:00:00Z', finished_at: '2026-10-24T16:00:01Z' },
      validation: report(remediated ? 'PASS' : 'FAIL'), metrics: {}, logs: [],
    });
    if (url === `/api/deployments/${profile.id}/validate` && method === 'POST') return jsonResponse(report(remediated ? 'PASS' : 'FAIL'));
    if (url === `/api/deployments/${profile.id}/start-core` && method === 'POST') {
      remediated = true;
      return jsonResponse({ id: profile.id, action: 'start-core', status: 'running', message: 'Core started without RF' });
    }
    if (url === `/api/deployments/${profile.id}/start` && method === 'POST') {
      remediated = true;
      return jsonResponse({ id: profile.id, action: 'start', status: 'running', message: 'Simulation started' });
    }
    if (url.endsWith('/hardware-check') && method === 'POST') return jsonResponse({ id: profile.id, action: 'hardware-check', status: 'stopped', message: 'Hardware check completed' });
    if (url.endsWith('/preflight') && method === 'POST') return jsonResponse({ id: profile.id, action: 'preflight', status: 'stopped', message: 'Preflight completed' });
    return jsonResponse({});
  }));
  return { requests };
}

describe('profile troubleshooter', () => {
  it.each(profiles)('detects and safely resolves a synthetic core failure in $name', async (profile) => {
    const user = userEvent.setup();
    const { requests } = mockProfile(profile);
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, `/scenarios/${profile.id}`);

    await user.click(await screen.findByRole('tab', { name: 'troubleshooter' }));
    expect(await screen.findByRole('heading', { name: 'Recommended repair order' })).toBeInTheDocument();
    expect(screen.getByText('Likely cause')).toBeInTheDocument();
    expect(screen.getByText('Suggested fix')).toBeInTheDocument();
    expect(screen.getAllByText(profile.detail).length).toBeGreaterThan(0);

    if (profile.rf) {
      await user.click(screen.getByRole('button', { name: 'Start core and verify (no RF)' }));
      await waitFor(() => expect(requests).toContainEqual({ url: `/api/deployments/${profile.id}/start-core`, method: 'POST' }));
    } else {
      await user.click(screen.getByRole('button', { name: 'Start simulation and verify' }));
      const dialog = await screen.findByRole('dialog', { name: `Start ${profile.name}` });
      await user.click(within(dialog).getByRole('button', { name: 'Start full simulation' }));
      await waitFor(() => expect(requests).toContainEqual({ url: `/api/deployments/${profile.id}/start`, method: 'POST' }));
    }

    expect(await screen.findByRole('heading', { name: 'No failing checks detected' })).toBeInTheDocument();
    expect(requests).toContainEqual({ url: `/api/deployments/${profile.id}/validate`, method: 'POST' });
    expect(requests.some((request) => request.url.includes('/start-rf'))).toBe(false);
  });

  it.each([
    { ...profiles[2], failedCheck: 'uhd_fpga_compatible', detail: 'FPGA image incompatible with active UHD runtime' },
    { ...profiles[3], failedCheck: 'uhd_available', detail: 'RFNoC protocol mismatch between SW: 2.0 and HW: 1.0' },
    { ...profiles[4], failedCheck: 'rfnoc_initialization', detail: 'RFNoC protocol mismatch between SW: 2.0 and HW: 1.0' },
  ])('keeps hardware errors visible and offers a non-transmitting check for $name', async (profile) => {
    const user = userEvent.setup();
    const { requests } = mockProfile(profile);
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, `/scenarios/${profile.id}`);
    await user.click(await screen.findByRole('tab', { name: 'troubleshooter' }));

    expect(await screen.findByText(/UHD software and X310 FPGA use incompatible RFNoC protocol versions|FPGA image could not be confirmed compatible/i)).toBeInTheDocument();
    expect(screen.getByText(/install an FPGA image compatible with the exact UHD version|install the image matching the UHD version/i)).toBeInTheDocument();
    await user.click(within(screen.getByLabelText('Profile troubleshooter')).getByRole('button', { name: 'Hardware check' }));
    await waitFor(() => expect(requests).toContainEqual({ url: `/api/deployments/${profile.id}/hardware-check`, method: 'POST' }));
    expect(requests.some((request) => request.url.includes('/start-rf'))).toBe(false);
  });

  it('guides an Ethernet-link failure and keeps it failed until the physical path is fixed', async () => {
    const user = userEvent.setup();
    const profile = { ...profiles[2], failedCheck: 'ethernet_link', detail: 'No Ethernet link detected on X310 management path' };
    const { requests } = mockProfile(profile);
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, `/scenarios/${profile.id}`);
    await user.click(await screen.findByRole('tab', { name: 'troubleshooter' }));

    expect(await screen.findByText('The host-to-radio Ethernet path is missing or on an unexpected subnet.')).toBeInTheDocument();
    expect(screen.getByText('Check the cable/NIC, configure the documented radio subnet, and verify that no competing route uses the X310 address.')).toBeInTheDocument();
    await user.click(within(screen.getByLabelText('Profile troubleshooter')).getByRole('button', { name: 'Hardware check' }));
    await waitFor(() => expect(requests).toContainEqual({ url: `/api/deployments/${profile.id}/hardware-check`, method: 'POST' }));

    await user.click(screen.getByRole('button', { name: 'Run diagnosis' }));
    expect(await screen.findByText('No Ethernet link detected on X310 management path')).toBeInTheDocument();
    expect(screen.getByText('Check the cable/NIC, configure the documented radio subnet, and verify that no competing route uses the X310 address.')).toBeInTheDocument();
    expect(requests.some((request) => request.url.includes('/start-rf'))).toBe(false);
  });
});
