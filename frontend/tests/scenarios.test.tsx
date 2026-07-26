import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ScenarioDetailPage } from '../src/pages/ScenarioDetailPage';
import { ScenariosPage } from '../src/pages/ScenariosPage';
import { deploymentStatus, jsonResponse, renderRoute, renderWithClient } from './testUtils';

const scenarios = [
  { id: '5g-sa', name: '5G - UERANSIM Simulation', description: '5G standalone', path: 'deployments/5g-sa', status: 'stopped', mode: 'simulation', supported_actions: ['start', 'stop', 'restart', 'status', 'logs', 'validate'], validation_checks: ['ng_setup'], rf_capable: false, components: ['mongo', 'nrf', 'amf', 'gnb', 'ue'] },
  { id: '5g-vonr-sim', name: '5G SA + VoNR Signaling', description: '5G SA data and IMS signaling', path: 'deployments/5g-vonr', status: 'stopped', mode: 'simulation', supported_actions: ['start', 'stop', 'restart', 'status', 'logs', 'validate'], validation_checks: ['ng_setup', 'pdu_internet', 'pdu_ims', 'ims_dns', 'sip_register'], rf_capable: false, components: ['mongo', 'nrf', 'amf', 'gnb', 'ue', 'ims-database', 'pcscf', 'icscf', 'scscf', 'dns'] },
  { id: '4g-lte-sim', name: '4G - srsRAN ZMQ Simulation', description: 'srsENB and srsUE over ZMQ', path: 'deployments/4g-lte-sim', status: 'stopped', mode: 'simulation', supported_actions: ['start', 'stop', 'restart', 'status', 'logs', 'validate'], validation_checks: ['s1_setup', 'ue_registration'], rf_capable: false, components: ['mme', 'enb', 'ue'] },
  { id: '4g-lte-x310', name: '4G - Guarded VoLTE RF Preparation', description: 'Guarded SDR', path: 'deployments/4g-volte/x310', status: 'stopped', mode: 'rf-controlled', supported_actions: ['stop', 'status', 'logs', 'validate', 'hardware-check', 'preflight', 'start-core', 'start-rf', 'emergency-stop'], validation_checks: ['hardware_detected'], rf_capable: true, components: ['mongo', 'mme', 'enb-x310'], conditional_components: ['enb-x310'] },
  { id: '5g-sa-x310', name: '5G - Guarded VoNR RF Preparation', description: 'Guarded 5G SDR', path: 'deployments/5g-sa-x310', status: 'stopped', mode: 'rf-controlled', supported_actions: ['stop', 'status', 'logs', 'validate', 'hardware-check', 'preflight', 'start-core', 'start-rf', 'emergency-stop'], validation_checks: ['hardware_detected'], rf_capable: true, components: ['amf', 'gnb-x310'] },
];
const run = { run_id: 'run-5g', metadata: { scenario: '5g-sa', status: 'PASS', finished_at: '2026-07-10T13:36:33Z', git_commit: 'abc1234' }, validation: { status: 'PASS', checks: [{ id: 'pdu_session', status: 'PASS', detail: 'PDU session established' }] }, metrics: {}, logs: [], loaded_at: '2026-07-10T13:36:34Z' };
const rfProfiles: Record<string, any> = {
  '4g-lte-x310': { profile: '4g-lte-x310', radio: { device: 'x300', usrp_addr: '192.168.10.2', lte_band: 7, earfcn: 3150, bandwidth_mhz: 5, tx_gain: 20, rx_gain: 40 }, safety: { rf_allowed: false, environment: 'shielded', attenuation_db: 60, antenna_connected: false, shielded_environment: true, auto_stop: true, authorization_confirmed: true, maximum_duration_seconds: 600, operator_note: 'Authorized 4G RF test' } },
  '5g-sa-x310': { profile: '5g-sa-x310', radio: { device: 'x300', usrp_addr: '192.168.10.2', band: 78, dl_arfcn: 632628, bandwidth_mhz: 10, tx_gain: 20, rx_gain: 30 }, safety: { rf_allowed: false, environment: 'shielded', attenuation_db: 60, antenna_connected: false, shielded_environment: true, auto_stop: true, authorization_confirmed: true, maximum_duration_seconds: 600, operator_note: 'Authorized 5G RF test' } },
};

