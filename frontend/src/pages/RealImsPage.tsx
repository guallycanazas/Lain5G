import { type FormEvent, useState } from 'react';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useRealImsActions, useRealImsPreflight, useRealImsStatus, useRealImsSubscribers } from '../hooks/useRealIms';
import type { RealImsMode, RealImsProvisionPayload, RealImsReport } from '../types/realIms';

type PendingExecution =
  | { kind: 'images' }
  | { kind: 'start' }
  | { kind: 'stop' }
  | { kind: 'provision'; payload: RealImsProvisionPayload };

const initialSubscriber = {
  imsi: '',
  msisdn: '',
  ki: '',
  opc: '',
  amf: '8000',
  sqn: '000000000001',
  apn_internet: 'internet',
  apn_ims: 'ims',
  enabled: true,
};

function evidenceText(evidence: unknown) {
  if (evidence === null || evidence === undefined || evidence === '') return 'No evidence reported';
  if (typeof evidence === 'string') return evidence;
  return JSON.stringify(evidence);
}

function ReportPanel({ title, report, empty }: { title: string; report?: RealImsReport; empty: string }) {
  return (
    <section className="panel ims-report">
      <div className="panel-heading">
        <h2>{title}</h2>
        {report ? <StatusBadge status={report.status} kind="validation" /> : null}
      </div>
      {report ? (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Check</th><th>Status</th><th>Message</th><th>Evidence</th></tr></thead>
            <tbody>
              {report.checks.map((check) => (
                <tr key={check.id}>
                  <td><code>{check.id}</code></td>
                  <td><StatusBadge status={check.status} kind="validation" /></td>
                  <td>{check.message}</td>
                  <td><code className="ims-evidence">{evidenceText(check.evidence)}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <div className="empty-state">{empty}</div>}
    </section>
  );
}

export function RealImsPage() {
  const [mode, setMode] = useState<RealImsMode>('4g');
  const [mcc, setMcc] = useState('001');
  const [mnc, setMnc] = useState('01');
  const [statusImsi, setStatusImsi] = useState('');
  const [subscriber, setSubscriber] = useState(initialSubscriber);
  const [pending, setPending] = useState<PendingExecution | null>(null);
  const [result, setResult] = useState('');
  const preflight = useRealImsPreflight(mode);
  const status = useRealImsStatus(mode, statusImsi);
  const imsSubscribers = useRealImsSubscribers(mode);
  const actions = useRealImsActions();
  const actionError = actions.images.error || actions.start.error || actions.stop.error || actions.provision.error;
  const actionPending = actions.images.isPending || actions.start.isPending || actions.stop.isPending || actions.provision.isPending;

  const clearSecrets = () => setSubscriber((current) => ({ ...current, ki: '', opc: '' }));
  const complete = (message: string, clearsSecrets = false) => {
    setResult(message);
    if (clearsSecrets) clearSecrets();
  };
  const startPayload = (execute: boolean) => ({ mode, execute, mcc: mcc.trim(), mnc: mnc.trim() });

  const previewImages = () => actions.images.mutate(false, { onSuccess: () => complete('Image build dry-run completed. No images were built.') });
  const previewStart = () => actions.start.mutate(startPayload(false), { onSuccess: () => complete(`${mode.toUpperCase()} runtime start dry-run completed.`) });
  const previewStop = () => actions.stop.mutate({ mode, execute: false }, { onSuccess: () => complete(`${mode.toUpperCase()} runtime stop dry-run completed.`) });

  const submitProvision = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const execute = submitter?.value === 'execute';
    const payload: RealImsProvisionPayload = {
      mode,
      execute,
      mcc: mcc.trim(),
      mnc: mnc.trim(),
      imsi: subscriber.imsi.trim(),
      msisdn: subscriber.msisdn.trim(),
      ki: subscriber.ki.trim(),
      opc: subscriber.opc.trim(),
      amf: subscriber.amf.trim(),
      sqn: subscriber.sqn.trim(),
      apn_internet: subscriber.apn_internet.trim(),
      apn_ims: subscriber.apn_ims.trim(),
      enabled: subscriber.enabled,
    };
    if (execute) {
      setPending({ kind: 'provision', payload });
      return;
    }
    actions.provision.mutate(payload, { onSuccess: () => complete('Subscriber provisioning dry-run completed. No subscriber was changed.', true) });
  };

  const confirmExecution = () => {
    if (!pending) return;
    if (pending.kind === 'images') actions.images.mutate(true, { onSuccess: () => complete('IMS runtime images built successfully.') });
    if (pending.kind === 'start') actions.start.mutate(startPayload(true), { onSuccess: () => complete(`${mode.toUpperCase()} IMS runtime start requested.`) });
    if (pending.kind === 'stop') actions.stop.mutate({ mode, execute: true }, { onSuccess: () => complete(`${mode.toUpperCase()} IMS runtime stop requested.`) });
    if (pending.kind === 'provision') actions.provision.mutate(pending.payload, { onSuccess: () => complete('Subscriber provisioned successfully.', true) });
    setPending(null);
  };

  const confirmation = pending ? {
    images: ['Build real IMS images?', 'This executes the first-party IMS image build on the host.', 'Build images'],
    start: [`Start the real ${mode.toUpperCase()} IMS runtime?`, `This starts first-party core and IMS services for MCC ${mcc}, MNC ${mnc}. It does not start RF.`, 'Start runtime'],
    stop: [`Stop the real ${mode.toUpperCase()} IMS runtime?`, 'This stops the selected first-party IMS runtime.', 'Stop runtime'],
    provision: ['Provision this subscriber?', `This writes subscriber ${pending.kind === 'provision' ? pending.payload.imsi : ''} to the real ${mode.toUpperCase()} runtime.`, 'Provision now'],
  }[pending.kind] : null;

  return (
    <section className="page-panel real-ims-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">First-party runtime</span>
          <h1>Real 4G/5G IMS operator</h1>
          <p className="page-subtitle">Operate the real first-party IMS runtime. This workspace is separate from legacy SIP probes and simulated SIP evidence.</p>
        </div>
        <div className="tab-list ims-mode-switch" aria-label="IMS network mode">
          <button type="button" className={mode === '4g' ? 'active' : ''} aria-pressed={mode === '4g'} onClick={() => setMode('4g')}>4G IMS</button>
          <button type="button" className={mode === '5g' ? 'active' : ''} aria-pressed={mode === '5g'} onClick={() => setMode('5g')}>5G IMS</button>
        </div>
      </div>

      <div className="warning-box ims-limitation"><strong>Readiness is not a VoLTE or VoNR call claim.</strong> Passing checks shows reported service readiness only. This page has no RF start controls and does not prove UE registration, media flow, or an end-to-end call.</div>

      {result ? <div className="ims-result" role="status">{result}</div> : null}
      {actionError ? <ErrorAlert error={actionError} /> : null}

      <div className="page-grid ims-section">
        <section className="panel">
          <div className="panel-heading"><h2>Network identity</h2><StatusBadge status={mode === '4g' ? '4G' : '5G'} /></div>
          <div className="ims-field-grid">
            <label>MCC<input required pattern="\d{3}" inputMode="numeric" value={mcc} onChange={(event) => setMcc(event.target.value)} /></label>
            <label>MNC<input required pattern="\d{2,3}" inputMode="numeric" value={mnc} onChange={(event) => setMnc(event.target.value)} /></label>
          </div>
          <p className="muted-text">MCC and MNC are sent to runtime start and subscriber provisioning requests.</p>
        </section>
        <section className="panel">
          <div className="panel-heading"><h2>Status lookup</h2></div>
            <label>Status IMSI<input inputMode="numeric" pattern="\d{14,15}" value={statusImsi} onChange={(event) => setStatusImsi(event.target.value)} placeholder="Optional subscriber IMSI" /></label>
          <div className="inline-actions ims-actions">
            <ActionButton variant="secondary" loading={preflight.isFetching} onClick={() => preflight.refetch()}>Refresh preflight</ActionButton>
            <ActionButton variant="secondary" loading={status.isFetching} onClick={() => status.refetch()}>Refresh status</ActionButton>
          </div>
        </section>
      </div>

      {preflight.isLoading ? <LoadingState /> : null}
      {preflight.error ? <ErrorAlert error={preflight.error} onRetry={() => preflight.refetch()} /> : null}
      {status.error ? <ErrorAlert error={status.error} onRetry={() => status.refetch()} /> : null}
      <div className="page-grid ims-section">
        <ReportPanel title={`${mode.toUpperCase()} preflight checks`} report={preflight.data} empty="No preflight report available." />
        <ReportPanel title={`${mode.toUpperCase()} runtime status`} report={status.data} empty="Refresh status to inspect runtime and subscriber checks." />
      </div>

      <section className="panel ims-section">
        <div className="panel-heading">
          <div><h2>IMS subscribers</h2><p className="muted-text">Correlated pyHSS and Open5GS records. Authentication secrets are never returned.</p></div>
          <div className="inline-actions"><StatusBadge status={`${imsSubscribers.data?.count || 0} subscribers`} /><ActionButton variant="secondary" loading={imsSubscribers.isFetching} onClick={() => imsSubscribers.refetch()}>Refresh subscribers</ActionButton></div>
        </div>
        {imsSubscribers.error ? <ErrorAlert error={imsSubscribers.error} onRetry={() => imsSubscribers.refetch()} /> : null}
        {imsSubscribers.isLoading ? <LoadingState /> : null}
        {imsSubscribers.data?.subscribers.length ? (
          <div className="table-wrap">
            <table>
              <thead><tr><th>IMSI / MSISDN</th><th>Public identity</th><th>S-CSCF</th><th>APNs</th><th>Synchronization</th><th>Status</th></tr></thead>
              <tbody>{imsSubscribers.data.subscribers.map((item) => (
                <tr key={item.imsi}>
                  <td><strong>{item.imsi}</strong><br /><span className="muted-text">{item.msisdn}</span></td>
                  <td><code>{item.impu || item.impi}</code></td>
                  <td><code>{item.scscf || 'not assigned'}</code></td>
                  <td>{item.apns.join(', ') || 'not synchronized'}</td>
                  <td><StatusBadge status={item.open5gs_present && item.pyhss_present ? 'PASS' : 'WARNING'} kind="validation" /></td>
                  <td><StatusBadge status={item.enabled ? 'enabled' : 'disabled'} /></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : (!imsSubscribers.isLoading && !imsSubscribers.error ? <div className="empty-state">No IMS subscribers are provisioned in {mode.toUpperCase()}.</div> : null)}
      </section>

      <section className="panel ims-section">
        <div className="panel-heading"><div><h2>Runtime controls</h2><p className="muted-text">Preview is dry-run only. Execute actions always require confirmation.</p></div></div>
        <div className="ims-runtime-grid">
          <article className="ims-control-card"><h3>Runtime images</h3><p>Build first-party IMS service images.</p><div className="inline-actions"><ActionButton variant="secondary" disabled={actionPending} onClick={previewImages}>Preview image build</ActionButton><ActionButton disabled={actionPending} onClick={() => setPending({ kind: 'images' })}>Build images</ActionButton></div></article>
          <article className="ims-control-card"><h3>Start {mode.toUpperCase()}</h3><p>Start core and IMS services without RF.</p><div className="inline-actions"><ActionButton variant="secondary" disabled={actionPending} onClick={previewStart}>Preview start</ActionButton><ActionButton disabled={actionPending} onClick={() => setPending({ kind: 'start' })}>Start runtime</ActionButton></div></article>
          <article className="ims-control-card"><h3>Stop {mode.toUpperCase()}</h3><p>Stop the selected IMS runtime services.</p><div className="inline-actions"><ActionButton variant="secondary" disabled={actionPending} onClick={previewStop}>Preview stop</ActionButton><ActionButton variant="danger" disabled={actionPending} onClick={() => setPending({ kind: 'stop' })}>Stop runtime</ActionButton></div></article>
        </div>
      </section>

      <section className="panel ims-section">
        <div className="panel-heading"><div><h2>Subscriber provisioning</h2><p className="muted-text">Dry-run is the default. Ki and OPc stay only in this form's memory and are cleared after a successful request.</p></div></div>
        <form className="real-ims-form" onSubmit={submitProvision}>
          <div className="ims-field-grid">
            <label>IMSI<input required inputMode="numeric" pattern="\d{14,15}" value={subscriber.imsi} onChange={(event) => setSubscriber({ ...subscriber, imsi: event.target.value })} /></label>
            <label>MSISDN<input required inputMode="tel" pattern="\+?\d{5,15}" value={subscriber.msisdn} onChange={(event) => setSubscriber({ ...subscriber, msisdn: event.target.value })} /></label>
            <label>Ki<input required type="password" autoComplete="new-password" pattern="[0-9a-fA-F]{32}" value={subscriber.ki} onChange={(event) => setSubscriber({ ...subscriber, ki: event.target.value })} /></label>
            <label>OPc<input required type="password" autoComplete="new-password" pattern="[0-9a-fA-F]{32}" value={subscriber.opc} onChange={(event) => setSubscriber({ ...subscriber, opc: event.target.value })} /></label>
            <label>AMF<input required pattern="[0-9a-fA-F]{4}" value={subscriber.amf} onChange={(event) => setSubscriber({ ...subscriber, amf: event.target.value })} /></label>
            <label>SQN<input required pattern="[0-9a-fA-F]{12}" value={subscriber.sqn} onChange={(event) => setSubscriber({ ...subscriber, sqn: event.target.value })} /></label>
            <label>Internet APN<input required value={subscriber.apn_internet} onChange={(event) => setSubscriber({ ...subscriber, apn_internet: event.target.value })} /></label>
            <label>IMS APN<input required value={subscriber.apn_ims} onChange={(event) => setSubscriber({ ...subscriber, apn_ims: event.target.value })} /></label>
          </div>
          <label className="ims-checkbox"><input type="checkbox" checked={subscriber.enabled} onChange={(event) => setSubscriber({ ...subscriber, enabled: event.target.checked })} />Subscriber enabled</label>
          <div className="inline-actions">
            <ActionButton type="submit" name="provisionAction" value="dry-run" variant="secondary" loading={actions.provision.isPending}>Preview provisioning</ActionButton>
            <ActionButton type="submit" name="provisionAction" value="execute" disabled={actionPending}>Provision subscriber</ActionButton>
          </div>
        </form>
      </section>

      <ConfirmDialog open={Boolean(pending)} title={confirmation?.[0] || ''} message={confirmation?.[1] || ''} confirmLabel={confirmation?.[2] || 'Confirm'} onConfirm={confirmExecution} onCancel={() => setPending(null)} />
    </section>
  );
}
