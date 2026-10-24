import { type FormEvent, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useRealImsActions, useRealImsStatus, useRealImsSubscribers } from '../hooks/useRealIms';
import type { RealImsMode, RealImsProvisionPayload, RealImsReport } from '../types/realIms';

type PendingExecution = { payload: RealImsProvisionPayload };
type PendingRuntimeAction = 'start' | 'stop';
type PendingSync = { imsi: string; targetMode: RealImsMode };

const initialSubscriber = {
  imsi: '',
  msisdn: '',
  ki: '',
  opc: '',
  amf: '8000',
  sqn: '000000000001',
  enabled: true,
};

function ReportPanel({ report }: { report?: RealImsReport }) {
  if (!report) return <div className="empty-state">Refresh status to inspect subscriber and service checks.</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Check</th><th>Status</th><th>Result</th></tr></thead>
        <tbody>{report.checks.map((check) => (
          <tr key={check.id}>
            <td><code>{check.id}</code></td>
            <td><StatusBadge status={check.status} kind="validation" /></td>
            <td>{check.message}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

export function RealImsPage() {
  const [mode, setMode] = useState<RealImsMode>('4g');
  const [mcc, setMcc] = useState('001');
  const [mnc, setMnc] = useState('01');
  const [statusImsi, setStatusImsi] = useState('');
  const [subscriber, setSubscriber] = useState(initialSubscriber);
  const [editing, setEditing] = useState(false);
  const [pending, setPending] = useState<PendingExecution | null>(null);
  const [pendingRuntimeAction, setPendingRuntimeAction] = useState<PendingRuntimeAction | null>(null);
  const [pendingSync, setPendingSync] = useState<PendingSync | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [result, setResult] = useState('');
  const queryClient = useQueryClient();
  const formRef = useRef<HTMLFormElement>(null);
  const status = useRealImsStatus(mode, statusImsi);
  const imsSubscribers = useRealImsSubscribers(mode);
  const actions = useRealImsActions();
  const actionError = actions.provision.error || actions.deleteSubscriber.error || actions.start.error || actions.stop.error || actions.syncSubscriber.error;

  const clearSecrets = () => setSubscriber((current) => ({ ...current, ki: '', opc: '' }));
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
      apn_internet: 'internet',
      apn_ims: 'ims',
      enabled: subscriber.enabled,
    };
    if (execute) {
      setPending({ payload });
      return;
    }
    actions.provision.mutate(payload, {
      onSuccess: () => setResult('Preview passed. No subscriber records were changed.'),
    });
  };

  const confirmProvision = () => {
    if (!pending) return;
    actions.provision.mutate(pending.payload, {
      onSuccess: () => {
        setResult(`${pending.payload.imsi} was synchronized with Open5GS and pyHSS.`);
        setSubscriber(initialSubscriber);
        setEditing(false);
        void imsSubscribers.refetch();
        if (statusImsi === pending.payload.imsi) void status.refetch();
      },
    });
    setPending(null);
  };

  const confirmDelete = () => {
    if (!deleteTarget || deleteConfirmation !== deleteTarget) return;
    actions.deleteSubscriber.mutate({ mode, execute: true, mcc: mcc.trim(), mnc: mnc.trim(), imsi: deleteTarget }, {
      onSuccess: () => {
        setResult(`${deleteTarget} was removed from Open5GS and pyHSS. Shared APN profiles were kept.`);
        setDeleteTarget(null);
        setDeleteConfirmation('');
        if (editing && subscriber.imsi === deleteTarget) {
          setEditing(false);
          setSubscriber(initialSubscriber);
        }
        void imsSubscribers.refetch();
      },
    });
  };

  const confirmRuntimeAction = () => {
    if (!pendingRuntimeAction) return;
    if (pendingRuntimeAction === 'start') {
      actions.start.mutate({ mode, execute: true, mcc: mcc.trim(), mnc: mnc.trim() }, {
        onSuccess: () => {
          setResult(`${mode.toUpperCase()} IMS services are running. No RAN or RF service was started.`);
          void imsSubscribers.refetch();
          void status.refetch();
        },
      });
    } else {
      actions.stop.mutate({ mode, execute: true }, {
        onSuccess: () => setResult(`${mode.toUpperCase()} IMS services stopped. Subscriber records were retained.`),
      });
    }
    setPendingRuntimeAction(null);
  };

  const confirmSync = () => {
    if (!pendingSync) return;
    actions.syncSubscriber.mutate({
      source_mode: mode,
      target_mode: pendingSync.targetMode,
      mcc: mcc.trim(),
      mnc: mnc.trim(),
      imsi: pendingSync.imsi,
    }, {
      onSuccess: () => {
        setResult(`${pendingSync.imsi} was synchronized from ${mode.toUpperCase()} IMS to ${pendingSync.targetMode.toUpperCase()} IMS. Authentication keys remained hidden.`);
        void imsSubscribers.refetch();
        void queryClient.invalidateQueries({ queryKey: ['real-ims', 'subscribers', pendingSync.targetMode] });
      },
    });
    setPendingSync(null);
  };

  const beginEdit = (item: NonNullable<typeof imsSubscribers.data>['subscribers'][number]) => {
    setSubscriber((current) => ({ ...current, imsi: item.imsi, msisdn: item.msisdn }));
    setEditing(true);
    setResult('Re-enter Ki and OPc to update this subscriber. Secrets are never retrieved from the core.');
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <section className="page-panel real-ims-page subscriber-ims-workspace">
      <header className="subscriber-section-heading">
        <div>
          <span className="eyebrow">IMS service provisioning</span>
          <h2>IMS synchronization</h2>
          <p className="page-subtitle">This is the same IMSI as the packet-core record. Open5GS and pyHSS each need their own technical record; the identity is synchronized, not a second user.</p>
        </div>
        <div className="tab-list ims-mode-switch" aria-label="IMS network mode">
          <button type="button" className={mode === '4g' ? 'active' : ''} aria-pressed={mode === '4g'} onClick={() => setMode('4g')}>4G</button>
          <button type="button" className={mode === '5g' ? 'active' : ''} aria-pressed={mode === '5g'} onClick={() => setMode('5g')}>5G</button>
        </div>
      </header>

      <div className="subscriber-apn-profiles" aria-label="Preconfigured APNs">
        <article><span className="apn-mark">01</span><div><strong>internet</strong><p>Default data access · QCI 9</p></div><span className="apn-auto-label">Added automatically</span></article>
        <article><span className="apn-mark">02</span><div><strong>ims</strong><p>IMS signaling · QCI 5 · voice bearers QCI 1/2</p></div><span className="apn-auto-label">Added automatically</span></article>
      </div>

      <section className="panel subscriber-ims-runtime">
        <div className="panel-heading"><div><h3>{mode.toUpperCase()} IMS services</h3><p className="muted-text">Start or stop the isolated Open5GS, Kamailio and pyHSS services for this mode. This does not start a RAN or transmit RF.</p></div><div className="inline-actions"><ActionButton variant="secondary" loading={actions.start.isPending} onClick={() => setPendingRuntimeAction('start')}>Start IMS services</ActionButton><ActionButton variant="secondary" loading={actions.stop.isPending} onClick={() => setPendingRuntimeAction('stop')}>Stop IMS services</ActionButton></div></div>
      </section>

      {result ? <div className="ims-result" role="status">{result}</div> : null}
      {actionError ? <ErrorAlert error={actionError} /> : null}

      <section className="panel subscriber-ims-list">
        <div className="panel-heading">
          <div><h3>IMS synchronization status</h3><p className="muted-text">Shows whether the same IMSI exists in the IMS runtime’s Open5GS and pyHSS. Secrets stay hidden.</p></div>
          <div className="inline-actions"><StatusBadge status={`${imsSubscribers.data?.count || 0} subscribers`} /><ActionButton variant="secondary" loading={imsSubscribers.isFetching} onClick={() => imsSubscribers.refetch()}>Refresh</ActionButton></div>
        </div>
        {imsSubscribers.error ? <ErrorAlert error={imsSubscribers.error} onRetry={() => imsSubscribers.refetch()} /> : null}
        {imsSubscribers.isLoading ? <LoadingState /> : null}
        {imsSubscribers.data?.subscribers.length ? (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Subscriber</th><th>IMS address</th><th>APN profile</th><th>Sync</th><th>Action</th></tr></thead>
              <tbody>{imsSubscribers.data.subscribers.map((item) => (
                <tr key={item.imsi}>
                  <td><strong>{item.imsi}</strong><br /><span className="muted-text">{item.msisdn}</span></td>
                  <td><code>{item.impu || item.impi}</code></td>
                  <td>{item.apns.join(', ') || 'not synchronized'}</td>
                  <td><StatusBadge status={item.open5gs_present && item.pyhss_present ? 'Synced' : 'Needs attention'} kind="validation" /></td>
                  <td><div className="row-actions"><button className="row-action" type="button" onClick={() => setPendingSync({ imsi: item.imsi, targetMode: mode === '4g' ? '5g' : '4g' })}>Sync to {mode === '4g' ? '5G' : '4G'}</button><button className="row-action" type="button" onClick={() => beginEdit(item)}>Edit</button><button className="row-action danger" type="button" onClick={() => { setDeleteTarget(item.imsi); setDeleteConfirmation(''); }}><Trash2 size={14} /><span>Delete</span></button></div></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : (!imsSubscribers.isLoading && !imsSubscribers.error ? <div className="empty-state">No IMS subscribers yet. Add one below.</div> : null)}
      </section>

      <section className="panel subscriber-ims-create">
          <div className="panel-heading"><div><h3>{editing ? 'Update IMS credentials' : 'Enable IMS for an identity'}</h3><p className="muted-text">Required: IMSI, phone number, Ki and OPc. The preconfigured internet and ims APN profiles are synchronized automatically.</p></div>{editing ? <button type="button" className="secondary" onClick={() => { setEditing(false); setSubscriber(initialSubscriber); }}>Cancel edit</button> : null}</div>
        <form ref={formRef} className="real-ims-form" onSubmit={submitProvision}>
          <div className="ims-field-grid">
            <label>IMSI<input required inputMode="numeric" pattern="\d{14,15}" value={subscriber.imsi} onChange={(event) => setSubscriber({ ...subscriber, imsi: event.target.value })} /></label>
            <label>MSISDN<input required inputMode="tel" pattern="\+?\d{5,15}" value={subscriber.msisdn} onChange={(event) => setSubscriber({ ...subscriber, msisdn: event.target.value })} /></label>
            <label>Ki<input required type="password" autoComplete="new-password" pattern="[0-9a-fA-F]{32}" value={subscriber.ki} onChange={(event) => setSubscriber({ ...subscriber, ki: event.target.value })} /></label>
            <label>OPc<input required type="password" autoComplete="new-password" pattern="[0-9a-fA-F]{32}" value={subscriber.opc} onChange={(event) => setSubscriber({ ...subscriber, opc: event.target.value })} /></label>
          </div>
          <label className="ims-checkbox"><input type="checkbox" checked={subscriber.enabled} onChange={(event) => setSubscriber({ ...subscriber, enabled: event.target.checked })} />Subscriber enabled</label>
          <details className="subscriber-advanced">
            <summary>Advanced network settings</summary>
            <p>MCC and MNC identify your test network. They determine the IMS domain and must match the beginning of the IMSI. Defaults are MCC 001 and MNC 01.</p>
            <div className="ims-field-grid">
              <label>MCC<input required pattern="\d{3}" inputMode="numeric" value={mcc} onChange={(event) => setMcc(event.target.value)} /></label>
              <label>MNC<input required pattern="\d{2,3}" inputMode="numeric" value={mnc} onChange={(event) => setMnc(event.target.value)} /></label>
              <label>AMF<input required pattern="[0-9a-fA-F]{4}" value={subscriber.amf} onChange={(event) => setSubscriber({ ...subscriber, amf: event.target.value })} /></label>
              <label>SQN<input required pattern="[0-9a-fA-F]{12}" value={subscriber.sqn} onChange={(event) => setSubscriber({ ...subscriber, sqn: event.target.value })} /></label>
            </div>
          </details>
          <div className="inline-actions">
            <ActionButton type="submit" name="provisionAction" value="dry-run" variant="secondary" loading={actions.provision.isPending}>Preview</ActionButton>
            <ActionButton type="submit" name="provisionAction" value="execute" disabled={actions.provision.isPending}>{editing ? 'Save and synchronize' : 'Add subscriber'}</ActionButton>
          </div>
        </form>
      </section>

      <details className="panel subscriber-technical-status">
        <summary>Service and subscriber checks</summary>
        <div className="subscriber-status-lookup">
          <label>Optional IMSI<input inputMode="numeric" pattern="\d{14,15}" value={statusImsi} onChange={(event) => setStatusImsi(event.target.value)} placeholder="Enter IMSI to inspect" /></label>
          <ActionButton variant="secondary" loading={status.isFetching} onClick={() => status.refetch()}>Check status</ActionButton>
        </div>
        {status.error ? <ErrorAlert error={status.error} onRetry={() => status.refetch()} /> : null}
        {status.isLoading ? <LoadingState /> : null}
        <ReportPanel report={status.data} />
        <p className="muted-text">Use the selected scenario workspace to start the RAN and check UE registration and calls.</p>
      </details>

      <ConfirmDialog open={Boolean(pending)} title={editing ? 'Save IMS subscriber changes?' : 'Add this IMS subscriber?'} message={`This synchronizes ${pending?.payload.imsi || 'the subscriber'} to Open5GS and pyHSS. Ki and OPc are sent to the selected local IMS runtime and are never shown in the list.`} confirmLabel={editing ? 'Save and synchronize' : 'Add subscriber'} onConfirm={confirmProvision} onCancel={() => setPending(null)} />
      <ConfirmDialog open={Boolean(pendingRuntimeAction)} title={`${pendingRuntimeAction === 'start' ? 'Start' : 'Stop'} ${mode.toUpperCase()} IMS services?`} message={pendingRuntimeAction === 'start' ? 'This starts the selected local IMS service stack only. It does not start an eNB, gNB, UE, or radio transmission.' : 'This stops the selected IMS service stack. Subscriber records and shared APN profiles are retained.'} confirmLabel={`${pendingRuntimeAction === 'start' ? 'Start' : 'Stop'} IMS services`} onConfirm={confirmRuntimeAction} onCancel={() => setPendingRuntimeAction(null)} />
      <ConfirmDialog open={Boolean(pendingSync)} title={`Synchronize ${pendingSync?.imsi || 'subscriber'} to ${pendingSync?.targetMode.toUpperCase() || 'other'} IMS?`} message={`This copies the existing local identity from ${mode.toUpperCase()} IMS to ${pendingSync?.targetMode.toUpperCase() || 'the other'} IMS, including the required authentication records and preconfigured APNs. Keys stay inside the local backend and are never shown. The target IMS services must be running.`} confirmLabel={`Sync to ${pendingSync?.targetMode.toUpperCase() || 'other'} IMS`} onConfirm={confirmSync} onCancel={() => setPendingSync(null)} />
      {deleteTarget ? <div className="dialog-backdrop" role="presentation"><div className="dialog" role="dialog" aria-modal="true" aria-labelledby="ims-delete-title"><h2 id="ims-delete-title">Delete IMS subscriber?</h2><p>This removes the subscriber from Open5GS, pyHSS, and AuC. Shared APN profiles stay in place. Type the IMSI to confirm.</p><label>IMSI<input autoFocus value={deleteConfirmation} onChange={(event) => setDeleteConfirmation(event.target.value)} /></label><div className="dialog-actions"><button type="button" onClick={() => { setDeleteTarget(null); setDeleteConfirmation(''); }}>Cancel</button><button type="button" className="danger" disabled={deleteConfirmation !== deleteTarget || actions.deleteSubscriber.isPending} onClick={confirmDelete}>{actions.deleteSubscriber.isPending ? 'Deleting…' : 'Delete subscriber'}</button></div></div></div> : null}
    </section>
  );
}
