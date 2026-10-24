import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { Download, Plus, RefreshCw, Search, ShieldCheck } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { EmptyState } from '../components/EmptyState';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { SubscriberCloneDialog } from '../components/subscribers/SubscriberCloneDialog';
import { SubscriberConnectionStatus } from '../components/subscribers/SubscriberConnectionStatus';
import { SubscriberDeleteDialog } from '../components/subscribers/SubscriberDeleteDialog';
import { SubscriberTable } from '../components/subscribers/SubscriberTable';
import { RealImsPage } from './RealImsPage';
import { useSubscriberActions, useSubscriberConnection, useSubscribers } from '../hooks/useSubscribers';
import type { SubscriberProfile, SubscriberSummary } from '../types/subscriber';

const pageSize = 25;
const subscriberProfiles: { id: SubscriberProfile; label: string }[] = [
  { id: '4g-lte-x310', label: '4G LTE X310' },
  { id: '5g-sa-x310', label: '5G SA X310' },
  { id: '5g-nsa-x310', label: '5G NSA X310 · shared 4G EPC' },
];

export function SubscribersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeView = searchParams.get('view') === 'ims' ? 'ims' : 'open5gs';
  const requestedProfile = searchParams.get('profile');
  const profile: SubscriberProfile = subscriberProfiles.some((item) => item.id === requestedProfile)
    ? requestedProfile as SubscriberProfile
    : '4g-lte-x310';
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [cloneTarget, setCloneTarget] = useState<SubscriberSummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<SubscriberSummary | null>(null);
  const connection = useSubscriberConnection(profile);
  const subscribers = useSubscribers({ limit: pageSize, offset, search, profile });
  const actions = useSubscriberActions(profile);
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
      <header className="subscribers-page-heading">
        <div><span className="eyebrow">Identity management</span><h1>Subscribers</h1><p>Manage each SIM identity once. Packet-core and IMS views show the same IMSI in the systems that need it.</p></div>
        {activeView === 'open5gs' ? <div className="subscriber-health-chip"><i className={connectionOnline ? 'online' : 'offline'} />{connectionOnline ? 'Packet core connected' : 'Packet core unavailable'}</div> : null}
      </header>

      <nav className="tab-list subscriber-workspace-tabs" aria-label="Subscriber records">
        <button type="button" className={activeView === 'open5gs' ? 'active' : ''} aria-pressed={activeView === 'open5gs'} onClick={() => setSearchParams({ profile })}>
          Packet core <span>{subscribers.isLoading ? '…' : subscriberCount}</span>
        </button>
        <button type="button" className={activeView === 'ims' ? 'active' : ''} aria-pressed={activeView === 'ims'} onClick={() => setSearchParams({ view: 'ims', profile })}>IMS provisioning</button>
      </nav>

      {activeView === 'ims' ? <RealImsPage /> : <>
        <div className="subscriber-intro-row">
          <div><h2>Packet-core identities</h2><p>Create, edit, clone, or remove identities in the selected profile’s Open5GS database.</p></div>
          <div className="subscriber-primary-actions">
            <button className="secondary" onClick={exportVisible} disabled={!subscribers.data?.items.length}><Download size={15} />Export</button>
            <Link className="action-link" to={`/subscribers/new?profile=${profile}`}><Plus size={16} />Add subscriber</Link>
          </div>
        </div>

        {connection.isLoading ? <LoadingState /> : null}
        {connection.error ? <ErrorAlert error={connection.error} onRetry={() => connection.refetch()} /> : null}
        {connection.data ? <details className="subscriber-connection-details"><summary><ShieldCheck size={16} />Database connection details</summary><SubscriberConnectionStatus status={connection.data} /></details> : null}
        {mutationError ? <ErrorAlert error={mutationError} /> : null}

        <section className="subscriber-registry panel">
          <div className="subscriber-toolbar">
            <label className="subscriber-profile-select">Network profile<select aria-label="Network profile" value={profile} onChange={(event) => setSearchParams({ profile: event.target.value })}>{subscriberProfiles.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
            <label className="search-field"><Search size={17} /><span className="sr-only">Search IMSI / MSISDN</span><input aria-label="Search IMSI / MSISDN" placeholder="Search IMSI or phone number…" value={search} onChange={(event) => { setOffset(0); setSearch(event.target.value); }} /></label>
            <ActionButton variant="secondary" onClick={() => subscribers.refetch()} loading={subscribers.isFetching}><RefreshCw size={15} />Refresh</ActionButton>
            <span className="registry-source">{connection.data?.database || 'Open5GS'} · {connection.data?.collection || 'subscribers'}</span>
          </div>

          {subscribers.isLoading ? <LoadingState /> : null}
          {subscribers.error ? <ErrorAlert error={subscribers.error} onRetry={() => subscribers.refetch()} /> : null}
          {subscribers.data && subscribers.data.items.length > 0 ? <SubscriberTable subscribers={subscribers.data.items} profile={profile} onClone={setCloneTarget} onDelete={setDeleteTarget} /> : null}
          {subscribers.data && subscribers.data.items.length === 0 ? <EmptyState title="No subscribers found" message={connectionOnline ? 'Add a subscriber to start managing SIM identities.' : 'The configured Open5GS database is unavailable. Check the connection details above.'} /> : null}

          {subscribers.data ? (
            <div className="pagination-row">
              <button className="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>Previous</button>
              <span>{subscriberCount === 0 ? '0' : `${offset + 1}–${Math.min(offset + pageSize, subscriberCount)}`} of {subscriberCount}</span>
              <button className="secondary" disabled={offset + pageSize >= subscriberCount} onClick={() => setOffset(offset + pageSize)}>Next</button>
            </div>
          ) : null}
        </section>

        <p className="subscriber-secret-note"><ShieldCheck size={15} />Authentication secrets are never shown in the list or exported file.</p>
      </>}

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
