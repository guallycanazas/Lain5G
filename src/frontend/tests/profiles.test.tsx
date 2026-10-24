import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProfileConfigPage } from '../src/pages/ProfileConfigPage';
import { jsonResponse, renderRoute } from './testUtils';

const profile = { profile: '5g-sa', network: { mcc: '001', mnc: '01', tac: 1, dnn: 'internet', slice: { sst: 1, sd: '000001' } }, core: { amf_addr: '10.20.0.5', gnb_addr: '10.20.0.20' }, subscriber: { imsi: '001011234567895' }, safety: { rf_allowed: false } };
const x310 = { profile: '4g-lte-x310', network: { mcc: '001', mnc: '01', tac: 7, apn_internet: 'internet' }, core: { mme_addr: '10.42.0.10' }, ran: { enb_bind_addr: '10.42.0.1' }, subscriber: { imsi: '001011234567895' }, radio: { device: 'x300', usrp_addr: '192.168.10.2', lte_band: 7, earfcn: 3150, bandwidth_mhz: 5, tx_gain: 20, rx_gain: 30, clock_source: 'internal', time_source: 'internal' }, safety: { maximum_duration_seconds: 60, environment: 'cabled', attenuation_db: 60, antenna_connected: false, shielded_environment: false, auto_stop: true, authorization_confirmed: false, operator_note: '' } };
const x3105g = { profile: '5g-sa-x310', network: { mcc: '001', mnc: '01', tac: 1, dnn: 'internet', slice: { sst: 1, sd: '000001' } }, core: { amf_addr: '10.20.0.5', gnb_bind_addr: '0.0.0.0', n3_bind_addr: '0.0.0.0' }, radio: { device: 'x300', usrp_addr: '192.168.10.2', band: 78, dl_arfcn: 632628, bandwidth_mhz: 10, tx_gain: 20, rx_gain: 30, clock_source: 'internal', time_source: 'internal' }, safety: { maximum_duration_seconds: 600, environment: 'shielded', attenuation_db: 60, antenna_connected: true, shielded_environment: true, auto_stop: true, authorization_confirmed: true, operator_note: 'Authorized 5G test' } };
const nsa = { profile: '5g-nsa-x310', network: { mcc: '001', mnc: '01', tac: 7, apn_internet: 'internet' }, core: { mme_addr: '10.42.0.10' }, ran: { enb_bind_addr: '10.42.0.1' }, radio: { device: 'x300', usrp_addr: '192.168.10.2', lte_band: 7, earfcn: 3150, bandwidth_mhz: 10, nr_band: 3, nr_dl_arfcn: 368500, subcarrier_spacing_khz: 15, tx_gain: 20, rx_gain: 31.5, clock_source: 'internal', time_source: 'internal' }, safety: { maximum_duration_seconds: 600, environment: 'shielded', attenuation_db: 60, antenna_connected: true, nr_rf_path_connected: true, shielded_environment: true, auto_stop: true, authorization_confirmed: true, authorized_lab_frequencies: true, operator_note: 'Authorized NSA test' } };
const summaries = [{ profile: '5g-sa', rf_capable: false, rf_allowed: false }, { profile: '4g-lte-sim', rf_capable: false, rf_allowed: false }, { profile: '4g-lte-x310', rf_capable: true, rf_allowed: false }, { profile: '5g-sa-x310', rf_capable: true, rf_allowed: false }, { profile: '5g-nsa-x310', rf_capable: true, rf_allowed: false }];
const knownSubscriber = { imsi: '001010123456789', msisdn: '51987654321', dnn: 'internet', apns: ['internet', 'ims'], sst: 1, sd: '000001', security: { k_configured: true, op_configured: false, opc_configured: true } };

