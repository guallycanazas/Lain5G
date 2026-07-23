import type { ReactElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PreferencesProvider } from '../src/preferences/PreferencesProvider';

export function renderWithClient(ui: ReactElement, route = '/') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <PreferencesProvider><QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider></PreferencesProvider>,
  );
}

export function renderRoute(path: string, element: ReactElement, route = path) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <PreferencesProvider><QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={path} element={element} />
          <Route path="/subscribers/:imsi" element={<div>subscriber-detail</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider></PreferencesProvider>,
  );
}

export function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }));
}

export const healthResponse = { status: 'ok', service: 'lain5g-lab-backend', version: '1.0.0-rc.1', dry_run: false };

export const deploymentStatus = {
  id: '5g-sa',
  status: 'stopped',
  containers: [
    { name: 'lain5g-lab-5g-sa-mongo', service: 'mongo', status: 'stopped', running: false },
    { name: 'lain5g-lab-5g-sa-amf', service: 'amf', status: 'stopped', running: false },
  ],
  checked_at: '2026-07-10T02:00:00Z',
  output: 'NAME IMAGE COMMAND SERVICE CREATED STATUS',
  command: {
    command: ['deployments/5g-sa/scripts/status.sh'],
    cwd: 'deployments/5g-sa',
    exit_code: 0,
    stdout: 'status output',
    stderr: '',
    started_at: '2026-07-10T02:00:00Z',
    finished_at: '2026-07-10T02:00:01Z',
    duration_ms: 1000,
    timed_out: false,
    dry_run: false,
  },
};

export const validationReport = {
  run_id: 'run-valid',
  scenario: '5g-sa',
  status: 'PASS',
  checked_at: '2026-07-10T02:00:00Z',
  validation: { mongo: 'PASS', nrf: 'PASS', amf: 'PASS', smf: 'PASS', upf: 'PASS', ausf: 'PASS', udm: 'PASS', udr: 'PASS', pcf: 'PASS', ng_connection: 'PASS', ue_registration: 'PASS', pdu_session: 'PASS', ue_tun: 'PASS', ue_ip: 'PASS', ping: 'PASS' },
  checks: [
    { id: 'mongo', status: 'PASS', detail: 'MongoDB responds to ping' },
    { id: 'nrf', status: 'FAIL', detail: 'container is not running' },
    { id: 'ue_ip', status: 'WARNING', detail: 'UE IP assigned: 10.45.0.2' },
    { id: 'ping', status: 'NOT_TESTED', detail: 'UE is not running' },
  ],
};

export const runSummary = {
  run_id: 'run-valid',
  scenario: '5g-sa',
  deployment_path: 'deployments/5g-sa',
  started_at: '2026-07-10T02:00:00Z',
  finished_at: '2026-07-10T02:01:00Z',
  status: 'stopped',
  git_commit: 'abc1234',
  validated_claims: ['UE registered'],
};

export const subscriberConnection = {
  status: 'connected',
  database: 'open5gs',
  collection: 'subscribers',
  server: 'mongo:27017',
  latency_ms: 4,
  checked_at: '2026-07-10T02:00:00Z',
};

export const subscriberDetail = {
  imsi: '001010000000001',
  msisdn: '51999999999',
  dnn: 'internet',
  sst: 1,
  sd: '000001',
  security: {
    k_configured: true,
    op_configured: false,
    opc_configured: true,
    amf: '8000',
    sqn: '************',
  },
  checked_at: '2026-07-10T02:00:00Z',
  note: 'A subscriber record in Open5GS does not establish that the UE authenticated successfully.',
};

export const subscriberList = {
  items: [subscriberDetail],
  total: 1,
  limit: 25,
  offset: 0,
};
