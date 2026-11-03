import { Link, useParams, useSearchParams } from 'react-router';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { SubscriberDatabaseUnavailable } from '../components/subscribers/SubscriberDatabaseUnavailable';
import { useSubscriberConnection, useSubscriberDetail } from '../hooks/useSubscribers';
import { formatDate } from '../utils/dates';
import type { SubscriberProfile } from '../types/subscriber';

export function SubscriberDetailPage() {
  const { imsi } = useParams();
  const [searchParams] = useSearchParams();
  const profile = (searchParams.get('profile') || '4g-lte-x310') as SubscriberProfile;
  const connection = useSubscriberConnection(profile);
  const connectionOnline = connection.data?.status === 'connected';
  const detail = useSubscriberDetail(imsi, profile, connectionOnline);
  const subscriber = detail.data;
  return (
    <section className="panel page-panel">
      <div className="panel-heading">
        <h2>Subscriber details</h2>
        <div className="inline-actions">
          <Link to={`/subscribers?profile=${profile}`}>Back</Link>
          {subscriber ? <Link to={`/subscribers/${subscriber.imsi}/edit?profile=${profile}`}>Edit</Link> : null}
        </div>
      </div>
      {connection.isLoading ? <LoadingState /> : null}
      {connection.error ? <ErrorAlert error={connection.error} onRetry={() => connection.refetch()} /> : null}
      {connection.data && !connectionOnline ? <SubscriberDatabaseUnavailable profile={profile} status={connection.data.status} onRetry={() => void connection.refetch()} retrying={connection.isFetching} /> : null}
      {connectionOnline && detail.isLoading ? <LoadingState /> : null}
      {connectionOnline && detail.error ? <ErrorAlert error={detail.error} onRetry={() => detail.refetch()} /> : null}
      {connectionOnline && subscriber ? (
        <>
          <dl className="facts compact">
            <dt>IMSI</dt><dd>{subscriber.imsi}</dd>
            <dt>MSISDN</dt><dd>{subscriber.msisdn || 'n/a'}</dd>
            <dt>APN / DNN</dt><dd>{(subscriber.apns?.length ? subscriber.apns : subscriber.dnn ? [subscriber.dnn] : []).join(', ') || 'n/a'}</dd>
            <dt>Slice</dt><dd>{subscriber.sst ?? 'n/a'} / {subscriber.sd || 'n/a'}</dd>
            <dt>K</dt><dd>{subscriber.security.k_configured ? 'Configured' : 'Not configured'}</dd>
            <dt>OP</dt><dd>{subscriber.security.op_configured ? 'Configured' : 'Not configured'}</dd>
            <dt>OPc</dt><dd>{subscriber.security.opc_configured ? 'Configured' : 'Not configured'}</dd>
            <dt>AMF</dt><dd>{subscriber.security.amf || 'n/a'}</dd>
            <dt>SQN</dt><dd>{subscriber.security.sqn || 'n/a'}</dd>
            <dt>Checked</dt><dd>{formatDate(subscriber.checked_at)}</dd>
          </dl>
        </>
      ) : null}
    </section>
  );
}
