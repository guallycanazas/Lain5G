import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, Navigate, useParams } from 'react-router';
import { Activity, Boxes, Cpu, Play, RadioTower, ShieldAlert } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ComponentPullProgress } from '../components/ComponentPullProgress';
import { ContainerStatusTable } from '../components/ContainerStatusTable';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { LogsViewer } from '../components/LogsViewer';
import { StatusBadge } from '../components/StatusBadge';
import { RfStartDialog } from '../components/RfStartDialog';
import { ScenarioValidationPanel } from '../components/ScenarioValidationPanel';
import { SimulationStartDialog } from '../components/SimulationStartDialog';
import { TopologyPanel } from '../components/TopologyPanel';
import { ValidationTable } from '../components/ValidationTable';
import { deploymentsApi } from '../services/deploymentsApi';
import { runsApi } from '../services/runsApi';
import { useScenario, useScenarioActions, useScenarioStatus } from '../hooks/useDeployment';
import { useProfileComponents, usePullComponents } from '../hooks/usePreparation';
import { formatDate } from '../utils/dates';
import { getScenarioGuidance } from '../utils/scenarioGuidance';
import type { RfStartPayload } from '../types/deployment';

const tabs = ['overview', 'topology', 'configuration', 'validation', 'logs', 'runs'] as const;
const publicScenarios = new Set(['4g-lte-sim', '4g-lte-x310', '5g-sa', '5g-sa-x310']);
type Tab = typeof tabs[number];

