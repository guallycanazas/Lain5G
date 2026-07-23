import { Link } from 'react-router-dom';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useDeployments } from '../hooks/useDeployment';
import { useRuns } from '../hooks/useRuns';
import { formatDate } from '../utils/dates';
import { getScenarioGuidance } from '../utils/scenarioGuidance';

export function ScenariosPage() {
  const deployments = useDeployments();
  const runs = useRuns();
  const deploymentList = Array.isArray(deployments.data) ? deployments.data : [];
  const runList = Array.isArray(runs.data) ? runs.data : [];
  return <section className="page-panel">
    <div className="page-heading"><div><span className="eyebrow">Operation</span><h1>Scenarios</h1><p className="page-subtitle">Select a laboratory workspace. Each scenario retains its own deployment, evidence and safety constraints.</p></div></div>
    {deployments.isLoading ? <LoadingState /> : null}
    {deployments.error ? <ErrorAlert error={deployments.error} onRetry={() => deployments.refetch()} /> : null}
    {(['4G', '5G'] as const).map((generation) => <section className="scenario-family" key={generation}>
      <div className="scenario-family-heading"><span>{generation}</span><div><h2>{generation} laboratory profiles</h2><p>{generation === '4G' ? 'LTE simulation or guarded VoLTE RF preparation.' : 'SA simulation or guarded VoNR RF preparation.'}</p></div></div>
      <div className="scenario-grid">
        {deploymentList.filter((deployment) => getScenarioGuidance(deployment.id)?.generation === generation).map((deployment) => {
          const lastRun = runList.find((run) => run.scenario === deployment.id);
          const guidance = getScenarioGuidance(deployment.id);
          return <article className="panel scenario-card card-interactive" key={deployment.id}>
            <div className="scenario-meta"><span className="eyebrow">{guidance?.variant || deployment.mode}</span><StatusBadge status={deployment.status} /></div>
            <div><h3>{deployment.name}</h3><p className="scenario-purpose">{guidance?.purpose || deployment.description}</p></div>
            {guidance ? <div className="scenario-definition"><div><span>Includes</span><ul>{guidance.includes.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span>Not yet included</span><ul>{guidance.excludes.map((item) => <li key={item}>{item}</li>)}</ul></div><div className="scenario-hardware"><span>Hardware</span><p>{guidance.hardware}</p></div></div> : null}
            <dl className="facts scenario-facts"><dt>Technical ID</dt><dd><code>{deployment.id}</code></dd><dt>Validation</dt><dd>{deployment.validation_checks.length} checks</dd><dt>Latest run</dt><dd>{lastRun ? formatDate(lastRun.finished_at || lastRun.started_at) : 'No run recorded'}</dd></dl>
            {deployment.rf_capable ? <div className="warning-box">Guarded RF preparation does not establish a VoLTE or VoNR call without correlated UE, SIP, and RTP evidence.</div> : null}
            <div className="scenario-card-footer"><span className="muted-text">{deployment.rf_capable ? 'Real hardware' : 'Software only'}</span><Link className="action-link" to={`/scenarios/${deployment.id}`}>Open scenario</Link></div>
          </article>;
        })}
      </div>
    </section>)}
  </section>;
}
