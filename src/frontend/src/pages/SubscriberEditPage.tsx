import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { SubscriberForm } from '../components/subscribers/SubscriberForm';
import { useSubscriberActions, useSubscriberDetail } from '../hooks/useSubscribers';
import type { SubscriberProfile } from '../types/subscriber';

export function SubscriberEditPage() {
  const { imsi } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const profile = (searchParams.get('profile') || '4g-lte-x310') as SubscriberProfile;
  const detail = useSubscriberDetail(imsi, profile);
  const actions = useSubscriberActions(profile);
  return (
    <section className="panel page-panel">
      <div className="panel-heading"><h2>Edit subscriber</h2><Link to={`/subscribers/${imsi}?profile=${profile}`}>Back to details</Link></div>
      {detail.isLoading ? <LoadingState /> : null}
      {detail.error ? <ErrorAlert error={detail.error} onRetry={() => detail.refetch()} /> : null}
      {actions.update.error ? <ErrorAlert error={actions.update.error} /> : null}
      {detail.data ? (
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
