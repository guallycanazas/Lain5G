import { useState } from 'react';
import { Link } from 'react-router-dom';
import { EmptyState } from '../components/EmptyState';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useDeployments } from '../hooks/useDeployment';
import { useRuns } from '../hooks/useRuns';
import { formatDate } from '../utils/dates';

export function RunsPage() {
  const [scenario, setScenario] = useState('');
  const [status, setStatus] = useState('');
  const deployments = useDeployments();
  const runs = useRuns({ scenario: scenario || undefined, status: status || undefined, limit: 100 });
  const deploymentList = Array.isArray(deployments.data) ? deployments.data : [];
  return <section className="page-panel"><div className="page-heading"><div><span className="eyebrow">Observability</span><h1>Runs</h1><p className="page-subtitle">Immutable execution evidence read from the local runs directory.</p></div></div><div className="panel controls-panel"><label>Scenario<select value={scenario} onChange={(event) => setScenario(event.target.value)}><option value="">All scenarios</option>{deploymentList.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Result<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All results</option><option value="PASS">PASS</option><option value="FAIL">FAIL</option><option value="WARNING">WARNING</option></select></label></div>{runs.isLoading ? <LoadingState /> : null}{runs.error ? <ErrorAlert error={runs.error} onRetry={() => runs.refetch()} /> : null}{runs.data?.length ? <div className="run-timeline" style={{ marginTop: 18 }}>{runs.data.map((run) => <Link className={`run-card ${String(run.status || '').toLowerCase()}`} to={`/runs/${run.run_id}`} key={run.run_id}><span className="run-marker" /><div><div className="run-title">{run.run_id}</div><div className="run-meta">{run.scenario || 'Unknown scenario'} · {formatDate(run.started_at)} to {formatDate(run.finished_at)} · {run.git_commit || 'Commit not recorded'}</div></div><StatusBadge status={String(run.status || 'unknown')} kind="validation" /></Link>)}</div> : null}{runs.data && runs.data.length === 0 ? <EmptyState title="No matching runs" message="Completed validation scripts will add immutable evidence under runs/." /> : null}</section>;
}
