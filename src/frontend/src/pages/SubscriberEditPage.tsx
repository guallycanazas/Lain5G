import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { SubscriberForm } from '../components/subscribers/SubscriberForm';
import { SubscriberDatabaseUnavailable } from '../components/subscribers/SubscriberDatabaseUnavailable';
import { useSubscriberActions, useSubscriberConnection, useSubscriberDetail } from '../hooks/useSubscribers';
import type { SubscriberProfile } from '../types/subscriber';

export function SubscriberEditPage() {
  const { imsi } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const profile = (searchParams.get('profile') || '4g-lte-x310') as SubscriberProfile;
  const connection = useSubscriberConnection(profile);
  const connectionOnline = connection.data?.status === 'connected';
  const detail = useSubscriberDetail(imsi, profile, connectionOnline);
  const actions = useSubscriberActions(profile);
  return (
    <section className="panel page-panel">
      <div className="panel-heading"><h2>Edit subscriber</h2><Link to={`/subscribers/${imsi}?profile=${profile}`}>Back to details</Link></div>
      {connection.isLoading ? <LoadingState /> : null}
      {connection.error ? <ErrorAlert error={connection.error} onRetry={() => connection.refetch()} /> : null}
      {connection.data && !connectionOnline ? <SubscriberDatabaseUnavailable profile={profile} status={connection.data.status} onRetry={() => void connection.refetch()} retrying={connection.isFetching} /> : null}
      {connectionOnline && detail.isLoading ? <LoadingState /> : null}
      {connectionOnline && detail.error ? <ErrorAlert error={detail.error} onRetry={() => detail.refetch()} /> : null}
      {connectionOnline && actions.update.error ? <ErrorAlert error={actions.update.error} /> : null}
      {connectionOnline && detail.data ? (
        <SubscriberForm
          mode="edit"
          initial={detail.data}
          loading={actions.update.isPending}
          onSubmit={(payload) => actions.update.mutate({ imsi: detail.data.imsi, payload }, { onSuccess: () => navigate(`/subscribers/${detail.data?.imsi}?profile=${profile}`) })}
        />
      ) : null}
    </section>
  );
}
