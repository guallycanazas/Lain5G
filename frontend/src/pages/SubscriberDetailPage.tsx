import { Link, useParams } from 'react-router-dom';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { useSubscriberDetail } from '../hooks/useSubscribers';
import { formatDate } from '../utils/dates';

export function SubscriberDetailPage() {
  const { imsi } = useParams();
  const detail = useSubscriberDetail(imsi);
  const subscriber = detail.data;
  return (
    <section className="panel page-panel">
      <div className="panel-heading">
        <h2>Subscriber details</h2>
        <div className="inline-actions">
          <Link to="/subscribers">Back</Link>
          {subscriber ? <Link to={`/subscribers/${subscriber.imsi}/edit`}>Edit</Link> : null}
        </div>
      </div>
      {detail.isLoading ? <LoadingState /> : null}
      {detail.error ? <ErrorAlert error={detail.error} onRetry={() => detail.refetch()} /> : null}
      {subscriber ? (
        <>
          <dl className="facts compact">
            <dt>IMSI</dt><dd>{subscriber.imsi}</dd>
            <dt>MSISDN</dt><dd>{subscriber.msisdn || 'n/a'}</dd>
            <dt>DNN</dt><dd>{subscriber.dnn || 'n/a'}</dd>
            <dt>Slice</dt><dd>{subscriber.sst ?? 'n/a'} / {subscriber.sd || 'n/a'}</dd>
            <dt>K</dt><dd>{subscriber.security.k_configured ? 'Configured' : 'Not configured'}</dd>
            <dt>OP</dt><dd>{subscriber.security.op_configured ? 'Configured' : 'Not configured'}</dd>
            <dt>OPc</dt><dd>{subscriber.security.opc_configured ? 'Configured' : 'Not configured'}</dd>
            <dt>AMF</dt><dd>{subscriber.security.amf || 'n/a'}</dd>
            <dt>SQN</dt><dd>{subscriber.security.sqn || 'n/a'}</dd>
            <dt>Checked</dt><dd>{formatDate(subscriber.checked_at)}</dd>
          </dl>
          <p className="muted-text">{subscriber.note}</p>
        </>
      ) : null}
    </section>
  );
}
