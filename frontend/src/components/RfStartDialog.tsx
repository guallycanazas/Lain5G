import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { AlertTriangle, RadioTower, ShieldCheck, Timer, X } from 'lucide-react';
import type { RfStartPayload } from '../types/deployment';
import { profilesApi } from '../services/profilesApi';

const acknowledgementLabels = {
  legal_authorization_valid: 'Legal and local authorization remains valid.',
  isolation_and_attenuation_verified: 'Shielding, cabling, and attenuation were physically verified.',
  channel_and_gain_reviewed: 'Channel, bandwidth, and gain match the approved plan.',
  emergency_stop_accessible: 'Emergency stop remains accessible for the entire session.',
};

export function RfStartDialog({ scenarioId, open, loading, onCancel, onConfirm }: { scenarioId: string; open: boolean; loading: boolean; onCancel: () => void; onConfirm: (payload: RfStartPayload) => void }) {
  const [duration, setDuration] = useState(60);
  const [note, setNote] = useState('Controlled RF session from Lain5G-Lab');
  const [phrase, setPhrase] = useState('');
  const [acknowledgements, setAcknowledgements] = useState<Record<keyof RfStartPayload['acknowledgements'], boolean>>({ legal_authorization_valid: false, isolation_and_attenuation_verified: false, channel_and_gain_reviewed: false, emergency_stop_accessible: false });
  const profile = useQuery({ queryKey: ['profile', scenarioId], queryFn: () => profilesApi.detail(scenarioId), enabled: open });
  const diff = useQuery({ queryKey: ['profile-diff', scenarioId], queryFn: () => profilesApi.diff(scenarioId), enabled: open });
  const expectedPhrase = `START ${scenarioId.toUpperCase()} RF`;
  const is5g = scenarioId === '5g-sa-x310';
  const config = profile.data;
  const radio = config?.radio || {};
  const safety = config?.safety || {};
  const maximumDuration = Number(safety.maximum_duration_seconds) || 60;
  const pendingChanges = Boolean(diff.data?.files?.some((file) => file.changed));
  const configurationReady = Boolean(config && diff.data && !pendingChanges);
  const valid = configurationReady && duration >= 1 && duration <= maximumDuration && phrase === expectedPhrase && note.trim().length >= 3 && Object.values(acknowledgements).every(Boolean);

  useEffect(() => {
    if (!open) return;
    setPhrase('');
    setAcknowledgements({ legal_authorization_valid: false, isolation_and_attenuation_verified: false, channel_and_gain_reviewed: false, emergency_stop_accessible: false });
  }, [open, scenarioId]);

  useEffect(() => {
    if (!open || !profile.data) return;
    const limit = Number(profile.data.safety?.maximum_duration_seconds) || 60;
    setDuration(Math.min(60, limit));
    setNote(profile.data.safety?.operator_note || 'Controlled RF session from Lain5G-Lab');
  }, [open, profile.data, scenarioId]);

  if (!open) return null;
  return <div className="dialog-backdrop rf-dialog-backdrop" role="presentation">
    <section className="rf-start-dialog" role="dialog" aria-modal="true" aria-labelledby="rf-start-title">
      <header><div className="rf-dialog-title"><span><RadioTower size={21} /></span><div><small>GUARDED RF SESSION</small><h2 id="rf-start-title">Start {is5g ? '5G gNB' : 'LTE eNB'} + X310</h2></div></div><button className="dialog-close" type="button" onClick={onCancel} aria-label="Close"><X size={18} /></button></header>
      <div className="rf-danger-banner"><AlertTriangle size={18} /><div><strong>This action transmits RF energy.</strong><span>The core starts first and the SDR container stops automatically.</span></div></div>
      {profile.isLoading || diff.isLoading ? <div className="rf-config-state">Loading effective RF configuration...</div> : null}
      {profile.error || diff.error ? <div className="rf-config-state error">The RF configuration could not be verified. Start remains blocked.</div> : null}
      {pendingChanges ? <div className="rf-config-state warning"><strong>Configuration changes are pending.</strong><span>Open <Link to="/deployments" onClick={onCancel}>Deployments</Link>, validate, and apply the profile before starting RF.</span></div> : null}
      <div className="rf-session-summary">
        <div><span>Radio</span><strong>{is5g ? `n${radio.band ?? '—'} · ARFCN ${radio.dl_arfcn ?? '—'}` : `Band ${radio.lte_band ?? '—'} · EARFCN ${radio.earfcn ?? '—'}`}</strong></div>
        <div><span>Bandwidth</span><strong>{radio.bandwidth_mhz ?? '—'} MHz</strong></div>
        <div><span>TX / RX gain</span><strong>{radio.tx_gain ?? '—'} / {radio.rx_gain ?? '—'} dB</strong></div>
        <div><span>USRP</span><strong>{radio.usrp_addr || '—'} · {radio.device || '—'}</strong></div>
        <div><span>Environment</span><strong>{safety.environment || '—'} · {safety.attenuation_db ?? '—'} dB</strong></div>
        <div><span>Auto-stop limit</span><strong>{maximumDuration} seconds</strong></div>
      </div>
      <div className="rf-profile-link">Values come from the applied <code>{scenarioId}</code> profile. <Link to="/deployments" onClick={onCancel}>Edit configuration</Link></div>
      <div className="rf-form-grid"><label><Timer size={14} />Requested duration (seconds)<input type="number" min={1} max={maximumDuration} value={duration} onChange={(event) => setDuration(Number(event.target.value))} /></label><label>Operator purpose<input value={note} maxLength={240} onChange={(event) => setNote(event.target.value)} /></label></div>
      <fieldset className="rf-acknowledgements"><legend><ShieldCheck size={15} />Required checks</legend>{Object.entries(acknowledgementLabels).map(([key, label]) => <label key={key}><input type="checkbox" checked={acknowledgements[key as keyof typeof acknowledgements]} onChange={(event) => setAcknowledgements((current) => ({ ...current, [key]: event.target.checked }))} /><span>{label}</span></label>)}</fieldset>
      <label className="rf-confirmation">Type <code>{expectedPhrase}</code> to authorize this session<input autoComplete="off" value={phrase} onChange={(event) => setPhrase(event.target.value)} /></label>
      <footer><button className="secondary" type="button" onClick={onCancel}>Cancel</button><button className="danger rf-launch-button" type="button" disabled={!valid || loading} onClick={() => onConfirm({ execute: true, confirmation_phrase: phrase, operator_note: note.trim(), requested_duration_seconds: duration, acknowledgements })}>{loading ? 'Starting guarded session…' : 'Start core + RF'}</button></footer>
    </section>
  </div>;
}
