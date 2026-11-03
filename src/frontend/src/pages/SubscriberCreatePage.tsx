import { useNavigate, useSearchParams } from 'react-router';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { SubscriberForm } from '../components/subscribers/SubscriberForm';
import { SubscriberDatabaseUnavailable } from '../components/subscribers/SubscriberDatabaseUnavailable';
import { useSubscriberActions, useSubscriberConnection } from '../hooks/useSubscribers';
import type { SubscriberProfile } from '../types/subscriber';

export function SubscriberCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const profile = (searchParams.get('profile') || '4g-lte-x310') as SubscriberProfile;
  const connection = useSubscriberConnection(profile);
  const actions = useSubscriberActions(profile);
  return (
    <section className="panel page-panel">
      <div className="panel-heading"><h2>New subscriber</h2></div>
      {connection.isLoading ? <LoadingState /> : null}
      {connection.error ? <ErrorAlert error={connection.error} onRetry={() => connection.refetch()} /> : null}
      {connection.data && connection.data.status !== 'connected' ? <SubscriberDatabaseUnavailable profile={profile} status={connection.data.status} onRetry={() => void connection.refetch()} retrying={connection.isFetching} /> : null}
      {connection.data?.status === 'connected' ? <>
        {actions.create.error ? <ErrorAlert error={actions.create.error} /> : null}
        {actions.create.data ? <p className="result-line">{actions.create.data.message}</p> : null}
        <SubscriberForm mode="create" loading={actions.create.isPending} onSubmit={(payload) => actions.create.mutate(payload, { onSuccess: (result) => navigate(`/subscribers/${result.subscriber?.imsi || ''}?profile=${profile}`) })} />
      </> : null}
    </section>
  );
}
