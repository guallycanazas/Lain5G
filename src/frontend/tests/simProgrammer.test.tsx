import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SimProgrammerPage } from '../src/pages/SimProgrammerPage';
import { jsonResponse, renderWithClient } from './testUtils';


const status = {
  available: true,
  programming_enabled: true,
  readers: ['USB Test Reader'],
  message: 'PC/SC bridge is ready.',
};

const supportedCard = {
  reader: 'USB Test Reader',
  detected: true,
  recognized: true,
  supported: true,
  card: 'sysmoUSIM-SJS1',
  message: 'Supported test USIM detected.',
};

const simulatedResult = {
  success: true,
  reader: 'USB Test Reader',
  card: 'sysmoUSIM-SJS1',
  imsi: '001011234567895',
  iccid: '8901234567890123455',
  verified_fields: ['ICCID', 'Ki', 'OPc', 'IMSI', 'MNC length'],
  message: 'SIM programming and read-back verification completed.',
};

describe('Physical SIM programmer page', () => {
  afterEach(() => vi.restoreAllMocks());

  it('keeps recognized SJA5 cards read-only', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.endsWith('/status')) return jsonResponse(status);
      if (url.endsWith('/inspect')) return jsonResponse({
        ...supportedCard,
        supported: false,
        card: 'sysmoISIM-SJA5',
        message: 'This model is identified but is not writable here.',
      });
      return jsonResponse({});
    }));
    renderWithClient(<SimProgrammerPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Detect card' }));

    expect(await screen.findByText('sysmoISIM-SJA5')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Review and write' })).toBeDisabled();
    expect(screen.getByText(/writing for this model is not enabled/i)).toBeInTheDocument();
  });

  it('requires a second confirmation before sending a write and displays read-back result', async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url.endsWith('/status')) return jsonResponse(status);
      if (url.endsWith('/inspect')) return jsonResponse(supportedCard);
      if (url.endsWith('/program')) return jsonResponse(simulatedResult);
      return jsonResponse({});
    }));
    const user = userEvent.setup();
    renderWithClient(<SimProgrammerPage />);

    await user.click(await screen.findByRole('button', { name: 'Detect card' }));
    await screen.findByText('sysmoUSIM-SJS1');
    await user.type(screen.getByLabelText('MCC'), '001');
    await user.type(screen.getByLabelText('MNC'), '01');
    await user.type(screen.getByLabelText('IMSI'), '001011234567895');
    await user.type(screen.getByLabelText('ICCID'), '8901234567890123455');
    await user.type(screen.getByLabelText('Ki'), '00112233445566778899aabbccddeeff');
    await user.type(screen.getByLabelText('OPc'), 'ffeeddccbbaa99887766554433221100');
    await user.type(screen.getByLabelText(/Card ADM1/), '76543210');
    await user.click(screen.getByLabelText(/I inserted the intended supported test USIM/i));
    await user.click(screen.getByRole('button', { name: 'Review and write' }));

    expect(screen.getByRole('dialog', { name: 'Write the physical SIM?' })).toBeInTheDocument();
    expect(calls.some(({ url }) => url.endsWith('/program'))).toBe(false);
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Write SIM' }));

    await waitFor(() => expect(calls.some(({ url }) => url.endsWith('/program'))).toBe(true));
    const request = calls.find(({ url }) => url.endsWith('/program'))!;
    const body = JSON.parse(String(request.init?.body));
    expect(body).toEqual(expect.objectContaining({
      reader_index: 0,
      mcc: '001',
      mnc: '01',
      imsi: '001011234567895',
      iccid: '8901234567890123455',
      adm: '76543210',
      confirm: true,
    }));
    expect(await screen.findByRole('heading', { name: 'Card verified' })).toBeInTheDocument();
    expect(screen.getByLabelText(/Card ADM1/)).toHaveValue('');
    expect(screen.getByText(/Read-back matched ICCID, Ki, OPc, IMSI, MNC length/)).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('00112233445566778899aabbccddeeff');
    expect(document.body.textContent).not.toContain('ffeeddccbbaa99887766554433221100');
  });
});
