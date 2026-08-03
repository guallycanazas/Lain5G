import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link } from 'react-router';
import { AlertTriangle, CheckCircle2, Download, RadioTower, ShieldCheck, Timer, X } from 'lucide-react';
import type { RfStartPayload } from '../types/deployment';
import type { ComponentImageStatus, ComponentPullJob } from '../types/preparation';
import { profilesApi } from '../services/profilesApi';
import { ComponentPullProgress } from './ComponentPullProgress';

const acknowledgementLabels = {
  legal_authorization_valid: 'Legal and local authorization remains valid.',
  isolation_and_attenuation_verified: 'Shielding, cabling, and attenuation were physically verified.',
  channel_and_gain_reviewed: 'Channel, bandwidth, and gain match the approved plan.',
  emergency_stop_accessible: 'Emergency stop remains accessible for the entire session.',
};

type RfEnvironment = 'cabled' | 'shielded';

export function RfStartDialog({ scenarioId, open, loading, missingImages, pullJob, onCancel, onConfirm }: { scenarioId: string; open: boolean; loading: boolean; missingImages: ComponentImageStatus[]; pullJob?: ComponentPullJob; onCancel: () => void; onConfirm: (payload: RfStartPayload) => void }) {
  const [duration, setDuration] = useState(60);
  const [note, setNote] = useState('Controlled RF session from OpenLain5G');
  const [phrase, setPhrase] = useState('');
  const [authorizationSelected, setAuthorizationSelected] = useState(false);
  const [environment, setEnvironment] = useState<RfEnvironment>('cabled');
  const [attenuation, setAttenuation] = useState(60);
  const [antennaConnected, setAntennaConnected] = useState(false);
  const [nrPathConnected, setNrPathConnected] = useState(false);
  const [frequenciesAuthorized, setFrequenciesAuthorized] = useState(false);
  const [acknowledgements, setAcknowledgements] = useState<Record<keyof RfStartPayload['acknowledgements'], boolean>>({ legal_authorization_valid: false, isolation_and_attenuation_verified: false, channel_and_gain_reviewed: false, emergency_stop_accessible: false });
  const previousMissingCount = useRef(missingImages.length);
  const profile = useQuery({ queryKey: ['profile', scenarioId], queryFn: () => profilesApi.detail(scenarioId), enabled: open });
  const diff = useQuery({ queryKey: ['profile-diff', scenarioId], queryFn: () => profilesApi.diff(scenarioId), enabled: open });
  const expectedPhrase = `START ${scenarioId.toUpperCase()} RF`;
  const is5gSa = scenarioId === '5g-sa-x310';
  const is5gNsa = scenarioId === '5g-nsa-x310';
  const is5g = is5gSa || is5gNsa;
  const config = profile.data;
  const radio = config?.radio || {};
  const safety = config?.safety || {};
  const maximumDuration = Number(safety.maximum_duration_seconds) || 60;
  const configuredAttenuation = Number(safety.attenuation_db);
  const pendingChanges = Boolean(diff.data?.files?.some((file) => file.changed));
  const authorizationConfigured = Boolean(
    config
    && safety.rf_allowed === false
    && safety.authorization_confirmed === true
    && safety.auto_stop === true
    && String(safety.operator_note || '').trim()
    && Number.isInteger(maximumDuration)
    && maximumDuration >= 1
    && maximumDuration <= 600
    && Number.isInteger(configuredAttenuation)
    && configuredAttenuation >= (safety.environment === 'cabled' ? 30 : 0)
    && configuredAttenuation <= 120
    && (safety.environment === 'cabled' || (safety.environment === 'shielded' && safety.shielded_environment === true))
    && !(safety.antenna_connected === true && safety.shielded_environment !== true)
    && (!is5gNsa || (safety.nr_rf_path_connected === true && safety.authorized_lab_frequencies === true)),
  );
  const configurationReady = Boolean(config && diff.data && !pendingChanges && authorizationConfigured);
  const needsAuthorizationSetup = Boolean(config && (!authorizationConfigured || pendingChanges));
  const authorizationFormValid = Boolean(
    authorizationSelected
    && note.trim().length >= 3
    && Number.isInteger(attenuation)
    && attenuation >= (environment === 'cabled' ? 30 : 0)
    && attenuation <= 120
    && (!is5gNsa || (nrPathConnected && frequenciesAuthorized)),
  );
  const remainingChecks = Object.values(acknowledgements).filter((checked) => !checked).length;
  const launchBlockers: string[] = [];
  if (profile.isLoading || diff.isLoading) launchBlockers.push('Wait for the effective RF configuration to load.');
  else if (profile.error || diff.error) launchBlockers.push('Resolve the RF configuration error.');
  else {
    if (pendingChanges) launchBlockers.push('Apply the pending profile changes.');
    if (!authorizationConfigured) launchBlockers.push('Authorize and apply the RF profile.');
  }
  if (duration < 1 || duration > maximumDuration) launchBlockers.push(`Use a duration between 1 and ${maximumDuration} seconds.`);
  if (note.trim().length < 3) launchBlockers.push('Enter an operator purpose of at least 3 characters.');
  if (remainingChecks) launchBlockers.push(`Mark all required checks (${remainingChecks} remaining).`);
  if (phrase !== expectedPhrase) launchBlockers.push(`Type ${expectedPhrase} exactly in the confirmation field.`);
  const valid = configurationReady && duration >= 1 && duration <= maximumDuration && phrase === expectedPhrase && note.trim().length >= 3 && Object.values(acknowledgements).every(Boolean);
  const authorizeRf = useMutation({
    mutationFn: async () => {
      if (!config) throw new Error('The RF profile is not loaded.');
      const updatedConfig = {
        ...config,
        safety: {
          ...safety,
          rf_allowed: false,
          environment,
          attenuation_db: attenuation,
          antenna_connected: environment === 'shielded' && antennaConnected,
          shielded_environment: environment === 'shielded',
          auto_stop: true,
          authorization_confirmed: true,
          operator_note: note.trim(),
          ...(is5gNsa ? { nr_rf_path_connected: nrPathConnected, authorized_lab_frequencies: frequenciesAuthorized } : {}),
        },
      };
      await profilesApi.update(scenarioId, updatedConfig);
      const validation = await profilesApi.validate(scenarioId);
      if (!validation.valid) throw new Error(validation.errors.join(' ') || 'The RF profile failed validation.');
      return profilesApi.apply(scenarioId);
    },
    onSuccess: async () => {
      await Promise.all([profile.refetch(), diff.refetch()]);
    },
  });
  const authorizationError = authorizeRf.error instanceof Error ? authorizeRf.error.message : 'The RF authorization could not be applied.';
  const radioSummary = is5gNsa
    ? `LTE B${radio.lte_band ?? '—'} + NR n${radio.nr_band ?? '—'} · ARFCN ${radio.nr_dl_arfcn ?? '—'}`
    : is5gSa
      ? `n${radio.band ?? '—'} · ARFCN ${radio.dl_arfcn ?? '—'}`
      : `Band ${radio.lte_band ?? '—'} · EARFCN ${radio.earfcn ?? '—'}`;
  const radioTitle = is5gNsa ? '5G NSA RAN' : is5g ? '5G gNB' : 'LTE eNB';

  useEffect(() => {
    if (!open) return;
    setPhrase('');
    authorizeRf.reset();
    setAcknowledgements({ legal_authorization_valid: false, isolation_and_attenuation_verified: false, channel_and_gain_reviewed: false, emergency_stop_accessible: false });
  }, [open, scenarioId]);

  useEffect(() => {
    if (!open || !profile.data) return;
    const limit = Number(profile.data.safety?.maximum_duration_seconds) || 60;
    setDuration(Math.min(60, limit));
    setNote(profile.data.safety?.operator_note || 'Controlled RF session from OpenLain5G');
    const configuredEnvironment = profile.data.safety?.environment === 'shielded' ? 'shielded' : 'cabled';
    setEnvironment(configuredEnvironment);
    setAttenuation(Number(profile.data.safety?.attenuation_db) || 60);
    setAntennaConnected(profile.data.safety?.antenna_connected === true);
    setNrPathConnected(profile.data.safety?.nr_rf_path_connected === true);
    setFrequenciesAuthorized(profile.data.safety?.authorized_lab_frequencies === true);
    setAuthorizationSelected(profile.data.safety?.authorization_confirmed === true);
  }, [open, profile.data, scenarioId]);

  useEffect(() => {
    if (open && previousMissingCount.current > 0 && missingImages.length === 0) {
      setPhrase('');
      setAcknowledgements({ legal_authorization_valid: false, isolation_and_attenuation_verified: false, channel_and_gain_reviewed: false, emergency_stop_accessible: false });
    }
    previousMissingCount.current = missingImages.length;
  }, [missingImages.length, open]);

  if (!open) return null;
  return <div className="dialog-backdrop rf-dialog-backdrop" role="presentation">
    <section className="rf-start-dialog" role="dialog" aria-modal="true" aria-labelledby="rf-start-title">
      <header><div className="rf-dialog-title"><span><RadioTower size={21} /></span><div><small>GUARDED RF SESSION</small><h2 id="rf-start-title">Start {radioTitle} + X310</h2></div></div><button className="dialog-close" type="button" onClick={onCancel} aria-label="Close"><X size={18} /></button></header>
      <div className="rf-danger-banner"><AlertTriangle size={18} /><div><strong>This action transmits RF energy.</strong><span>The core starts first and the SDR container stops automatically.</span></div></div>
      {profile.isLoading || diff.isLoading ? <div className="rf-config-state">Loading effective RF configuration...</div> : null}
      {profile.error || diff.error ? <div className="rf-config-state error">The RF configuration could not be verified. Start remains blocked.</div> : null}
      {pendingChanges ? <div className="rf-config-state warning"><strong>Configuration changes are pending.</strong><span>Validate and apply the RF authorization below, or use <Link to="/deployments" onClick={onCancel}>Deployments</Link> for advanced editing.</span></div> : null}
      {missingImages.length ? <div className="warning-box"><strong>{missingImages.length} component{missingImages.length === 1 ? '' : 's'} missing</strong><ul>{missingImages.map((image) => <li key={image.local_image}>{image.description}</li>)}</ul><p>Download these components first. RF start requires a second explicit click with the current safety checks after the download completes.</p></div> : null}
      {pullJob ? <ComponentPullProgress job={pullJob} /> : null}
      <div className="rf-session-summary">
        <div><span>Radio</span><strong>{radioSummary}</strong></div>
        <div><span>Bandwidth</span><strong>{radio.bandwidth_mhz ?? '—'} MHz</strong></div>
        <div><span>TX / RX gain</span><strong>{radio.tx_gain ?? '—'} / {radio.rx_gain ?? '—'} dB</strong></div>
        <div><span>USRP</span><strong>{radio.usrp_addr || '—'} · {radio.device || '—'}</strong></div>
        <div><span>Environment</span><strong>{safety.environment || '—'} · {safety.attenuation_db ?? '—'} dB</strong></div>
        <div><span>Auto-stop limit</span><strong>{maximumDuration} seconds</strong></div>
      </div>
      <div className="rf-profile-link">Values come from the applied <code>{scenarioId}</code> profile. <Link to="/deployments" onClick={onCancel}>Edit configuration</Link></div>
      <div className="rf-form-grid"><label><Timer size={14} />Requested duration (seconds)<input type="number" min={1} max={maximumDuration} value={duration} onChange={(event) => setDuration(Number(event.target.value))} /></label><label>Operator purpose<input value={note} maxLength={240} onChange={(event) => setNote(event.target.value)} /></label></div>
      {config ? <section className={`rf-authorization-panel ${needsAuthorizationSetup ? 'required' : 'ready'}`} aria-labelledby="rf-authorization-title">
        <div className="rf-authorization-heading"><div><span className="rf-authorization-icon">{needsAuthorizationSetup ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}</span><div><small>PROFILE GATE</small><h3 id="rf-authorization-title">{needsAuthorizationSetup ? 'Authorize RF for this lab' : 'RF profile authorized and applied'}</h3></div></div><strong>{needsAuthorizationSetup ? 'Action required' : 'Ready'}</strong></div>
        {needsAuthorizationSetup ? <div className="rf-authorization-body">
          <p>Select the physical setup. Backend validation remains authoritative and <code>rf_allowed</code> stays false in the central profile.</p>
          <div className="rf-environment-options">
            <label className={environment === 'cabled' ? 'selected' : ''}><input type="radio" name="rf-environment" value="cabled" checked={environment === 'cabled'} disabled={authorizeRf.isPending} onChange={() => { setEnvironment('cabled'); setAntennaConnected(false); }} /><span><strong>Cabled + attenuated</strong><small>No antenna; requires at least 30 dB attenuation.</small></span></label>
            <label className={environment === 'shielded' ? 'selected' : ''}><input type="radio" name="rf-environment" value="shielded" checked={environment === 'shielded'} disabled={authorizeRf.isPending} onChange={() => setEnvironment('shielded')} /><span><strong>Shielded environment</strong><small>For a verified RF enclosure or chamber.</small></span></label>
          </div>
          <div className="rf-authorization-fields"><label>Attenuation (dB)<input type="number" min={environment === 'cabled' ? 30 : 0} max={120} value={attenuation} disabled={authorizeRf.isPending} onChange={(event) => setAttenuation(Number(event.target.value))} /></label>{environment === 'shielded' ? <label className="rf-inline-check"><input type="checkbox" checked={antennaConnected} disabled={authorizeRf.isPending} onChange={(event) => setAntennaConnected(event.target.checked)} /><span>Antenna connected inside shielding</span></label> : null}</div>
          {is5gNsa ? <div className="rf-nsa-checks"><label><input type="checkbox" checked={nrPathConnected} disabled={authorizeRf.isPending} onChange={(event) => setNrPathConnected(event.target.checked)} /><span>NR RF path is physically connected.</span></label><label><input type="checkbox" checked={frequenciesAuthorized} disabled={authorizeRf.isPending} onChange={(event) => setFrequenciesAuthorized(event.target.checked)} /><span>LTE and NR laboratory frequencies are authorized.</span></label></div> : null}
          <label className="rf-authorization-confirm"><input type="checkbox" checked={authorizationSelected} disabled={authorizeRf.isPending} onChange={(event) => setAuthorizationSelected(event.target.checked)} /><span>I confirm this profile is authorized for RF transmission in the selected laboratory environment.</span></label>
          <div className="rf-authorization-action"><span>Session checks and the exact launch phrase are still required every time.</span><button type="button" disabled={!authorizationFormValid || authorizeRf.isPending} onClick={() => authorizeRf.mutate()}>{authorizeRf.isPending ? 'Validating and applying…' : 'Authorize, validate & apply'}</button></div>
        </div> : <p className="rf-authorization-ready"><CheckCircle2 size={15} />Applied files match the authorized profile. Complete the per-session checks below to continue.</p>}
        {authorizeRf.isError ? <div className="rf-authorization-result error"><strong>Authorization was not applied.</strong><span>{authorizationError}</span></div> : null}
        {authorizeRf.isSuccess && !needsAuthorizationSetup ? <div className="rf-authorization-result success">RF authorization validated and applied successfully.</div> : null}
      </section> : null}
      <fieldset className="rf-acknowledgements"><legend><ShieldCheck size={15} />Required checks</legend>{Object.entries(acknowledgementLabels).map(([key, label]) => <label key={key}><input type="checkbox" checked={acknowledgements[key as keyof typeof acknowledgements]} onChange={(event) => setAcknowledgements((current) => ({ ...current, [key]: event.target.checked }))} /><span>{label}</span></label>)}</fieldset>
      <label className="rf-confirmation">Type <code>{expectedPhrase}</code> to authorize this session<input autoComplete="off" value={phrase} onChange={(event) => setPhrase(event.target.value)} /></label>
      <footer><div className={`rf-launch-readiness ${valid ? 'ready' : 'blocked'}`} aria-live="polite">{valid ? <><CheckCircle2 size={15} /><span><strong>{missingImages.length ? 'Ready to download.' : 'Ready to start.'}</strong> All profile and session guards are satisfied.</span></> : <><AlertTriangle size={15} /><span><strong>Start is blocked.</strong>{launchBlockers.map((blocker) => <small key={blocker}>{blocker}</small>)}</span></>}</div><div className="rf-dialog-actions"><button className="secondary" type="button" onClick={onCancel}>Cancel</button><button className="danger rf-launch-button" type="button" disabled={!valid || loading} title={!valid ? launchBlockers.join(' ') : undefined} onClick={() => onConfirm({ execute: true, confirmation_phrase: phrase, operator_note: note.trim(), requested_duration_seconds: duration, acknowledgements })}>{loading ? 'Preparing guarded session…' : missingImages.length ? <><Download size={15} />Download {missingImages.length} components</> : 'Start core + RF'}</button></div></footer>
    </section>
  </div>;
}
