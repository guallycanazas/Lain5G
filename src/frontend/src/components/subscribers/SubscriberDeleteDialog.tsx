import { useState } from 'react';
import type { SubscriberSummary } from '../../types/subscriber';

interface Props {
  subscriber: SubscriberSummary | null;
  loading?: boolean;
  onCancel: () => void;
  onConfirm: (imsi: string) => void;
}

export function SubscriberDeleteDialog({ subscriber, loading, onCancel, onConfirm }: Props) {
  const [confirmation, setConfirmation] = useState('');
  if (!subscriber) return null;
  const allowed = confirmation === subscriber.imsi;
  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="dialog" role="dialog" aria-modal="true">
        <h2>Delete subscriber</h2>
        <p>Type IMSI <strong>{subscriber.imsi}</strong> to confirm. This does not stop the laboratory or delete runs.</p>
        <label>Confirm IMSI<input value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></label>
        <div className="dialog-actions">
          <button onClick={onCancel}>Cancel</button>
          <button className="danger" disabled={!allowed || loading} onClick={() => onConfirm(subscriber.imsi)}>{loading ? 'Deleting...' : 'Delete'}</button>
        </div>
      </div>
    </div>
  );
}
