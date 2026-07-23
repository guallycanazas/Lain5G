import { useState } from 'react';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useScenarioActions } from '../hooks/useDeployment';
import { useProfiles } from '../hooks/useProfiles';

export function RfSafetyPage() {
  const profiles = useProfiles();
  const actions = useScenarioActions('4g-lte-x310');
  const [confirm, setConfirm] = useState(false);
  return <section className="page-panel"><div className="page-heading"><div><span className="eyebrow">Administration</span><h1>RF Safety</h1><p className="page-subtitle">Authorization and transmission remain enforced by local manifests and guarded backend scripts.</p></div><button className="danger" onClick={() => setConfirm(true)}>Emergency stop</button></div><section className="warning-box"><strong>RF controls are intentionally constrained.</strong><p>Starting RF is not exposed as a generic web action. Use preflight, local authorization and the documented lab procedure.</p></section>{profiles.isLoading ? <LoadingState /> : null}{profiles.error ? <ErrorAlert error={profiles.error} onRetry={() => profiles.refetch()} /> : null}{actions.emergencyStop.error ? <ErrorAlert error={actions.emergencyStop.error} /> : null}<div className="scenario-grid" style={{ marginTop: 18 }}>{profiles.data?.filter((profile) => profile.rf_capable).map((profile) => <article className="panel scenario-card" key={profile.profile}><div className="scenario-meta"><strong>{profile.profile}</strong><StatusBadge status={profile.rf_allowed ? 'warning' : 'stopped'} /></div><p className="muted-text">Local RF policy and safety manifest are evaluated server-side before any guarded action.</p><dl className="facts"><dt>RF capable</dt><dd>{String(profile.rf_capable)}</dd><dt>Default authorization</dt><dd>{String(profile.rf_allowed)}</dd></dl></article>)}</div><ConfirmDialog open={confirm} title="Emergency stop RF service" message="This sends the guarded emergency-stop action for the LTE X310 deployment. It stops the RF service and clears the local active-session marker." confirmLabel="Emergency stop" onConfirm={() => { actions.emergencyStop.mutate(); setConfirm(false); }} onCancel={() => setConfirm(false)} /></section>;
}
