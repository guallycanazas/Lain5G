import { useNavigate } from 'react-router-dom';
import { ErrorAlert } from '../components/ErrorAlert';
import { SubscriberForm } from '../components/subscribers/SubscriberForm';
import { useSubscriberActions } from '../hooks/useSubscribers';

export function SubscriberCreatePage() {
  const navigate = useNavigate();
  const actions = useSubscriberActions();
  return (
    <section className="panel page-panel">
      <div className="panel-heading"><h2>New subscriber</h2></div>
      {actions.create.error ? <ErrorAlert error={actions.create.error} /> : null}
      {actions.create.data ? <p className="result-line">{actions.create.data.message}</p> : null}
      <SubscriberForm mode="create" loading={actions.create.isPending} onSubmit={(payload) => actions.create.mutate(payload, { onSuccess: (result) => navigate(`/subscribers/${result.subscriber?.imsi || ''}`) })} />
    </section>
  );
}
