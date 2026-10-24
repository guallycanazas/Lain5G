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
    syncSubscriber: vi.fn(),
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
    vi.mocked(realImsApi.syncSubscriber).mockResolvedValue({ status: 'PASS' });
  });

  it('switches IMS modes and checks status for the selected identity', async () => {
    const user = userEvent.setup();
    renderWithClient(<RealImsPage />);

    expect(screen.getByRole('heading', { name: 'IMS synchronization' })).toBeInTheDocument();
    expect(screen.getByText(/same IMSI as the packet-core record/i)).toBeInTheDocument();
    await waitFor(() => expect(realImsApi.subscribers).toHaveBeenCalledWith('4g'));

    await user.click(screen.getByRole('button', { name: '5G' }));
    await waitFor(() => expect(realImsApi.subscribers).toHaveBeenCalledWith('5g'));
    await user.type(screen.getByLabelText('Optional IMSI'), '001010000000001');
    await user.click(screen.getByRole('button', { name: 'Check status' }));
    await waitFor(() => expect(realImsApi.status).toHaveBeenCalledWith('5g', '001010000000001'));
  });

  it('requires confirmation for execution and clears secrets after successful provisioning', async () => {
    const user = userEvent.setup();
    renderWithClient(<RealImsPage />);
    await waitFor(() => expect(realImsApi.subscribers).toHaveBeenCalledWith('4g'));

    fireEvent.change(screen.getByLabelText('IMSI'), { target: { value: '001010000000001' } });
    fireEvent.change(screen.getByLabelText('MSISDN'), { target: { value: '15551234567' } });
    fireEvent.change(screen.getByLabelText('Ki'), { target: { value: '00112233445566778899aabbccddeeff' } });
    fireEvent.change(screen.getByLabelText('OPc'), { target: { value: 'ffeeddccbbaa99887766554433221100' } });
    await user.click(screen.getByRole('button', { name: 'Add subscriber' }));
    expect(realImsApi.provision).not.toHaveBeenCalled();
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Add subscriber' }));

    await waitFor(() => expect(vi.mocked(realImsApi.provision).mock.calls[0]?.[0]).toEqual(expect.objectContaining({
      mode: '4g', execute: true, mcc: '001', mnc: '01', imsi: '001010000000001', enabled: true,
    })));
    await waitFor(() => expect(screen.getByLabelText('Ki')).toHaveValue(''));
    expect(screen.getByLabelText('OPc')).toHaveValue('');
  });

  it('uses dry-run provisioning by default', async () => {
    const user = userEvent.setup();
    renderWithClient(<RealImsPage />);
    await waitFor(() => expect(realImsApi.subscribers).toHaveBeenCalledWith('4g'));
    fireEvent.change(screen.getByLabelText('IMSI'), { target: { value: '001010000000001' } });
    fireEvent.change(screen.getByLabelText('MSISDN'), { target: { value: '15551234567' } });
    fireEvent.change(screen.getByLabelText('Ki'), { target: { value: '00112233445566778899aabbccddeeff' } });
    fireEvent.change(screen.getByLabelText('OPc'), { target: { value: 'ffeeddccbbaa99887766554433221100' } });
    await user.click(screen.getByRole('button', { name: 'Preview' }));

    await waitFor(() => expect(vi.mocked(realImsApi.provision).mock.calls[0]?.[0]).toEqual(expect.objectContaining({ execute: false })));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('starts the selected IMS services only after confirmation', async () => {
    const user = userEvent.setup();
    renderWithClient(<RealImsPage />);
    await waitFor(() => expect(realImsApi.subscribers).toHaveBeenCalledWith('4g'));
    await user.click(screen.getByRole('button', { name: '5G' }));
    await user.click(screen.getByRole('button', { name: 'Start IMS services' }));
    expect(realImsApi.start).not.toHaveBeenCalled();
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Start IMS services' }));
    await waitFor(() => expect(vi.mocked(realImsApi.start).mock.calls[0]?.[0]).toEqual({ mode: '5g', execute: true, mcc: '001', mnc: '01' }));
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

  it('syncs an existing identity to the other IMS mode without asking for its keys again', async () => {
    const user = userEvent.setup();
    vi.mocked(realImsApi.subscribers).mockResolvedValue({
      mode: '4g', count: 1, secrets_redacted: true,
      subscribers: [{
        imsi: '001010000000001', msisdn: '15551234567', impi: 'impi', impu: 'impu', domain: 'ims.example',
        scscf: null, enabled: true, apns: ['internet', 'ims'], open5gs_present: true, pyhss_present: true,
      }],
    });
    renderWithClient(<RealImsPage />);
    await user.click(await screen.findByRole('button', { name: 'Sync to 5G' }));
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Sync to 5G IMS' }));
    await waitFor(() => expect(vi.mocked(realImsApi.syncSubscriber).mock.calls[0]?.[0]).toEqual({
      source_mode: '4g', target_mode: '5g', mcc: '001', mnc: '01', imsi: '001010000000001',
    }));
    expect(await screen.findByRole('status')).toHaveTextContent(/synchronized from 4G IMS to 5G IMS/i);
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
