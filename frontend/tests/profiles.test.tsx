import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProfileConfigPage } from '../src/pages/ProfileConfigPage';
import { jsonResponse, renderRoute } from './testUtils';

const profile = { profile: '5g-sa', network: { mcc: '001', mnc: '01', tac: 1, dnn: 'internet', slice: { sst: 1, sd: '000001' } }, core: { amf_addr: '10.20.0.5', gnb_addr: '10.20.0.20' }, subscriber: { imsi: '001011234567895' }, safety: { rf_allowed: false } };
const x310 = { profile: '4g-lte-x310', network: { mcc: '001', mnc: '01', tac: 7, apn_internet: 'internet', apn_ims: 'ims' }, core: { mme_addr: '10.42.0.10' }, ran: { enb_bind_addr: '10.42.0.1' }, radio: { device: 'x300', usrp_addr: '192.168.10.2', lte_band: 7, earfcn: 3150, bandwidth_mhz: 5, tx_gain: 20, rx_gain: 30, clock_source: 'internal', time_source: 'internal' }, safety: { maximum_duration_seconds: 60, environment: 'cabled', attenuation_db: 60, antenna_connected: false, shielded_environment: false, auto_stop: true, authorization_confirmed: false, operator_note: '' } };
const x3105g = { profile: '5g-sa-x310', network: { mcc: '001', mnc: '01', tac: 1, dnn: 'internet', slice: { sst: 1, sd: '000001' } }, core: { amf_addr: '10.20.0.5', gnb_bind_addr: '0.0.0.0', n3_bind_addr: '0.0.0.0' }, radio: { device: 'x300', usrp_addr: '192.168.10.2', band: 78, dl_arfcn: 632628, bandwidth_mhz: 10, tx_gain: 20, rx_gain: 30, clock_source: 'internal', time_source: 'internal' }, safety: { maximum_duration_seconds: 600, environment: 'shielded', attenuation_db: 60, antenna_connected: true, shielded_environment: true, auto_stop: true, authorization_confirmed: true, operator_note: 'Authorized 5G test' } };
const nsa = { profile: '5g-nsa-x310', network: { mcc: '001', mnc: '01', tac: 7, apn_internet: 'internet' }, core: { mme_addr: '10.42.0.10' }, ran: { enb_bind_addr: '10.42.0.1' }, radio: { device: 'x300', usrp_addr: '192.168.10.2', lte_band: 7, earfcn: 3150, bandwidth_mhz: 10, nr_band: 3, nr_dl_arfcn: 368500, subcarrier_spacing_khz: 15, tx_gain: 20, rx_gain: 31.5, clock_source: 'internal', time_source: 'internal' }, safety: { maximum_duration_seconds: 600, environment: 'shielded', attenuation_db: 60, antenna_connected: true, nr_rf_path_connected: true, shielded_environment: true, auto_stop: true, authorization_confirmed: true, authorized_lab_frequencies: true, operator_note: 'Authorized NSA test' } };
const summaries = [{ profile: '5g-sa', rf_capable: false, rf_allowed: false }, { profile: '4g-lte-sim', rf_capable: false, rf_allowed: false }, { profile: '4g-lte-x310', rf_capable: true, rf_allowed: false }, { profile: '5g-sa-x310', rf_capable: true, rf_allowed: false }, { profile: '5g-nsa-x310', rf_capable: true, rf_allowed: false }];

describe('Deployment configuration', () => {
  beforeEach(() => vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
    if (url === '/api/profiles') return jsonResponse(summaries);
    if (url.includes('4g-lte-x310') && init?.method !== 'PUT') return jsonResponse(x310);
    if (url.includes('5g-sa-x310') && init?.method !== 'PUT') return jsonResponse(x3105g);
    if (url.includes('5g-nsa-x310') && init?.method !== 'PUT') return jsonResponse(nsa);
    if (url.includes('/validate')) return jsonResponse({ profile: '5g-sa', valid: true, errors: [] });
    if (url.includes('/diff')) return jsonResponse({ profile: '5g-sa', files: [{ path: 'deployments/5g-sa/.env', changed: true, diff: 'diff output' }] });
    if (url.includes('/apply')) return jsonResponse({ profile: '5g-sa', modified_files: ['deployments/5g-sa/.env'], backup: '.backups/config/5g-sa/run' });
    return jsonResponse(profile);
  })));
  afterEach(() => vi.restoreAllMocks());

  it('renders structured editable fields without a raw YAML editor', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    expect(await screen.findByRole('heading', { name: 'Simulated, no RF' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Guarded real RF' })).toBeInTheDocument();
    await userEvent.click(await screen.findByText('5g-sa'));
    expect(await screen.findByLabelText('MCC')).toHaveValue('001');
    expect(screen.getByLabelText('DNN')).toHaveValue('internet');
    expect(document.querySelector('textarea')).toBeNull();
  });

  it('validates, reviews and confirms apply after a dirty edit', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    const mcc = await screen.findByLabelText('MCC');
    await userEvent.clear(mcc); await userEvent.type(mcc, '999');
    await userEvent.click(screen.getByRole('button', { name: 'Compare changes' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/profiles/5g-sa/diff', expect.any(Object)));
    await userEvent.click(screen.getByRole('button', { name: 'Apply to scenario' }));
    await userEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Apply configuration' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/profiles/5g-sa/apply', expect.objectContaining({ method: 'POST' })));
  });

  it('shows guarded RF profile fields', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    await userEvent.click(await screen.findByText('4g-lte-x310'));
    expect(await screen.findByLabelText('Bandwidth MHz')).toHaveValue(5);
    expect(screen.getByLabelText('Attenuation dB')).toHaveValue(60);
    expect(screen.getByLabelText('RF authorization confirmed')).toHaveValue('false');
  });

  it('exposes the effective 5G X310 radio and safety fields', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    await userEvent.click(await screen.findByText('5g-sa-x310'));
    expect(await screen.findByLabelText('NR band')).toHaveValue(78);
    expect(screen.getByLabelText('DL ARFCN')).toHaveValue(632628);
    expect(screen.getByLabelText('USRP address')).toHaveValue('192.168.10.2');
    expect(screen.getByLabelText('Maximum duration')).toHaveValue(600);
    expect(screen.getByLabelText('Shielded environment')).toHaveValue('true');
  });

  it('exposes the dual-RAT NSA carrier, TX/RX and safety fields', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    await userEvent.click(await screen.findByText('5g-nsa-x310'));
    expect(await screen.findByLabelText('LTE anchor EARFCN')).toHaveValue(3150);
    expect(screen.getByLabelText('NR secondary band')).toHaveValue(3);
    expect(screen.getByLabelText('NR DL ARFCN')).toHaveValue(368500);
    expect(screen.getByLabelText('TX gain')).toHaveValue(20);
    expect(screen.getByLabelText('RX gain')).toHaveValue(31.5);
    expect(screen.getByLabelText('NR RF path connected')).toHaveValue('true');
    expect(screen.getByLabelText('All carrier frequencies authorized')).toHaveValue('true');
  });
});