export function ScenarioDetailPage() {
  const { scenarioId = '' } = useParams();
  const [tab, setTab] = useState<Tab>('overview');
  const [container, setContainer] = useState('all');
  const [confirm, setConfirm] = useState<'stop' | 'restart' | 'emergency' | null>(null);
  const [rfStartOpen, setRfStartOpen] = useState(false);
  const [simulationStartOpen, setSimulationStartOpen] = useState(false);
  const [startAfterPull, setStartAfterPull] = useState(false);
  const startIntentToken = useRef(0);
  const handledPullJob = useRef<string | null>(null);
  const scenario = useScenario(scenarioId);
  const status = useScenarioStatus(scenarioId);
  const actions = useScenarioActions(scenarioId);
  const components = useProfileComponents(scenarioId);
  const coreComponents = useProfileComponents(scenarioId, true);
  const pullComponents = usePullComponents(scenarioId);
  const runs = useQuery({ queryKey: ['runs', scenarioId], queryFn: () => runsApi.list({ scenario: scenarioId, limit: 10 }), enabled: Boolean(scenarioId) });
  const latestRun = useQuery({ queryKey: ['run', runs.data?.[0]?.run_id], queryFn: () => runsApi.detail(runs.data?.[0]?.run_id || ''), enabled: Boolean(runs.data?.[0]?.run_id) });
  const latestValidationSummary = runs.data?.find((run) => ['PASS', 'FAIL', 'PARTIAL', 'WARNING'].includes(String(run.status || '').toUpperCase()));
  const latestValidationRun = useQuery({ queryKey: ['run', latestValidationSummary?.run_id], queryFn: () => runsApi.detail(latestValidationSummary?.run_id || ''), enabled: Boolean(latestValidationSummary?.run_id) });
  const logs = useQuery({ queryKey: ['logs', scenarioId, container], queryFn: () => deploymentsApi.logs(container === 'all' ? null : container, 300, scenarioId), enabled: false });
  const deployment = scenario.data;
  const guidance = getScenarioGuidance(scenarioId);
  const checks = Array.isArray(latestValidationRun.data?.validation?.checks) ? latestValidationRun.data.validation.checks as { id: string; status: any; detail: string | null }[] : [];
  const validationStatus = String(latestValidationRun.data?.validation?.status || latestValidationSummary?.status || 'NOT_TESTED');
  const validationCheckedAt = String(latestValidationRun.data?.validation?.checked_at || latestValidationRun.data?.metadata.finished_at || '');
  const busy = Object.values(actions).some((action) => action.isPending) || pullComponents.isPending;
  const actionError = Object.values(actions).find((action) => action.error)?.error;
  const missingImages = components.data?.images.filter((image) => !image.installed) || [];
  const runConfirmed = () => {
    if (confirm === 'stop') actions.stop.mutate();
    if (confirm === 'restart') actions.restart.mutate();
    if (confirm === 'emergency') actions.emergencyStop.mutate();
    setConfirm(null);
  };
  const confirmSimulationStart = () => {
    if (components.data?.ready) {
      actions.start.mutate(undefined, { onSuccess: () => setSimulationStartOpen(false) });
      return;
    }
    handledPullJob.current = pullComponents.job?.job_id || null;
    const token = ++startIntentToken.current;
    setStartAfterPull(true);
    pullComponents.mutate(undefined, { onError: () => { if (startIntentToken.current === token) setStartAfterPull(false); } });
  };
  const confirmRfStart = (payload: RfStartPayload) => {
    if (components.data?.ready) {
      actions.startRf.mutate(payload, { onSuccess: () => setRfStartOpen(false) });
      return;
    }
    pullComponents.mutate();
  };
  useEffect(() => {
    const job = pullComponents.job;
    if (!startAfterPull || !job || handledPullJob.current === job.job_id) return;
    if (job.state === 'failed') {
      handledPullJob.current = job.job_id;
      setStartAfterPull(false);
      return;
    }
    if (job.state !== 'succeeded') return;
    handledPullJob.current = job.job_id;
    const token = startIntentToken.current;
    void components.refetch().then((result) => {
      if (startIntentToken.current !== token) return;
      setStartAfterPull(false);
      if (result.data?.ready) actions.start.mutate(undefined, { onSuccess: () => setSimulationStartOpen(false) });
    });
  }, [actions.start, components, pullComponents.job, startAfterPull]);
  useEffect(() => () => { startIntentToken.current += 1; }, []);

  if (!scenarioId || !publicScenarios.has(scenarioId)) return <Navigate to="/scenarios" replace />;
  return <div className="page-grid">
    <section className="hero-panel panel wide"><div><Link to="/scenarios" className="muted-text">Back to scenarios</Link><span className="eyebrow">{deployment?.rf_capable ? 'Guarded SDR workspace' : 'Software workspace'}</span><h1 className="hero-title">{deployment?.name || scenarioId}</h1><p className="page-subtitle">{deployment?.description}</p></div><div className="hero-actions"><StatusBadge status={status.data?.status || 'unknown'} /><ActionButton variant="secondary" onClick={() => status.refetch()} loading={status.isFetching}>Sync</ActionButton></div></section>
    {scenario.isLoading || status.isLoading ? <LoadingState /> : null}{scenario.error ? <ErrorAlert error={scenario.error} /> : null}{status.error ? <ErrorAlert error={status.error} onRetry={() => status.refetch()} /> : null}{actionError ? <ErrorAlert error={actionError} /> : null}
    {guidance ? <section className="panel wide scenario-guide"><div className="scenario-guide-intro"><span className="generation-mark">{guidance.generation}</span><div><span className="eyebrow">{guidance.variant}</span><h2>What is this profile?</h2><p>{guidance.purpose}</p></div></div><div className="scenario-guide-grid"><div><span>Includes</span><ul>{guidance.includes.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span>Not yet included</span><ul>{guidance.excludes.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span>Requirements</span><p>{guidance.hardware}</p></div></div></section> : null}
    {components.error ? <ErrorAlert error={components.error} onRetry={() => components.refetch()} /> : null}{pullComponents.error ? <ErrorAlert error={pullComponents.error} /> : null}
    {components.data ? <section className={`panel wide scenario-components ${components.data.ready ? 'ready' : 'missing'}`}><div><span className="eyebrow">Preparation</span><h3>{components.data.ready ? 'Components ready' : `${missingImages.length} component${missingImages.length === 1 ? '' : 's'} missing`}</h3><p>{components.data.installed_count}/{components.data.total_count} installed. Downloading does not build images, start services, or enable RF.</p></div><div className="actions-row"><StatusBadge status={components.data.ready ? 'PASS' : 'FAIL'} kind="validation" />{!components.data.ready ? <ActionButton onClick={() => pullComponents.mutate()} loading={pullComponents.isPending}>Download missing</ActionButton> : null}<Link className="action-link" to="/preparation">View details</Link></div>{pullComponents.job ? <ComponentPullProgress job={pullComponents.job} /> : null}</section> : null}
    <section className={`panel wide command-center ${deployment?.rf_capable ? 'rf-command-center' : 'simulation-command-center'}`}><div className="panel-heading"><div><span className="eyebrow">Command bar</span><h3>{deployment?.rf_capable ? 'X310 launch sequence' : 'Software launch sequence'}</h3></div>{busy ? <StatusBadge status="validating" /> : null}</div>{deployment?.rf_capable ? <div className="rf-quick-start"><div><span className="rf-quick-icon"><RadioTower size={21} /></span><div><strong>Core + guarded RF</strong><p>One guided action runs core startup, strict preflight and the time-limited SDR service.</p></div></div><ActionButton variant="danger" disabled={busy || components.isLoading} onClick={() => setRfStartOpen(true)}><Play size={15} />Start X310 lab</ActionButton></div> : deployment?.supported_actions.includes('start') ? <div className="simulation-quick-start"><div><span className="simulation-quick-icon"><Boxes size={21} /></span><div><strong>Complete software lab</strong><p>Start the core, simulated RAN, UE and scenario-specific services.</p></div></div><ActionButton disabled={busy || components.isLoading} onClick={() => setSimulationStartOpen(true)}><Play size={15} />Start lab</ActionButton></div> : null}<div className="actions-row">
      {deployment?.supported_actions.includes('start-core') ? <ActionButton variant="secondary" disabled={busy || coreComponents.data?.ready !== true} loading={actions.startCore.isPending} onClick={() => actions.startCore.mutate()}><Cpu size={15} />{scenarioId.startsWith('4g-') ? 'EPC + IMS, no RF' : '5GC + IMS, no RF'}</ActionButton> : deployment?.supported_actions.includes('start-epc') ? <ActionButton disabled={busy || coreComponents.data?.ready !== true} loading={actions.startEpc.isPending} onClick={() => actions.startEpc.mutate()}>EPC + IMS, no RF</ActionButton> : null}
      {deployment?.supported_actions.includes('hardware-check') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.hardwareCheck.isPending} onClick={() => actions.hardwareCheck.mutate()}><Activity size={15} />Hardware check</ActionButton> : null}
      {deployment?.supported_actions.includes('preflight') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.preflight.isPending} onClick={() => actions.preflight.mutate()}><ShieldAlert size={15} />Preflight</ActionButton> : null}
      {deployment?.supported_actions.includes('validate') ? <ActionButton variant="secondary" disabled={busy} loading={actions.validate.isPending} onClick={() => actions.validate.mutate()}>Validate</ActionButton> : null}
      {deployment?.supported_actions.includes('restart') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} onClick={() => setConfirm('restart')}>Restart</ActionButton> : null}
      {deployment?.supported_actions.includes('stop') ? <ActionButton variant="danger" disabled={busy} onClick={() => setConfirm('stop')}>Stop</ActionButton> : null}
      {deployment?.supported_actions.includes('emergency-stop') ? <ActionButton variant="danger" disabled={busy} onClick={() => setConfirm('emergency')}>Emergency stop</ActionButton> : null}
    </div></section>
    <section className="panel wide"><div className="tab-list" role="tablist">{tabs.map((item) => <button key={item} type="button" className={tab === item ? 'active' : ''} onClick={() => setTab(item)} role="tab" aria-selected={tab === item}>{item}</button>)}</div>
      {tab === 'overview' ? <div className="page-grid scenario-overview-grid"><section><h3>Service inventory</h3><p className="muted-text scenario-section-intro">Expected profile services are compared with containers currently detected by Docker.</p><ContainerStatusTable containers={status.data?.containers || []} expectedServices={deployment?.components || []} conditionalServices={deployment?.conditional_components || []} deploymentState={status.data?.status || 'unknown'} /></section><section className="scenario-validation-column"><div><h3>Operational validation</h3><p className="muted-text scenario-section-intro">Protocol, UE, user-plane and hardware evidence from the latest completed validation.</p><ScenarioValidationPanel expectedChecks={deployment?.validation_checks || []} checks={checks} status={validationStatus} checkedAt={validationCheckedAt} runId={latestValidationSummary?.run_id} loading={actions.validate.isPending} onValidate={() => actions.validate.mutate()} /></div><div className="scenario-latest-run"><h3>Latest execution</h3>{latestRun.data ? <dl className="facts"><dt>Run ID</dt><dd><Link to={`/runs/${latestRun.data.run_id}`}>{latestRun.data.run_id}</Link></dd><dt>Result</dt><dd><StatusBadge status={String(latestRun.data.validation?.status || latestRun.data.metadata.status || 'unknown')} kind="validation" /></dd><dt>Finished</dt><dd>{formatDate(String(latestRun.data.metadata.finished_at || latestRun.data.metadata.started_at || ''))}</dd><dt>Commit</dt><dd><code>{String(latestRun.data.metadata.git_commit || 'Not recorded')}</code></dd></dl> : <div className="empty-state"><h3>No runs recorded</h3><p>Run validation to generate immutable evidence.</p></div>}</div></section></div> : null}
      {tab === 'topology' ? <TopologyPanel containers={status.data?.containers || []} checks={checks} checkedAt={status.data?.checked_at} title={`${deployment?.name || scenarioId} topology`} /> : null}
      {tab === 'configuration' ? <div className="empty-state"><h3>Permanent configuration workspace</h3><p>Profiles are edited under Deployments. Generated run evidence remains under runs/ and is never edited here.</p><Link className="action-link" to="/deployments">Open deployments</Link></div> : null}
      {tab === 'validation' ? <ValidationTable checks={checks} expectedChecks={deployment?.validation_checks || []} checkedAt={validationCheckedAt} /> : null}
      {tab === 'logs' ? <><div className="logs-toolbar"><label>Service<select value={container} onChange={(event) => setContainer(event.target.value)}><option value="all">All services</option>{(deployment?.components || []).map((item) => <option key={item} value={item}>{item}</option>)}</select></label><ActionButton variant="secondary" onClick={() => logs.refetch()} loading={logs.isFetching}>Fetch logs</ActionButton><span className="log-state">WebSocket unavailable: manual fetch</span></div>{logs.error ? <ErrorAlert error={logs.error} onRetry={() => logs.refetch()} /> : null}<LogsViewer response={logs.data} /></> : null}
      {tab === 'runs' ? <div className="run-timeline">{runs.data?.length ? runs.data.map((run) => <Link className={`run-card ${String(run.status || '').toLowerCase()}`} to={`/runs/${run.run_id}`} key={run.run_id}><span className="run-marker" /><div><div className="run-title">{run.run_id}</div><div className="run-meta">{formatDate(run.finished_at || run.started_at)} · {run.git_commit || 'Commit not recorded'}</div></div><StatusBadge status={String(run.status || 'unknown')} kind="validation" /></Link>) : <div className="empty-state"><h3>No scenario runs</h3><p>Completed scripts will add evidence under runs/.</p></div>}</div> : null}
    </section>
    <ConfirmDialog open={confirm !== null} title={confirm === 'emergency' ? 'Emergency stop RF service' : confirm === 'restart' ? 'Restart deployment' : 'Stop deployment'} message="This request is executed by the backend through guarded operational scripts. Continue only if this is the intended laboratory action." confirmLabel={confirm === 'emergency' ? 'Emergency stop' : confirm === 'restart' ? 'Restart' : 'Stop'} onConfirm={runConfirmed} onCancel={() => setConfirm(null)} />
    <RfStartDialog scenarioId={scenarioId} open={rfStartOpen} loading={actions.startRf.isPending || pullComponents.isPending} missingImages={missingImages} pullJob={pullComponents.job} onCancel={() => setRfStartOpen(false)} onConfirm={confirmRfStart} />
    {deployment ? <SimulationStartDialog deployment={deployment} open={simulationStartOpen} loading={actions.start.isPending || pullComponents.isPending} missingImages={missingImages} pullJob={pullComponents.job} onCancel={() => { startIntentToken.current += 1; setStartAfterPull(false); setSimulationStartOpen(false); }} onConfirm={confirmSimulationStart} /> : null}
  </div>;
}
