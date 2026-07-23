import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Database, Download, Plus, RefreshCw, Search, ShieldCheck, Upload, UsersRound } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { EmptyState } from '../components/EmptyState';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { SubscriberCloneDialog } from '../components/subscribers/SubscriberCloneDialog';
import { SubscriberConnectionStatus } from '../components/subscribers/SubscriberConnectionStatus';
import { SubscriberDeleteDialog } from '../components/subscribers/SubscriberDeleteDialog';
import { SubscriberTable } from '../components/subscribers/SubscriberTable';
import { useSubscriberActions, useSubscriberConnection, useSubscribers } from '../hooks/useSubscribers';
import type { SubscriberSummary } from '../types/subscriber';

const pageSize = 25;

export function SubscribersPage() {
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [cloneTarget, setCloneTarget] = useState<SubscriberSummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<SubscriberSummary | null>(null);
  const connection = useSubscriberConnection();
  const subscribers = useSubscribers({ limit: pageSize, offset, search });
  const actions = useSubscriberActions();
  const mutationError = actions.clone.error || actions.delete.error;
  const subscriberCount = subscribers.data?.total || 0;
  const connectionOnline = connection.data?.status === 'connected';
  const exportVisible = () => {
    const rows = subscribers.data?.items || [];
    const csv = ['imsi,msisdn,dnn,sst,sd,k_configured,op_configured,opc_configured', ...rows.map((item) => [item.imsi, item.msisdn || '', item.dnn || '', item.sst || '', item.sd || '', item.security.k_configured, item.security.op_configured, item.security.opc_configured].join(','))].join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    const link = document.createElement('a'); link.href = url; link.download = 'open5gs-subscribers-redacted.csv'; link.click(); URL.revokeObjectURL(url);
  };

  return (
    <section className="subscribers-workspace">
      <div className="subscriber-hero">
        <div>
          <span className="eyebrow">IDENTITY REGISTRY · OPEN5GS</span>
          <h1>Subscribers</h1>
          <p className="page-subtitle">Manage packet-core identities without exposing authentication material.</p>
        </div>
        <div className="subscriber-hero-stats"><div><span>Total records</span><strong>{subscribers.isLoading ? '—' : subscriberCount}</strong></div><div><span>Database link</span><strong className={connectionOnline ? 'text-good' : 'text-bad'}>{connectionOnline ? 'ONLINE' : 'OFFLINE'}</strong></div></div>
        <div className="subscriber-primary-actions"><button className="secondary" onClick={exportVisible} disabled={!subscribers.data?.items.length}><Download size={15} />Export CSV</button><button className="secondary" disabled title="Bulk import is not exposed by the current backend"><Upload size={15} />Import</button><Link className="action-link" to="/subscribers/new"><Plus size={16} />Create subscriber</Link></div>
      </div>

      <div className="subscriber-overview-grid">
        <div>{connection.isLoading ? <LoadingState /> : null}{connection.error ? <ErrorAlert error={connection.error} onRetry={() => connection.refetch()} /> : null}{connection.data ? <SubscriberConnectionStatus status={connection.data} /> : null}</div>
        <aside className="security-note"><span><ShieldCheck size={19} /></span><div><small>SECURITY BOUNDARY</small><strong>Secrets stay sealed</strong><p>Ki, OP and OPc are redacted from list views, exports and diagnostics.</p></div></aside>
      </div>

      {mutationError ? <ErrorAlert error={mutationError} /> : null}

      <section className="subscriber-registry panel">
        <div className="registry-heading"><div><span className="registry-icon"><UsersRound size={18} /></span><div><h2>Subscriber registry</h2><p>{subscriberCount} records in the active Open5GS collection</p></div></div><span className={`registry-health ${connectionOnline ? 'online' : 'offline'}`}><i />{connectionOnline ? 'Database connected' : 'Database unavailable'}</span></div>
        <div className="subscriber-toolbar">
          <label className="search-field"><Search size={17} /><span className="sr-only">Search IMSI / MSISDN</span><input aria-label="Search IMSI / MSISDN" placeholder="Search IMSI or MSISDN…" value={search} onChange={(event) => { setOffset(0); setSearch(event.target.value); }} /></label>
          <ActionButton variant="secondary" onClick={() => subscribers.refetch()} loading={subscribers.isFetching}><RefreshCw size={15} />Refresh</ActionButton>
          <span className="registry-source"><Database size={14} />{connection.data?.database || 'open5gs'} / {connection.data?.collection || 'subscribers'}</span>
        </div>

        {subscribers.isLoading ? <LoadingState /> : null}
        {subscribers.error ? <ErrorAlert error={subscribers.error} onRetry={() => subscribers.refetch()} /> : null}
        {subscribers.data && subscribers.data.items.length > 0 ? <SubscriberTable subscribers={subscribers.data.items} onClone={setCloneTarget} onDelete={setDeleteTarget} /> : null}
        {subscribers.data && subscribers.data.items.length === 0 ? <EmptyState title="No subscribers" message="No subscriber records match the current filters, or MongoDB is unavailable." /> : null}

        {subscribers.data ? (
          <div className="pagination-row">
            <button className="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>Previous</button>
            <span>{offset + 1}-{Math.min(offset + pageSize, subscribers.data.total)} of {subscribers.data.total}</span>
            <button className="secondary" disabled={offset + pageSize >= subscribers.data.total} onClick={() => setOffset(offset + pageSize)}>Next</button>
          </div>
        ) : null}
      </section>

      <SubscriberCloneDialog
        subscriber={cloneTarget}
        loading={actions.clone.isPending}
        onCancel={() => setCloneTarget(null)}
        onConfirm={(imsi, payload) => actions.clone.mutate({ imsi, payload }, { onSuccess: () => setCloneTarget(null) })}
      />
      <SubscriberDeleteDialog
        subscriber={deleteTarget}
        loading={actions.delete.isPending}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={(imsi) => actions.delete.mutate({ imsi, confirm: true }, { onSuccess: () => setDeleteTarget(null) })}
      />
    </section>
  );
}