function stubScenarioFetch(extra?: (url: string, init?: RequestInit) => Promise<Response> | undefined) {
  vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
    const overridden = extra?.(url, init); if (overridden) return overridden;
    if (url.includes('/api/preparation/profiles/')) {
      const profile = url.split('/profiles/')[1].split('?')[0];
      return jsonResponse({ profile, name: profile, rf_capable: profile.includes('x310'), core_only: url.includes('core_only=true'), ready: true, installed_count: 3, total_count: 3, images: [] });
    }
    if (url === '/api/deployments') return jsonResponse(scenarios);
    const rfProfile = Object.values(rfProfiles).find((item) => url.includes(`/api/profiles/${item.profile}`));
    if (rfProfile && url.endsWith('/diff')) return jsonResponse({ profile: rfProfile.profile, files: [] });
    if (rfProfile) return jsonResponse(rfProfile);
    if (url.includes('/api/runs/run-5g')) return jsonResponse(run);
    if (url.includes('/api/runs?')) return jsonResponse([{ run_id: 'run-5g', scenario: '5g-sa', status: 'PASS' }]);
    const scenario = scenarios.find((item) => url === `/api/deployments/${item.id}` || url.startsWith(`/api/deployments/${item.id}/`));
    if (scenario && !url.includes('/status') && !url.includes('/logs') && init?.method !== 'POST') return jsonResponse(scenario);
    if (url.includes('/status')) return jsonResponse({ ...deploymentStatus, id: scenario?.id || '5g-sa' });
    if (url.includes('/logs')) return jsonResponse({ id: scenario?.id || '5g-sa', container: null, tail: 300, command: { ...deploymentStatus.command, stdout: 'log output' } });
    if (init?.method === 'POST') return jsonResponse({ id: scenario?.id || '5g-sa', action: 'ok', status: 'stopped', message: 'ok', command: deploymentStatus.command });
    return jsonResponse({});
  }));
}

