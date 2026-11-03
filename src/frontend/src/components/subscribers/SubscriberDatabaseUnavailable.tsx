import { Link } from 'react-router';
import { AlertCircle, ArrowRight, RefreshCw } from 'lucide-react';
import type { SubscriberConnectionState, SubscriberProfile } from '../../types/subscriber';

const profileNames: Record<SubscriberProfile, string> = {
  '4g-lte-x310': '4G LTE X310',
  '5g-sa-x310': '5G SA X310',
  '5g-nsa-x310': '5G NSA X310',
};

const causes: Partial<Record<SubscriberConnectionState, string>> = {
  disconnected: 'The profile database is stopped.',
  timeout: 'The profile database did not respond in time.',
  misconfigured: 'The profile database connection needs configuration.',
  error: 'The profile database could not be reached.',
};

export function SubscriberDatabaseUnavailable({
  profile,
  status,
  onRetry,
  retrying = false,
}: {
  profile: SubscriberProfile;
  status?: SubscriberConnectionState;
  onRetry?: () => void;
  retrying?: boolean;
}) {
  const cause = status ? causes[status] || 'The profile database status is not available yet.' : 'The profile database status is not available yet.';
  return (
    <div className="subscriber-db-unavailable" role="status">
      <span className="subscriber-db-unavailable-icon"><AlertCircle size={18} /></span>
      <div className="subscriber-db-unavailable-copy">
        <strong>Subscriber database unavailable</strong>
        <p>{cause} {profileNames[profile]} subscriber records were not loaded, and no changes were sent.</p>
        <p>Check the profile service state before starting it. RF profiles can start radio services when you use their start controls.</p>
        <div className="inline-actions">
          <Link className="action-link" to={`/scenarios/${profile}`}>Open profile status <ArrowRight size={15} /></Link>
          {onRetry ? <button className="secondary" type="button" onClick={onRetry} disabled={retrying}><RefreshCw size={14} />{retrying ? 'Checking…' : 'Retry connection'}</button> : null}
        </div>
      </div>
    </div>
  );
}