describe('Deployment configuration', () => {
  beforeEach(() => {
    const savedProfiles = new Map<string, any>();
    vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
    const profileId = url.match(/\/api\/profiles\/([^/?]+)/)?.[1] || '5g-sa';
    const fixtures: Record<string, any> = { '5g-sa': profile, '4g-lte-x310': x310, '5g-sa-x310': x3105g, '5g-nsa-x310': nsa, '4g-lte-sim': { profile: '4g-lte-sim', network: { mcc: '001', mnc: '01', tac: 7, apn_internet: 'internet' }, core: { mme_addr: '10.43.0.10' }, ran: { enb_bind_addr: '10.43.0.40', dl_earfcn: 3350, tx_gain: 80, rx_gain: 40 }, subscriber: { imsi: '001011234567895' }, safety: { rf_allowed: false } } };
    const selectedProfile = fixtures[profileId] || profile;
    if (url === '/api/profiles') return jsonResponse(summaries);
    if (url.startsWith('/api/subscribers?')) return jsonResponse({ items: [knownSubscriber], total: 1, limit: 100, offset: 0 });
    if (url.includes('/backups/latest')) return jsonResponse({ profile: profileId, backup: null });
    if (init?.method === 'PUT') { const saved = JSON.parse(String(init.body)); savedProfiles.set(profileId, saved); return jsonResponse(saved); }
    if (url.includes('/validate')) return jsonResponse({ profile: profileId, valid: true, errors: [] });
    if (url.includes('/diff')) return jsonResponse({ profile: profileId, files: [{ path: `deployments/${profileId}/.env`, changed: true, diff: 'diff output' }] });
    if (url.includes('/apply')) return jsonResponse({ profile: profileId, modified_files: [`deployments/${profileId}/.env`], backup: `.backups/config/${profileId}/run` });
    if (url.includes('/restore')) return jsonResponse({ profile: profileId, restored_files: [`deployments/${profileId}/.env`], backup: `.backups/config/${profileId}/run` });
    return jsonResponse(savedProfiles.get(profileId) || selectedProfile);
  }));
  });
  afterEach(() => vi.restoreAllMocks());

  it('renders structured editable fields without a raw YAML editor', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    expect(await screen.findByRole('heading', { name: 'Simulated, no RF' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Guarded real RF' })).toBeInTheDocument();
    expect(screen.getByText('Simulated 4G with srsENB + srsUE')).toBeInTheDocument();
    expect(screen.getByText('5G SA with X-Series radio')).toBeInTheDocument();
    await userEvent.click(await screen.findByText('5g-sa'));
    expect(await screen.findByLabelText('MCC')).toHaveValue('001');
    expect(screen.getByLabelText('DNN')).toHaveValue('internet');
    expect(document.querySelector('textarea')).toBeNull();
  });

  it('keeps edits local until Save, then validates, reviews and applies the saved profile', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    const mcc = await screen.findByLabelText('MCC');
    await userEvent.clear(mcc); await userEvent.type(mcc, '999');
    expect(screen.getByRole('button', { name: 'Compare changes' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Validate configuration' })).toBeDisabled();
    expect(fetch).not.toHaveBeenCalledWith('/api/profiles/5g-sa', expect.objectContaining({ method: 'PUT' }));
    await userEvent.click(screen.getByRole('button', { name: 'Save draft' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/profiles/5g-sa', expect.objectContaining({ method: 'PUT' })));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Compare changes' })).toBeEnabled());
    await userEvent.click(screen.getByRole('button', { name: 'Compare changes' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/profiles/5g-sa/diff', expect.any(Object)));
    await userEvent.click(screen.getByRole('button', { name: 'Apply to scenario' }));
    await userEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Apply configuration' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/profiles/5g-sa/apply', expect.objectContaining({ method: 'POST' })));
  });

  it('offers ready DNN presets and selects a subscriber from the live subscriber API', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    await userEvent.click(await screen.findByText('5g-sa'));
    await userEvent.selectOptions(await screen.findByRole('combobox', { name: 'DNN preset' }), 'custom');
    const dnn = screen.getByLabelText('DNN');
    await userEvent.clear(dnn); await userEvent.type(dnn, 'labnet');
    expect(dnn).toHaveValue('labnet');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Select existing subscriber' }), knownSubscriber.imsi);
    expect(screen.getByLabelText('IMSI')).toHaveValue(knownSubscriber.imsi);
    expect(fetch).toHaveBeenCalledWith(expect.stringMatching('/api/subscribers?'), expect.any(Object));
  });

  it('shows the latest backup only when one exists and requires confirmation to restore it', async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/profiles') return jsonResponse(summaries);
      if (url.startsWith('/api/subscribers?')) return jsonResponse({ items: [], total: 0, limit: 100, offset: 0 });
      if (url.includes('/backups/latest')) return jsonResponse({ profile: '5g-sa', backup: '.backups/config/5g-sa/20261024-120000' });
      if (url.includes('/restore')) return jsonResponse({ profile: '5g-sa', restored_files: ['deployments/5g-sa/.env'], backup: '.backups/config/5g-sa/20261024-120000' });
      return jsonResponse(profile);
    });
    vi.stubGlobal('fetch', fetchMock);
    renderRoute('/deployments', <ProfileConfigPage />);
    const restore = await screen.findByRole('button', { name: 'Restore latest backup' });
    expect(restore).toBeEnabled();
    await userEvent.click(restore);
    await userEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Restore backup' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/profiles/5g-sa/restore', expect.objectContaining({ method: 'POST' })));
  });

  it('shows guarded RF profile fields', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    await userEvent.click(await screen.findByText('4g-lte-x310'));
    expect(await screen.findByLabelText('Bandwidth MHz')).toHaveValue(5);
    expect(screen.getByLabelText('Attenuation dB')).toHaveValue(60);
    expect(screen.getByLabelText('RF authorization confirmed')).toHaveValue('false');
    expect(screen.queryByLabelText('IMS APN')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('IMS domain')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('MME address')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('eNB bind address')).not.toBeInTheDocument();
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

  it('exposes the LTE anchor and NR secondary-carrier configuration', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    await userEvent.click(await screen.findByText('5g-nsa-x310'));
    expect(await screen.findByLabelText('LTE anchor band')).toHaveValue(7);
    expect(screen.getByLabelText('NR secondary band')).toHaveValue(3);
    expect(screen.getByLabelText('NR DL ARFCN')).toHaveValue(368500);
    expect(screen.getByLabelText('NR RF path connected')).toHaveValue('true');
    expect(screen.getByLabelText('All carrier frequencies authorized')).toHaveValue('true');
  });

  it('keeps signaling profiles private and exposes the guarded NSA profile', async () => {
    renderRoute('/deployments', <ProfileConfigPage />);
    await screen.findByText('5g-sa');
    expect(screen.queryByText('4g-volte-sim')).not.toBeInTheDocument();
    expect(screen.queryByText('5g-vonr')).not.toBeInTheDocument();
    expect(screen.getByText('5g-nsa-x310')).toBeInTheDocument();
  });
});
