import { StatusBadge } from '../StatusBadge';
import { Activity, Clock3, Database, HardDrive, Server } from 'lucide-react';
import type { SubscriberConnectionStatus as Status } from '../../types/subscriber';

export function SubscriberConnectionStatus({ status }: { status: Status }) {
  return (
    <section className={`connection-card connection-${status.status}`}>
      <div className="connection-card-head"><div className="connection-title"><span><Database size={19} /></span><div><small>DATA SOURCE</small><strong>Open5GS MongoDB</strong></div></div><StatusBadge status={status.status === 'connected' ? 'running' : status.status === 'dry_run' ? 'dry_run' : 'error'} /></div>
      <dl className="connection-metrics">
        <div><dt><HardDrive size={14} />Database</dt><dd>{status.database}</dd></div>
        <div><dt><Database size={14} />Collection</dt><dd>{status.collection}</dd></div>
        <div><dt><Server size={14} />Endpoint</dt><dd>{status.server}</dd></div>
        <div><dt><Clock3 size={14} />Latency</dt><dd>{status.latency_ms === null ? 'n/a' : `${status.latency_ms} ms`}</dd></div>
      </dl>
      {status.message ? <p className="connection-detail"><Activity size={14} />{status.message}</p> : null}
    </section>
  );
}