describe('Scenario workspaces', () => {
  beforeEach(() => vi.restoreAllMocks());
  it('lists registered scenarios with modes and validation coverage', async () => {
    stubScenarioFetch(); renderWithClient(<ScenariosPage />);
    expect(await screen.findByText('5G - UERANSIM Simulation')).toBeInTheDocument();
    expect(screen.getByText('4G - srsRAN ZMQ Simulation')).toBeInTheDocument();
    expect(screen.getByText('5G SA + VoNR Signaling')).toBeInTheDocument();
    expect(screen.getByText('4G - Guarded VoLTE RF Preparation')).toBeInTheDocument();
    expect(screen.getByText('5G - Guarded VoNR RF Preparation')).toBeInTheDocument();
    expect(screen.getAllByText('Real hardware')).toHaveLength(2);
    expect(screen.getAllByText(/^\d+ checks$/)).toHaveLength(5);
  });
  it('keeps scenario commands and workspace tabs reachable', async () => {
    stubScenarioFetch(); renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/5g-sa');
    expect(await screen.findByRole('button', { name: 'Start lab' })).toBeInTheDocument();
    expect(screen.getByText('IMS, SIP, and VoNR calls')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'topology' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('tab', { name: 'validation' }));
    expect(await screen.findAllByText('PDU session established')).toHaveLength(2);
  });
  it('exposes a guarded X310 launch instead of unrestricted generic start', async () => {
    stubScenarioFetch(); renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/4g-lte-x310');
    expect(await screen.findByRole('button', { name: 'Hardware check' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Core only' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start X310 lab' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Emergency stop' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start' })).not.toBeInTheDocument();
  });
  it('shows expected services that are missing from a partial deployment', async () => {
    stubScenarioFetch((url) => url.includes('/api/deployments/4g-lte-x310/status') ? jsonResponse({
      ...deploymentStatus,
      id: '4g-lte-x310',
      status: 'partial',
      containers: [{ name: 'lain5g-lab-4g-lte-x310-mme', service: 'mme', status: 'Up 2 minutes', running: true }],
    }) : undefined);
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/4g-lte-x310');
    expect(await screen.findByText('1/2 required services running')).toBeInTheDocument();
    expect(screen.getByText('Expected by the profile but not running. Inspect its logs and dependencies.')).toBeInTheDocument();
    expect(screen.getAllByText('Not active')).toHaveLength(2);
    expect(screen.getByText('ENB-X310')).toBeInTheDocument();
    expect(screen.getByText('Standby')).toBeInTheDocument();
    expect(screen.getByText('Guarded RF service; starts only during an authorized, time-limited RF session.')).toBeInTheDocument();
  });
  it('summarizes simulation validation evidence and explains untested checks', async () => {
    stubScenarioFetch();
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/5g-sa');
    expect(await screen.findByText('Operational validation')).toBeInTheDocument();
    expect(await screen.findByText('1/2 checks passed')).toBeInTheDocument();
    expect(screen.getAllByText('PDU session established')).toHaveLength(2);
    expect(screen.getByText('No evidence was recorded for this check in the latest completed validation.')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Run validation' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/deployments/5g-sa/validate', expect.objectContaining({ method: 'POST' })));
  });
  it('requires the RF checklist and exact phrase before starting core plus RF', async () => {
    stubScenarioFetch(); renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/4g-lte-x310');
    await userEvent.click(await screen.findByRole('button', { name: 'Start X310 lab' }));
    expect(await screen.findByText('Band 7 · EARFCN 3150')).toBeInTheDocument();
    expect(screen.getByText('20 / 40 dB')).toBeInTheDocument();
    expect(screen.getByText('600 seconds')).toBeInTheDocument();
    const launch = screen.getByRole('button', { name: 'Start core + RF' });
    expect(launch).toBeDisabled();
    expect(screen.getByText('Mark all required checks (4 remaining).')).toBeInTheDocument();
    expect(screen.getByText('Type START 4G-LTE-X310 RF exactly in the confirmation field.')).toBeInTheDocument();
    for (const checkbox of screen.getAllByRole('checkbox')) await userEvent.click(checkbox);
    await userEvent.type(screen.getByLabelText(/Type START 4G-LTE-X310 RF/), 'START 4G-LTE-X310 RF');
    expect(screen.getByText('Ready to start.')).toBeInTheDocument();
    expect(launch).toBeEnabled();
    await userEvent.click(launch);
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/deployments/4g-lte-x310/start-rf', expect.objectContaining({ method: 'POST', body: expect.stringContaining('"execute":true') })));
  });
  it('shows applied 5G values instead of a hardcoded RF summary', async () => {
    stubScenarioFetch(); renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/5g-sa-x310');
    await userEvent.click(await screen.findByRole('button', { name: 'Start X310 lab' }));
    expect(await screen.findByText('n78 · ARFCN 632628')).toBeInTheDocument();
    expect(screen.getByText('10 MHz')).toBeInTheDocument();
    expect(screen.getByText('20 / 30 dB')).toBeInTheDocument();
  });
  it.each([
    ['4g-lte-x310', 'Start LTE eNB + X310'],
    ['5g-sa-x310', 'Start 5G gNB + X310'],
  ])('authorizes, validates, and applies the %s RF profile from the launch dialog', async (scenarioId, dialogTitle) => {
    let currentProfile = {
      ...rfProfiles[scenarioId],
      safety: {
        ...rfProfiles[scenarioId].safety,
        environment: 'cabled',
        shielded_environment: false,
        authorization_confirmed: false,
        operator_note: '',
      },
    };
    const baseUrl = `/api/profiles/${scenarioId}`;
    stubScenarioFetch((url, init) => {
      if (url === baseUrl && init?.method === 'PUT') {
        currentProfile = JSON.parse(String(init.body));
        return jsonResponse(currentProfile);
      }
      if (url === baseUrl && init?.method !== 'PUT') return jsonResponse(currentProfile);
      if (url === `${baseUrl}/validate`) return jsonResponse({ profile: scenarioId, valid: true, errors: [] });
      if (url === `${baseUrl}/apply`) return jsonResponse({ profile: scenarioId, modified_files: ['rf/safety-manifest.yaml'], backup: `.backups/${scenarioId}` });
      if (url === `${baseUrl}/diff`) return jsonResponse({ profile: scenarioId, files: [] });
      return undefined;
    });
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, `/scenarios/${scenarioId}`);
    await userEvent.click(await screen.findByRole('button', { name: 'Start X310 lab' }));
    expect(await screen.findByRole('dialog', { name: dialogTitle })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Authorize RF for this lab' })).toBeInTheDocument();
    const apply = screen.getByRole('button', { name: 'Authorize, validate & apply' });
    expect(apply).toBeDisabled();
    await userEvent.click(screen.getByRole('checkbox', { name: /I confirm this profile is authorized/ }));
    expect(apply).toBeEnabled();
    await userEvent.click(apply);
    expect(await screen.findByText('RF authorization validated and applied successfully.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'RF profile authorized and applied' })).toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(baseUrl, expect.objectContaining({
      method: 'PUT',
      body: expect.stringContaining('"authorization_confirmed":true'),
    })));
    expect(fetch).toHaveBeenCalledWith(`${baseUrl}/validate`, expect.objectContaining({ method: 'POST' }));
    expect(fetch).toHaveBeenCalledWith(`${baseUrl}/apply`, expect.objectContaining({ method: 'POST' }));
    expect(currentProfile.safety).toEqual(expect.objectContaining({ rf_allowed: false, environment: 'cabled', attenuation_db: 60, auto_stop: true, authorization_confirmed: true }));
    expect(screen.getByRole('button', { name: 'Start core + RF' })).toBeDisabled();
  });
  it('keeps RF blocked when backend profile validation rejects quick authorization', async () => {
    const profile = { ...rfProfiles['4g-lte-x310'], safety: { ...rfProfiles['4g-lte-x310'].safety, authorization_confirmed: false } };
    const baseUrl = '/api/profiles/4g-lte-x310';
    stubScenarioFetch((url, init) => {
      if (url === baseUrl && init?.method === 'PUT') return jsonResponse(JSON.parse(String(init.body)));
      if (url === baseUrl) return jsonResponse(profile);
      if (url === `${baseUrl}/validate`) return jsonResponse({ profile: '4g-lte-x310', valid: false, errors: ['RF authorization policy rejected this profile.'] });
      if (url === `${baseUrl}/diff`) return jsonResponse({ profile: '4g-lte-x310', files: [] });
      return undefined;
    });
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/4g-lte-x310');
    await userEvent.click(await screen.findByRole('button', { name: 'Start X310 lab' }));
    await userEvent.click(await screen.findByRole('checkbox', { name: /I confirm this profile is authorized/ }));
    await userEvent.click(screen.getByRole('button', { name: 'Authorize, validate & apply' }));
    expect(await screen.findByText('RF authorization policy rejected this profile.')).toBeInTheDocument();
    expect(screen.getByText('Authorization was not applied.')).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalledWith(`${baseUrl}/apply`, expect.anything());
    expect(screen.getByRole('button', { name: 'Start core + RF' })).toBeDisabled();
  });
  it('blocks RF launch while profile changes are not applied', async () => {
    stubScenarioFetch((url) => url.includes('/api/profiles/4g-lte-x310/diff') ? jsonResponse({ profile: '4g-lte-x310', files: [{ path: 'ran/enb.conf', changed: true, diff: 'pending' }] }) : undefined);
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/4g-lte-x310');
    await userEvent.click(await screen.findByRole('button', { name: 'Start X310 lab' }));
    expect(await screen.findByText('Configuration changes are pending.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start core + RF' })).toBeDisabled();
  });
  it.each([
    ['5g-sa', 'Start 5G - UERANSIM Simulation', '5GC + UERANSIM'],
    ['4g-lte-sim', 'Start 4G - srsRAN ZMQ Simulation', 'srsENB + srsUE simulation'],
    ['5g-vonr-sim', 'Start 5G SA + VoNR Signaling', '5G SA + VoNR simulation'],
  ])('provides a guided software launch for %s', async (scenarioId, title, flowLabel) => {
    stubScenarioFetch(); renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, `/scenarios/${scenarioId}`);
    await userEvent.click(await screen.findByRole('button', { name: 'Start lab' }));
    expect(screen.getByRole('dialog', { name: title })).toBeInTheDocument();
    expect(screen.getByText(flowLabel)).toBeInTheDocument();
    expect(screen.getByText('Software-only scenario')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Start full simulation' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(`/api/deployments/${scenarioId}/start`, expect.objectContaining({ method: 'POST' })));
  });
  it('preserves deployment conflict errors', async () => {
    stubScenarioFetch((url, init) => url.includes('/start') && init?.method === 'POST' ? jsonResponse({ detail: { code: 'DEPLOYMENT_CONFLICT', message: 'Another laboratory scenario is currently running.' } }, 409) : undefined);
    renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/4g-lte-sim');
    await userEvent.click(await screen.findByRole('button', { name: 'Start lab' }));
    await userEvent.click(screen.getByRole('button', { name: 'Start full simulation' }));
    expect(await screen.findByText('State conflict')).toBeInTheDocument();
  });
  it('fetches logs only from the selected scenario workspace', async () => {
    stubScenarioFetch(); renderRoute('/scenarios/:scenarioId', <ScenarioDetailPage />, '/scenarios/4g-lte-sim');
    await userEvent.click(await screen.findByRole('tab', { name: 'logs' }));
    await userEvent.click(screen.getByRole('button', { name: 'Fetch logs' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/deployments/4g-lte-sim/logs'), expect.anything()));
  });
});
