import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { RealImsPage } from '../src/pages/RealImsPage';
import { realImsApi } from '../src/services/realImsApi';
import { renderWithClient } from './testUtils';

vi.mock('../src/services/realImsApi', () => ({
  realImsApi: {
    preflight: vi.fn(),
    status: vi.fn(),
    subscribers: vi.fn(),
    images: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    provision: vi.fn(),
  },
}));

const report = {
  mode: '4g' as const,
  status: 'PASS',
  checks: [{ id: 'pcscf', status: 'PASS', message: 'P-CSCF is ready', evidence: 'pcscf:5060' }],
};

describe('Real IMS operator page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(realImsApi.preflight).mockResolvedValue(report);
    vi.mocked(realImsApi.status).mockResolvedValue(report);
    vi.mocked(realImsApi.subscribers).mockResolvedValue({ mode: '4g', count: 0, subscribers: [], secrets_redacted: true });
    vi.mocked(realImsApi.images).mockResolvedValue({ status: 'ok' });
    vi.mocked(realImsApi.start).mockResolvedValue({ status: 'ok' });
    vi.mocked(realImsApi.stop).mockResolvedValue({ status: 'ok' });
    vi.mocked(realImsApi.provision).mockResolvedValue({ status: 'ok' });
  });

  it('switches modes and refreshes first-party preflight and status reports', async () => {
    const user = userEvent.setup();
    renderWithClient(<RealImsPage />);

    expect(screen.getByRole('heading', { name: 'Real 4G/5G IMS operator' })).toBeInTheDocument();
    expect(screen.getByText(/separate from legacy SIP probes/i)).toBeInTheDocument();
    expect(await screen.findByText('P-CSCF is ready')).toBeInTheDocument();
    expect(realImsApi.preflight).toHaveBeenCalledWith('4g');

    await user.click(screen.getByRole('button', { name: '5G IMS' }));
    await waitFor(() => expect(realImsApi.preflight).toHaveBeenCalledWith('5g'));
    await user.type(screen.getByLabelText('Status IMSI'), '001010000000001');
    await user.click(screen.getByRole('button', { name: 'Refresh status' }));
    await waitFor(() => expect(realImsApi.status).toHaveBeenCalledWith('5g', '001010000000001'));
    expect(screen.queryByRole('button', { name: /RF start/i })).not.toBeInTheDocument();
  });

  it('requires confirmation for execution and clears secrets after successful provisioning', async () => {
    const user = userEvent.setup();
    renderWithClient(<RealImsPage />);
    await screen.findByText('P-CSCF is ready');

    await user.click(screen.getByRole('button', { name: 'Build images' }));
    expect(realImsApi.images).not.toHaveBeenCalled();
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Build images' }));
    await waitFor(() => expect(vi.mocked(realImsApi.images).mock.calls[0]?.[0]).toBe(true));

    fireEvent.change(screen.getByLabelText('IMSI'), { target: { value: '001010000000001' } });
    fireEvent.change(screen.getByLabelText('MSISDN'), { target: { value: '15551234567' } });
    fireEvent.change(screen.getByLabelText('Ki'), { target: { value: '00112233445566778899aabbccddeeff' } });
    fireEvent.change(screen.getByLabelText('OPc'), { target: { value: 'ffeeddccbbaa99887766554433221100' } });
    await user.click(screen.getByRole('button', { name: 'Provision subscriber' }));
    expect(realImsApi.provision).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Provision now' }));

    await waitFor(() => expect(vi.mocked(realImsApi.provision).mock.calls[0]?.[0]).toEqual(expect.objectContaining({
      mode: '4g', execute: true, mcc: '001', mnc: '01', imsi: '001010000000001', enabled: true,
    })));
    await waitFor(() => expect(screen.getByLabelText('Ki')).toHaveValue(''));
    expect(screen.getByLabelText('OPc')).toHaveValue('');
  });

  it('uses dry-run provisioning by default', async () => {
    const user = userEvent.setup();
    renderWithClient(<RealImsPage />);
    await screen.findByText('P-CSCF is ready');
    fireEvent.change(screen.getByLabelText('IMSI'), { target: { value: '001010000000001' } });
    fireEvent.change(screen.getByLabelText('MSISDN'), { target: { value: '15551234567' } });
    fireEvent.change(screen.getByLabelText('Ki'), { target: { value: '00112233445566778899aabbccddeeff' } });
    fireEvent.change(screen.getByLabelText('OPc'), { target: { value: 'ffeeddccbbaa99887766554433221100' } });
    await user.click(screen.getByRole('button', { name: 'Preview provisioning' }));

    await waitFor(() => expect(vi.mocked(realImsApi.provision).mock.calls[0]?.[0]).toEqual(expect.objectContaining({ execute: false })));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('shows correlated IMS subscribers without authentication secrets', async () => {
    vi.mocked(realImsApi.subscribers).mockResolvedValue({
      mode: '4g', count: 1, secrets_redacted: true,
      subscribers: [{
        imsi: '001010000000001', msisdn: '15551234567', impi: '001010000000001@ims.example',
        impu: 'sip:15551234567@ims.example', domain: 'ims.example', scscf: 'sip:scscf:6060', enabled: true,
        apns: ['internet', 'ims'], open5gs_present: true, pyhss_present: true,
      }],
    });

    renderWithClient(<RealImsPage />);

    expect(await screen.findByText('001010000000001')).toBeInTheDocument();
    expect(screen.getByText('sip:15551234567@ims.example')).toBeInTheDocument();
    expect(screen.queryByText('00112233445566778899AABBCCDDEEFF')).not.toBeInTheDocument();
  });
});

describe('real IMS API contract', () => {
  it('nests subscriber data and converts the hexadecimal SQN', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ status: 'DRY_RUN' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    }));

    await vi.importActual<typeof import('../src/services/realImsApi')>('../src/services/realImsApi').then(({ realImsApi: api }) => api.provision({
      mode: '4g', execute: false, mcc: '001', mnc: '01', imsi: '001010000000001', msisdn: '15551234567',
      ki: '00112233445566778899AABBCCDDEEFF', opc: 'FFEEDDCCBBAA99887766554433221100', amf: '8000',
      sqn: '00000000000A', apn_internet: 'internet', apn_ims: 'ims', enabled: true,
    }));

    const request = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(JSON.parse(String(request.body))).toEqual(expect.objectContaining({
      mode: '4g', execute: false, mcc: '001', mnc: '01',
      subscriber: expect.objectContaining({ imsi: '001010000000001', sqn: 10 }),
    }));
    fetchMock.mockRestore();
  });
});
