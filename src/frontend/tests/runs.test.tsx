import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { RunDetailPage } from '../src/pages/RunDetailPage';
import { RunsPage } from '../src/pages/RunsPage';
import { jsonResponse, renderRoute, renderWithClient, runSummary, validationReport } from './testUtils';

describe('Run evidence', () => {
  beforeEach(() => vi.restoreAllMocks());
  it('renders run timeline entries with status', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => url.includes('/api/runs') ? jsonResponse([runSummary]) : jsonResponse([])));
    renderWithClient(<RunsPage />);
    expect(await screen.findByText('run-valid')).toBeInTheDocument();
    expect(screen.getByText('5g-sa', { exact: false })).toBeInTheDocument();
  });
  it('renders immutable run metadata and available artifacts', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ run_id: 'run-valid', metadata: { ...runSummary, status: 'PASS' }, validation: validationReport, metrics: { ping_ms: 11 }, logs: ['docker-compose.log'], loaded_at: '2026-07-10T02:00:00Z' })));
    renderRoute('/runs/:runId', <RunDetailPage />, '/runs/run-valid');
    expect(await screen.findByText('docker-compose.log')).toBeInTheDocument();
    expect(screen.getByText('Validation evidence')).toBeInTheDocument();
  });
});
