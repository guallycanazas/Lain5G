import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { Activity, Boxes, Cpu, Play, RadioTower, ShieldAlert } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ContainerStatusTable } from '../components/ContainerStatusTable';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { LogsViewer } from '../components/LogsViewer';
import { StatusBadge } from '../components/StatusBadge';
import { RfStartDialog } from '../components/RfStartDialog';
import { SimulationStartDialog } from '../components/SimulationStartDialog';
import { TopologyPanel } from '../components/TopologyPanel';
import { ValidationTable } from '../components/ValidationTable';
import { deploymentsApi } from '../services/deploymentsApi';
import { runsApi } from '../services/runsApi';
import { useScenario, useScenarioActions, useScenarioStatus } from '../hooks/useDeployment';
import { useProfileComponents, usePullComponents } from '../hooks/usePreparation';
import { formatDate } from '../utils/dates';
import { getScenarioGuidance } from '../utils/scenarioGuidance';

const tabs = ['overview', 'topology', 'configuration', 'validation', 'logs', 'runs'] as const;
type Tab = typeof tabs[number];

export function ScenarioDetailPage() {
  const { scenarioId = '' } = useParams();
  const [tab, setTab] = useState<Tab>('overview');
  const [container, setContainer] = useState('all');
  const [confirm, setConfirm] = useState<'stop' | 'restart' | 'emergency' | null>(null);
  const [rfStartOpen, setRfStartOpen] = useState(false);
  const [simulationStartOpen, setSimulationStartOpen] = useState(false);
  const scenario = useScenario(scenarioId);
  const status = useScenarioStatus(scenarioId);
  const actions = useScenarioActions(scenarioId);
  const components = useProfileComponents(scenarioId);
  const coreComponents = useProfileComponents(scenarioId, true);
  const pullComponents = usePullComponents(scenarioId);
  const runs = useQuery({ queryKey: ['runs', scenarioId], queryFn: () => runsApi.list({ scenario: scenarioId, limit: 10 }), enabled: Boolean(scenarioId) });
  const latestRun = useQuery({ queryKey: ['run', runs.data?.[0]?.run_id], queryFn: () => runsApi.detail(runs.data?.[0]?.run_id || ''), enabled: Boolean(runs.data?.[0]?.run_id) });
  const logs = useQuery({ queryKey: ['logs', scenarioId, container], queryFn: () => deploymentsApi.logs(container === 'all' ? null : container, 300, scenarioId), enabled: false });
  const deployment = scenario.data;
  const guidance = getScenarioGuidance(scenarioId);
  const checks = Array.isArray(latestRun.data?.validation?.checks) ? latestRun.data.validation.checks as { id: string; status: any; detail: string | null }[] : [];
  const busy = Object.values(actions).some((action) => action.isPending) || pullComponents.isPending;
  const actionError = Object.values(actions).find((action) => action.error)?.error;
  const runConfirmed = () => {
    if (confirm === 'stop') actions.stop.mutate();
    if (confirm === 'restart') actions.restart.mutate();
    if (confirm === 'emergency') actions.emergencyStop.mutate();
    setConfirm(null);
  };

  if (!scenarioId) return null;
  return <div className="page-grid">
    <section className="hero-panel panel wide"><div><Link to="/scenarios" className="muted-text">Back to scenarios</Link><span className="eyebrow">{deployment?.rf_capable ? 'Guarded SDR workspace' : 'Software workspace'}</span><h1 className="hero-title">{deployment?.name || scenarioId}</h1><p className="page-subtitle">{deployment?.description}</p></div><div className="hero-actions"><StatusBadge status={status.data?.status || 'unknown'} /><ActionButton variant="secondary" onClick={() => status.refetch()} loading={status.isFetching}>Sync</ActionButton></div></section>
    {scenario.isLoading || status.isLoading ? <LoadingState /> : null}{scenario.error ? <ErrorAlert error={scenario.error} /> : null}{status.error ? <ErrorAlert error={status.error} onRetry={() => status.refetch()} /> : null}{actionError ? <ErrorAlert error={actionError} /> : null}
    {guidance ? <section className="panel wide scenario-guide"><div className="scenario-guide-intro"><span className="generation-mark">{guidance.generation}</span><div><span className="eyebrow">{guidance.variant}</span><h2>What is this profile?</h2><p>{guidance.purpose}</p></div></div><div className="scenario-guide-grid"><div><span>Includes</span><ul>{guidance.includes.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span>Not yet included</span><ul>{guidance.excludes.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span>Requirements</span><p>{guidance.hardware}</p></div></div></section> : null}
    {components.error ? <ErrorAlert error={components.error} onRetry={() => components.refetch()} /> : null}{pullComponents.error ? <ErrorAlert error={pullComponents.error} /> : null}
    {components.data ? <section className={`panel wide scenario-components ${components.data.ready ? 'ready' : 'missing'}`}><div><span className="eyebrow">Preparation</span><h3>{components.data.ready ? 'Components ready' : 'Images are missing for this profile'}</h3><p>{components.data.installed_count}/{components.data.total_count} installed. Downloading does not build images, start services, or enable RF.</p></div><div className="actions-row"><StatusBadge status={components.data.ready ? 'PASS' : 'FAIL'} kind="validation" />{!components.data.ready ? <ActionButton onClick={() => pullComponents.mutate()} loading={pullComponents.isPending}>Download missing</ActionButton> : null}<Link className="action-link" to="/preparation">View details</Link></div></section> : null}
    <section className={`panel wide command-center ${deployment?.rf_capable ? 'rf-command-center' : 'simulation-command-center'}`}><div className="panel-heading"><div><span className="eyebrow">Command bar</span><h3>{deployment?.rf_capable ? 'X310 launch sequence' : 'Software launch sequence'}</h3></div>{busy ? <StatusBadge status="validating" /> : null}</div>{deployment?.rf_capable ? <div className="rf-quick-start"><div><span className="rf-quick-icon"><RadioTower size={21} /></span><div><strong>Core + guarded RF</strong><p>One guided action runs core startup, strict preflight and the time-limited SDR service.</p></div></div><ActionButton variant="danger" disabled={busy || components.data?.ready !== true} onClick={() => setRfStartOpen(true)}><Play size={15} />Start X310 lab</ActionButton></div> : deployment?.supported_actions.includes('start') ? <div className="simulation-quick-start"><div><span className="simulation-quick-icon"><Boxes size={21} /></span><div><strong>Complete software lab</strong><p>Start the core, simulated RAN, UE and scenario-specific services.</p></div></div><ActionButton disabled={busy || components.data?.ready !== true} onClick={() => setSimulationStartOpen(true)}><Play size={15} />Start lab</ActionButton></div> : null}<div className="actions-row">
      {deployment?.supported_actions.includes('start-core') ? <ActionButton variant="secondary" disabled={busy || coreComponents.data?.ready !== true} loading={actions.startCore.isPending} onClick={() => actions.startCore.mutate()}><Cpu size={15} />Core only</ActionButton> : deployment?.supported_actions.includes('start-epc') ? <ActionButton disabled={busy || coreComponents.data?.ready !== true} loading={actions.startEpc.isPending} onClick={() => actions.startEpc.mutate()}>Start EPC without RF</ActionButton> : null}
      {deployment?.supported_actions.includes('hardware-check') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.hardwareCheck.isPending} onClick={() => actions.hardwareCheck.mutate()}><Activity size={15} />Hardware check</ActionButton> : null}
      {deployment?.supported_actions.includes('preflight') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.preflight.isPending} onClick={() => actions.preflight.mutate()}><ShieldAlert size={15} />Preflight</ActionButton> : null}
      {deployment?.supported_actions.includes('validate') ? <ActionButton variant="secondary" disabled={busy} loading={actions.validate.isPending} onClick={() => actions.validate.mutate()}>Validate</ActionButton> : null}
      {deployment?.supported_actions.includes('restart') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} onClick={() => setConfirm('restart')}>Restart</ActionButton> : null}
      {deployment?.supported_actions.includes('stop') ? <ActionButton variant="danger" disabled={busy} onClick={() => setConfirm('stop')}>Stop</ActionButton> : null}
      {deployment?.supported_actions.includes('emergency-stop') ? <ActionButton variant="danger" disabled={busy} onClick={() => setConfirm('emergency')}>Emergency stop</ActionButton> : null}
    </div></section>
    <section className="panel wide"><div className="tab-list" role="tablist">{tabs.map((item) => <button key={item} type="button" className={tab === item ? 'active' : ''} onClick={() => setTab(item)} role="tab" aria-selected={tab === item}>{item}</button>)}</div>
      {tab === 'overview' ? <div className="page-grid"><section><h3>Service inventory</h3><ContainerStatusTable containers={status.data?.containers || []} /></section><section><h3>Latest execution</h3>{latestRun.data ? <dl className="facts"><dt>Run ID</dt><dd><Link to={`/runs/${latestRun.data.run_id}`}>{latestRun.data.run_id}</Link></dd><dt>Result</dt><dd><StatusBadge status={String(latestRun.data.validation?.status || latestRun.data.metadata.status || 'unknown')} kind="validation" /></dd><dt>Finished</dt><dd>{formatDate(String(latestRun.data.metadata.finished_at || latestRun.data.metadata.started_at || ''))}</dd><dt>Commit</dt><dd><code>{String(latestRun.data.metadata.git_commit || 'Not recorded')}</code></dd></dl> : <div className="empty-state"><h3>No runs recorded</h3><p>Run validation to generate immutable evidence.</p></div>}</section></div> : null}
      {tab === 'topology' ? <TopologyPanel containers={status.data?.containers || []} checks={checks} checkedAt={status.data?.checked_at} title={`${deployment?.name || scenarioId} topology`} /> : null}
      {tab === 'configuration' ? <div className="empty-state"><h3>Permanent configuration workspace</h3><p>Profiles are edited under Deployments. Generated run evidence remains under runs/ and is never edited here.</p><Link className="action-link" to="/deployments">Open deployments</Link></div> : null}
      {tab === 'validation' ? <ValidationTable checks={checks} checkedAt={String(latestRun.data?.validation?.checked_at || '')} /> : null}
      {tab === 'logs' ? <><div className="logs-toolbar"><label>Service<select value={container} onChange={(event) => setContainer(event.target.value)}><option value="all">All services</option>{(deployment?.components || []).map((item) => <option key={item} value={item}>{item}</option>)}</select></label><ActionButton variant="secondary" onClick={() => logs.refetch()} loading={logs.isFetching}>Fetch logs</ActionButton><span className="log-state">WebSocket unavailable: manual fetch</span></div>{logs.error ? <ErrorAlert error={logs.error} onRetry={() => logs.refetch()} /> : null}<LogsViewer response={logs.data} /></> : null}
      {tab === 'runs' ? <div className="run-timeline">{runs.data?.length ? runs.data.map((run) => <Link className={`run-card ${String(run.status || '').toLowerCase()}`} to={`/runs/${run.run_id}`} key={run.run_id}><span className="run-marker" /><div><div className="run-title">{run.run_id}</div><div className="run-meta">{formatDate(run.finished_at || run.started_at)} · {run.git_commit || 'Commit not recorded'}</div></div><StatusBadge status={String(run.status || 'unknown')} kind="validation" /></Link>) : <div className="empty-state"><h3>No scenario runs</h3><p>Completed scripts will add evidence under runs/.</p></div>}</div> : null}
    </section>
    <ConfirmDialog open={confirm !== null} title={confirm === 'emergency' ? 'Emergency stop RF service' : confirm === 'restart' ? 'Restart deployment' : 'Stop deployment'} message="This request is executed by the backend through guarded operational scripts. Continue only if this is the intended laboratory action." confirmLabel={confirm === 'emergency' ? 'Emergency stop' : confirm === 'restart' ? 'Restart' : 'Stop'} onConfirm={runConfirmed} onCancel={() => setConfirm(null)} />
    <RfStartDialog scenarioId={scenarioId} open={rfStartOpen} loading={actions.startRf.isPending} onCancel={() => setRfStartOpen(false)} onConfirm={(payload) => actions.startRf.mutate(payload, { onSuccess: () => setRfStartOpen(false) })} />
    {deployment ? <SimulationStartDialog deployment={deployment} open={simulationStartOpen} loading={actions.start.isPending} onCancel={() => setSimulationStartOpen(false)} onConfirm={() => actions.start.mutate(undefined, { onSuccess: () => setSimulationStartOpen(false) })} /> : null}
  </div>;
}
