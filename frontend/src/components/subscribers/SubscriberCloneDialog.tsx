import { FormEvent, useState } from 'react';
import type { SubscriberClonePayload, SubscriberSummary } from '../../types/subscriber';

interface Props {
  subscriber: SubscriberSummary | null;
  loading?: boolean;
  onCancel: () => void;
  onConfirm: (imsi: string, payload: SubscriberClonePayload) => void;
}

export function SubscriberCloneDialog({ subscriber, loading, onCancel, onConfirm }: Props) {
  const [newImsi, setNewImsi] = useState('');
  const [newMsisdn, setNewMsisdn] = useState('');
  const [error, setError] = useState('');
  if (!subscriber) return null;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!/^\d{5,15}$/.test(newImsi) || newImsi === subscriber.imsi) {
      setError('The new IMSI is invalid or matches the source.');
      return;
    }
    if (newMsisdn && !/^\d{5,20}$/.test(newMsisdn)) {
      setError('The new MSISDN is invalid.');
      return;
    }
    setError('');
    onConfirm(subscriber.imsi, { new_imsi: newImsi, new_msisdn: newMsisdn || null });
  };
  return (
    <div className="dialog-backdrop" role="presentation">
      <form className="dialog" role="dialog" aria-modal="true" onSubmit={submit}>
        <h2>Clone subscriber</h2>
        <p>Source: <strong>{subscriber.imsi}</strong>. Credentials are copied internally but never displayed.</p>
        <label>New IMSI<input value={newImsi} onChange={(event) => setNewImsi(event.target.value)} /></label>
        <label>Optional new MSISDN<input value={newMsisdn} onChange={(event) => setNewMsisdn(event.target.value)} /></label>
        {error ? <p className="field-error">{error}</p> : null}
        <div className="dialog-actions">
          <button type="button" onClick={onCancel}>Cancel</button>
          <button disabled={loading}>{loading ? 'Cloning...' : 'Clone'}</button>
        </div>
      </form>
    </div>
  );
}
