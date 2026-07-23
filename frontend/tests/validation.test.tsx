import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ValidationPage } from '../src/pages/ValidationPage';
import { jsonResponse, renderWithClient, validationReport } from './testUtils';

describe('ValidationPage', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('groups backend checks by operational layer and retains result states', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => url.includes('/validation/latest') ? jsonResponse(validationReport) : jsonResponse([])));
    renderWithClient(<ValidationPage />);
    expect(await screen.findByText('Infrastructure')).toBeInTheDocument();
    expect(screen.getByText('Core control plane')).toBeInTheDocument();
    expect(screen.getByText('MongoDB available')).toBeInTheDocument();
    expect(screen.getByText('FAIL')).toBeInTheDocument();
    expect(screen.getByText('WARNING')).toBeInTheDocument();
  });

  it('keeps validation failures visible to the operator', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => init?.method === 'POST' ? jsonResponse({ detail: { code: 'DEPLOYMENT_VALIDATE_FAILED', message: 'Validation failed' } }, 500) : jsonResponse(validationReport)));
    renderWithClient(<ValidationPage />);
    await userEvent.click(await screen.findByRole('button', { name: 'Run validation' }));
    expect(await screen.findByText('Backend error')).toBeInTheDocument();
  });
});
