import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, Navigate, useParams } from 'react-router';
import { Activity, ArrowRight, Boxes, Cpu, Play, RadioTower, ShieldAlert, Wrench } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ComponentPullProgress } from '../components/ComponentPullProgress';
import { ContainerStatusTable } from '../components/ContainerStatusTable';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { LogsViewer } from '../components/LogsViewer';
import { OperationalProofPanel } from '../components/OperationalProofPanel';
import { StatusBadge } from '../components/StatusBadge';
import { RfStartDialog } from '../components/RfStartDialog';
import { ScenarioValidationPanel } from '../components/ScenarioValidationPanel';
import { SimulationStartDialog } from '../components/SimulationStartDialog';
import { TopologyPanel } from '../components/TopologyPanel';
import { ValidationTable } from '../components/ValidationTable';
import { ValidationDiagnosis } from '../components/ValidationDiagnosis';
import { ApiError } from '../types/api';
import { deploymentsApi } from '../services/deploymentsApi';
import { runsApi } from '../services/runsApi';
import { useDeployments, useScenario, useScenarioActions, useScenarioStatus } from '../hooks/useDeployment';
import { useProfileComponents, usePullComponents } from '../hooks/usePreparation';
import { formatDate } from '../utils/dates';
import { getScenarioGuidance } from '../utils/scenarioGuidance';
import { aggregateValidationStatus, validationDescription } from '../utils/status';
import type { RfStartPayload } from '../types/deployment';
import type { ValidationCheck, ValidationState } from '../types/validation';

const tabs = ['overview', 'topology', 'configuration', 'validation', 'troubleshooter', 'logs', 'runs'] as const;
const publicScenarios = new Set(['4g-lte-sim', '4g-lte-x310', '5g-sa', '5g-sa-x310', '5g-nsa-x310']);
const restartableServiceChecks = new Set(['mongo', 'mme', 'hss', 'sgwc', 'sgwu', 'pgwc', 'pgwu', 'pcrf', 'nrf', 'amf', 'smf', 'upf', 'ausf', 'udm', 'udr', 'pcf', 'ims-database', 'pcscf', 'icscf', 'scscf', 'dns', 'epc_services', 'core_services', 'ims_services', 'mme_ready', 'amf_ready']);
type Tab = typeof tabs[number];

export function ScenarioDetailPage() {
  const { scenarioId = '' } = useParams();
  const [tab, setTab] = useState<Tab>('overview');
  const [container, setContainer] = useState('all');
  const [confirm, setConfirm] = useState<'stop' | 'restart' | 'emergency' | null>(null);
  const [rfStartOpen, setRfStartOpen] = useState(false);
  const [simulationStartOpen, setSimulationStartOpen] = useState(false);
  const [conflictResolution, setConflictResolution] = useState<{ activeScenario: string; retry: () => Promise<unknown>; reset: () => void } | null>(null);
  const [conflictResolutionError, setConflictResolutionError] = useState<unknown>(null);
  const [startAfterPull, setStartAfterPull] = useState(false);
  const startIntentToken = useRef(0);
  const handledPullJob = useRef<string | null>(null);
  const verifyAfterSimulationRepair = useRef(false);
  const scenario = useScenario(scenarioId);
  const deployments = useDeployments();
  const status = useScenarioStatus(scenarioId);
  const actions = useScenarioActions(scenarioId);
  const queryClient = useQueryClient();
  const components = useProfileComponents(scenarioId);
  const coreComponents = useProfileComponents(scenarioId, true);
  const pullComponents = usePullComponents(scenarioId);
  const runs = useQuery({ queryKey: ['runs', scenarioId], queryFn: () => runsApi.list({ scenario: scenarioId, limit: 10 }), enabled: Boolean(scenarioId) });
  const latestRun = useQuery({ queryKey: ['run', runs.data?.[0]?.run_id], queryFn: () => runsApi.detail(runs.data?.[0]?.run_id || ''), enabled: Boolean(runs.data?.[0]?.run_id) });
  const latestValidationSummary = runs.data?.find((run) => ['PASS', 'FAIL', 'PARTIAL', 'WARNING', 'NOT_TESTED'].includes(String(run.status || '').toUpperCase()));
  const latestValidationRun = useQuery({ queryKey: ['run', latestValidationSummary?.run_id], queryFn: () => runsApi.detail(latestValidationSummary?.run_id || ''), enabled: Boolean(latestValidationSummary?.run_id) });
  const logs = useQuery({ queryKey: ['logs', scenarioId, container], queryFn: () => deploymentsApi.logs(container === 'all' ? null : container, 300, scenarioId), enabled: false });
  const deployment = scenario.data;
  const guidance = getScenarioGuidance(scenarioId);
  const is5gSaX310 = scenarioId === '5g-sa-x310';
  const is5gNsaX310 = scenarioId === '5g-nsa-x310';
  const ranNodeName = is5gSaX310 ? 'gNB' : 'eNB';
  const coreName = is5gSaX310 ? '5GC' : 'EPC';
  const validatedChecks = Array.isArray(latestValidationRun.data?.validation?.checks) ? latestValidationRun.data.validation.checks as ValidationCheck[] : [];
  const latestPreflight = latestRun.data?.preflight;
  const preflightStatus = latestPreflight && ['PASS', 'FAIL', 'WARNING', 'NOT_TESTED'].includes(String(latestPreflight.status))
    ? String(latestPreflight.status) as ValidationState
    : null;
  const failedPreflightChecks = Array.isArray(latestPreflight?.checks)
    ? (latestPreflight.checks as ValidationCheck[]).filter((check) => check.status === 'FAIL')
    : [];
  const currentPreflightCheck: ValidationCheck | null = preflightStatus ? {
    id: 'rf_preflight',
    status: preflightStatus,
    detail: failedPreflightChecks.length
      ? failedPreflightChecks.map((check) => `${check.id}: ${check.detail || 'failed'}`).join('; ')
      : preflightStatus === 'PASS' ? 'RF preflight passed.' : 'Latest RF preflight did not pass.',
  } : null;
  const checks = currentPreflightCheck
    ? validatedChecks.some((check) => check.id === 'rf_preflight')
      ? validatedChecks.map((check) => check.id === 'rf_preflight' ? currentPreflightCheck : check)
      : [...validatedChecks, currentPreflightCheck]
    : validatedChecks;
  const validationStatus = checks.length ? aggregateValidationStatus(checks) : String(latestValidationRun.data?.validation?.status || latestValidationSummary?.status || 'NOT_TESTED');
  const validationCheckedAt = String(latestPreflight?.checked_at || latestValidationRun.data?.validation?.checked_at || latestValidationRun.data?.metadata.finished_at || '');
  const latestEvidenceRunId = currentPreflightCheck ? latestRun.data?.run_id : latestValidationSummary?.run_id;
  const diagnosticReport = actions.validate.data?.scenario === scenarioId ? actions.validate.data : null;
  const diagnosticChecks = diagnosticReport?.checks || checks;
  const diagnosticIssues = diagnosticChecks.filter((check) => check.status !== 'PASS');
  const diagnosticStatus = diagnosticReport?.status || validationStatus;
  const diagnosticCheckedAt = diagnosticReport?.checked_at || validationCheckedAt;
  const diagnosticRunId = diagnosticReport?.run_id || latestEvidenceRunId;
  const busy = Object.values(actions).some((action) => action.isPending) || pullComponents.isPending;
  const actionError = Object.values(actions).find((action) => action.error)?.error;
  const displayActionError = conflictResolution ? null : actionError;
  const activeScenarioName = conflictResolution
    ? deployments.data?.find((item) => item.id === conflictResolution.activeScenario)?.name || conflictResolution.activeScenario
    : '';
  const missingImages = components.data?.images.filter((image) => !image.installed) || [];
  const runConfirmed = () => {
    if (confirm === 'stop') actions.stop.mutate();
    if (confirm === 'restart') actions.restart.mutate();
    if (confirm === 'emergency') actions.emergencyStop.mutate();
    setConfirm(null);
  };
  const runStartWithConflictPrompt = async (start: () => Promise<unknown>, reset: () => void) => {
    try {
      await start();
    } catch (error) {
      if (error instanceof ApiError && error.status === 409 && error.code === 'DEPLOYMENT_CONFLICT') {
        const details = error.details as { active_scenario?: unknown } | undefined;
        if (typeof details?.active_scenario === 'string' && details.active_scenario !== scenarioId) {
          reset();
          setConflictResolutionError(null);
          setConflictResolution({ activeScenario: details.active_scenario, retry: start, reset });
          return;
        }
      }
    }
  };
  const stopOtherScenarioAndContinue = async () => {
    const pending = conflictResolution;
    if (!pending) return;
    setConflictResolution(null);
    setConflictResolutionError(null);
    try {
      await deploymentsApi.stop(pending.activeScenario);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['deployments'] }),
        queryClient.invalidateQueries({ queryKey: ['deployment-status'] }),
        queryClient.invalidateQueries({ queryKey: ['deployment-status', pending.activeScenario] }),
      ]);
      await runStartWithConflictPrompt(pending.retry, pending.reset);
    } catch (error) {
      setConflictResolutionError(error);
    }
  };
  const startSimulation = async () => {
    await actions.start.mutateAsync();
    setSimulationStartOpen(false);
    if (verifyAfterSimulationRepair.current) {
      verifyAfterSimulationRepair.current = false;
      actions.validate.mutate();
    }
  };
  const confirmSimulationStart = () => {
    if (components.data?.ready) {
      void runStartWithConflictPrompt(startSimulation, () => actions.start.reset());
      return;
    }
    handledPullJob.current = pullComponents.job?.job_id || null;
    const token = ++startIntentToken.current;
    setStartAfterPull(true);
    pullComponents.mutate(undefined, { onError: () => { if (startIntentToken.current === token) setStartAfterPull(false); } });
  };
  const confirmRfStart = (payload: RfStartPayload) => {
    if (components.data?.ready) {
      void runStartWithConflictPrompt(async () => {
        await actions.startRf.mutateAsync(payload);
        setRfStartOpen(false);
      }, () => actions.startRf.reset());
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
      if (result.data?.ready) void runStartWithConflictPrompt(startSimulation, () => actions.start.reset());
    });
  }, [actions.start, actions.validate, components, pullComponents.job, startAfterPull]);
  useEffect(() => () => { startIntentToken.current += 1; }, []);

  const repairServiceIssue = (check: ValidationCheck) => {
    if (!restartableServiceChecks.has(check.id)) return;
    if (deployment?.rf_capable && deployment.supported_actions.includes('start-core')) {
      void runStartWithConflictPrompt(async () => {
        await actions.startCore.mutateAsync();
        actions.validate.mutate();
      }, () => actions.startCore.reset());
      return;
    }
    if (!deployment?.rf_capable && deployment?.supported_actions.includes('start')) {
      verifyAfterSimulationRepair.current = true;
      setSimulationStartOpen(true);
    }
  };

  if (!scenarioId || !publicScenarios.has(scenarioId)) return <Navigate to="/scenarios" replace />;
  return <div className="page-grid">
    <section className="hero-panel panel wide"><div><Link to="/scenarios" className="muted-text">Back to scenarios</Link><span className="eyebrow">{deployment?.rf_capable ? 'Guarded SDR workspace' : 'Software workspace'}</span><h1 className="hero-title">{deployment?.name || scenarioId}</h1><p className="page-subtitle">{deployment?.description}</p></div><div className="hero-actions"><StatusBadge status={status.data?.status || 'unknown'} /><ActionButton variant="secondary" onClick={() => status.refetch()} loading={status.isFetching}>Sync</ActionButton></div></section>
    {scenario.isLoading || status.isLoading ? <LoadingState /> : null}{scenario.error ? <ErrorAlert error={scenario.error} /> : null}{status.error ? <ErrorAlert error={status.error} onRetry={() => status.refetch()} /> : null}{displayActionError ? <ErrorAlert error={displayActionError} /> : null}{conflictResolutionError ? <ErrorAlert error={conflictResolutionError} /> : null}
    {guidance ? <section className="panel wide scenario-guide"><div className="scenario-guide-intro"><span className="generation-mark">{guidance.generation}</span><div><span className="eyebrow">{guidance.variant}</span><h2>What is this profile?</h2><p>{guidance.purpose}</p></div></div><div className="scenario-guide-grid"><div><span>Includes</span><ul>{guidance.includes.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span>Operational boundary</span><ul>{guidance.excludes.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span>Requirements</span><p>{guidance.hardware}</p></div></div></section> : null}
    {components.error ? <ErrorAlert error={components.error} onRetry={() => components.refetch()} /> : null}{pullComponents.error ? <ErrorAlert error={pullComponents.error} /> : null}
    {components.data ? <section className={`panel wide scenario-components ${components.data.ready ? 'ready' : 'missing'}`}><div><span className="eyebrow">Preparation</span><h3>{components.data.ready ? 'Components ready' : `${missingImages.length} component${missingImages.length === 1 ? '' : 's'} missing`}</h3><p>{components.data.installed_count}/{components.data.total_count} installed. Downloading does not build images, start services, or enable RF.</p></div><div className="actions-row"><StatusBadge status={components.data.ready ? 'PASS' : 'FAIL'} kind="validation" />{!components.data.ready ? <ActionButton onClick={() => pullComponents.mutate()} loading={pullComponents.isPending}>Download missing</ActionButton> : null}<Link className="action-link" to="/preparation">View details</Link></div>{pullComponents.job ? <ComponentPullProgress job={pullComponents.job} /> : null}</section> : null}
    <section className={`panel wide command-center ${deployment?.rf_capable ? 'rf-command-center' : 'simulation-command-center'}`}><div className="panel-heading"><div><span className="eyebrow">Command bar</span><h3>{deployment?.rf_capable ? 'X310 launch sequence' : 'Software launch sequence'}</h3></div>{busy ? <StatusBadge status="validating" /> : null}</div>{deployment?.rf_capable ? <div className="rf-quick-start"><div><span className="rf-quick-icon"><RadioTower size={21} /></span><div><strong>Core + guarded RF</strong><p>One guided action runs core startup, strict preflight and the time-limited SDR service.</p></div></div><ActionButton variant="danger" disabled={busy || components.isLoading} onClick={() => setRfStartOpen(true)}><Play size={15} />Start X310 lab</ActionButton></div> : deployment?.supported_actions.includes('start') ? <div className="simulation-quick-start"><div><span className="simulation-quick-icon"><Boxes size={21} /></span><div><strong>Complete software lab</strong><p>Start the core, simulated RAN, UE and scenario-specific services.</p></div></div><ActionButton disabled={busy || components.isLoading} onClick={() => setSimulationStartOpen(true)}><Play size={15} />Start lab</ActionButton></div> : null}<div className="actions-row">
      {deployment?.supported_actions.includes('start-core') ? <ActionButton variant="secondary" disabled={busy || coreComponents.data?.ready !== true} loading={actions.startCore.isPending} onClick={() => void runStartWithConflictPrompt(() => actions.startCore.mutateAsync(), () => actions.startCore.reset())}><Cpu size={15} />{is5gSaX310 ? '5GC + IMS, no RF' : 'EPC + IMS, no RF'}</ActionButton> : deployment?.supported_actions.includes('start-epc') ? <ActionButton disabled={busy || coreComponents.data?.ready !== true} loading={actions.startEpc.isPending} onClick={() => void runStartWithConflictPrompt(() => actions.startEpc.mutateAsync(), () => actions.startEpc.reset())}>EPC + IMS, no RF</ActionButton> : null}
      {deployment?.supported_actions.includes('hardware-check') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.hardwareCheck.isPending} onClick={() => actions.hardwareCheck.mutate()}><Activity size={15} />Hardware check</ActionButton> : null}
      {deployment?.supported_actions.includes('preflight') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.preflight.isPending} onClick={() => actions.preflight.mutate()}><ShieldAlert size={15} />Preflight</ActionButton> : null}
      {deployment?.supported_actions.includes('validate') ? <ActionButton variant="secondary" disabled={busy} loading={actions.validate.isPending} onClick={() => actions.validate.mutate()}>Validate</ActionButton> : null}
      {deployment?.supported_actions.includes('restart') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} onClick={() => setConfirm('restart')}>Restart</ActionButton> : null}
      {deployment?.supported_actions.includes('stop') ? <ActionButton variant="danger" disabled={busy} onClick={() => setConfirm('stop')}>Stop</ActionButton> : null}
      {deployment?.supported_actions.includes('emergency-stop') ? <ActionButton variant="danger" disabled={busy} onClick={() => setConfirm('emergency')}>Emergency stop</ActionButton> : null}
    </div>{deployment?.rf_capable ? <div className="rf-operator-guide" role="note"><div className="rf-operator-order"><strong>Recommended {is5gSaX310 ? '5G SA' : is5gNsaX310 ? '5G NSA' : '4G'} X310 run order</strong><ol><li><b>Apply the profile:</b> if its diff shows pending changes, review and apply the radio plan under Deployments before checks.</li><li><b>Hardware check:</b> confirm the Ethernet link, X310 detection, and UHD.</li><li><b>Preflight:</b> check the profile, authorization, and safety requirements; this does not transmit.</li><li><b>Start X310 lab:</b> starts {coreName}/IMS, reruns preflight, then starts the {ranNodeName} for the selected duration.</li><li>When finished, wait for auto-stop or use <b>Stop</b>. Use <b>Emergency stop</b> to cut RF immediately.</li><li><b>Validate:</b> records the run checks for review.</li></ol></div><div className="rf-action-help"><strong>Button guide</strong><ul><li><b>{coreName} + IMS, no RF:</b> starts the core and IMS services without RF.</li><li><b>Hardware check:</b> checks X310 detection, Ethernet, UHD, and required RF chains.</li><li><b>Preflight:</b> checks requirements before transmission.</li><li><b>Start X310 lab:</b> opens the guided start and runs the time-limited RF profile.</li><li><b>Validate:</b> analyzes and saves checks for the run.</li><li><b>Stop:</b> stops the guarded RAN and any core/IMS services started by this profile; it preserves the shared EPC if another profile is using it.</li><li><b>Emergency stop:</b> runs the emergency RF service shutdown.</li></ul></div></div> : null}</section>
    <section className="panel wide"><div className="tab-list" role="tablist">{tabs.map((item) => <button key={item} type="button" className={tab === item ? 'active' : ''} onClick={() => setTab(item)} role="tab" aria-selected={tab === item}>{item}</button>)}</div>
      {tab === 'overview' ? <div className="page-grid scenario-overview-grid"><OperationalProofPanel scenarioId={scenarioId} rfCapable={Boolean(deployment?.rf_capable)} checks={checks} checkedAt={validationCheckedAt} runId={latestEvidenceRunId} loading={actions.validate.isPending} onValidate={() => actions.validate.mutate()} onOpenLogs={() => setTab('logs')} /><section><h3>Service inventory</h3><p className="muted-text scenario-section-intro">Expected profile services are compared with containers currently detected by Docker.</p><ContainerStatusTable containers={status.data?.containers || []} expectedServices={deployment?.components || []} conditionalServices={deployment?.conditional_components || []} deploymentState={status.data?.status || 'unknown'} /></section><section className="scenario-validation-column"><div><h3>Operational validation</h3><p className="muted-text scenario-section-intro">{is5gNsaX310 ? 'RF-chain, UHD/RFNoC initialization, EPC, eNB session, LTE S1, NR secondary-cell and UE evidence from the latest validation.' : 'Protocol, UE, user-plane and hardware evidence from the latest completed validation.'}</p><ScenarioValidationPanel expectedChecks={deployment?.validation_checks || []} checks={checks} status={validationStatus} checkedAt={validationCheckedAt} runId={latestEvidenceRunId} loading={actions.validate.isPending} onValidate={() => actions.validate.mutate()} /></div><div className="scenario-latest-run"><h3>Latest execution</h3>{latestRun.data ? <dl className="facts"><dt>Run ID</dt><dd><Link to={`/runs/${latestRun.data.run_id}`}>{latestRun.data.run_id}</Link></dd><dt>Result</dt><dd><StatusBadge status={String(latestPreflight?.status || latestRun.data.validation?.status || latestRun.data.metadata.status || 'unknown')} kind="validation" /></dd><dt>Finished</dt><dd>{formatDate(String(latestPreflight?.checked_at || latestRun.data.metadata.finished_at || latestRun.data.metadata.started_at || ''))}</dd><dt>Commit</dt><dd><code>{String(latestRun.data.metadata.git_commit || 'Not recorded')}</code></dd></dl> : <div className="empty-state"><h3>No runs recorded</h3><p>Run validation to generate immutable evidence.</p></div>}</div></section></div> : null}
      {tab === 'topology' ? <TopologyPanel containers={status.data?.containers || []} checks={checks} checkedAt={status.data?.checked_at} title={`${deployment?.name || scenarioId} topology`} /> : null}
      {tab === 'configuration' ? <div className="empty-state"><h3>Permanent configuration workspace</h3><p>Profiles are edited under Deployments. Generated run evidence remains under runs/ and is never edited here.</p><Link className="action-link" to="/deployments">Open deployments</Link></div> : null}
      {tab === 'validation' ? <ValidationTable checks={checks} expectedChecks={deployment?.validation_checks || []} checkedAt={validationCheckedAt} /> : null}
      {tab === 'troubleshooter' ? <section className="scenario-troubleshooter" aria-label="Profile troubleshooter">
        <div className="scenario-troubleshooter-heading"><div><span className="eyebrow">Guided repair</span><h2>Troubleshooter</h2><p>Work through the first failing stage, apply an available safe action, then run the diagnosis again.</p></div><Wrench size={21} /></div>
        <div className="scenario-troubleshooter-actions">
          <ActionButton onClick={() => actions.validate.mutate()} loading={actions.validate.isPending}>Run diagnosis</ActionButton>
          {deployment?.supported_actions.includes('hardware-check') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.hardwareCheck.isPending} onClick={() => actions.hardwareCheck.mutate()}>Hardware check</ActionButton> : null}
          {deployment?.supported_actions.includes('preflight') ? <ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} loading={actions.preflight.isPending} onClick={() => actions.preflight.mutate()}>Preflight</ActionButton> : null}
          {deployment?.supported_actions.includes('start-core') ? <ActionButton variant="secondary" disabled={busy || coreComponents.data?.ready !== true} loading={actions.startCore.isPending} onClick={() => void runStartWithConflictPrompt(() => actions.startCore.mutateAsync(), () => actions.startCore.reset())}>Start core (no RF)</ActionButton> : null}
          {!deployment?.rf_capable && deployment?.supported_actions.includes('start') ? <ActionButton variant="secondary" disabled={busy || components.isLoading} onClick={() => setSimulationStartOpen(true)}>Start simulation lab</ActionButton> : null}
        </div>
        <div className="scenario-troubleshooter-meta"><StatusBadge status={diagnosticStatus} kind="validation" /><span>{diagnosticRunId ? <>Evidence from <code>{diagnosticRunId}</code>{diagnosticCheckedAt ? ` · ${formatDate(diagnosticCheckedAt)}` : ''}</> : 'No validation evidence is available yet.'}</span></div>
        {diagnosticIssues.length ? <div className="scenario-troubleshooter-issues"><div className="panel-heading"><div><h3>Recommended repair order</h3><p className="muted-text">Resolve the earliest failing stage first. Checks marked not tested need evidence after the earlier problem is fixed.</p></div></div>
          {diagnosticIssues.map((check, index) => <article className={`troubleshooter-issue ${check.status.toLowerCase()}`} key={check.id}>
            <div className="troubleshooter-issue-heading"><span className="troubleshooter-step">{index + 1}</span><div><h3>{validationDescription(check.id)}</h3><code>{check.id}</code></div><StatusBadge status={check.status} kind="validation" /></div>
            <ValidationDiagnosis check={check} />
            <div className="troubleshooter-issue-actions">
              {restartableServiceChecks.has(check.id) && deployment?.rf_capable && deployment.supported_actions.includes('start-core') ? <ActionButton variant="secondary" disabled={busy || coreComponents.data?.ready !== true} loading={actions.startCore.isPending} onClick={() => repairServiceIssue(check)}>Start core and verify (no RF)</ActionButton> : null}
              {restartableServiceChecks.has(check.id) && !deployment?.rf_capable && deployment?.supported_actions.includes('start') ? <ActionButton variant="secondary" disabled={busy || components.isLoading} onClick={() => { verifyAfterSimulationRepair.current = true; setSimulationStartOpen(true); }}>Start simulation and verify</ActionButton> : null}
              <button className="troubleshooter-log-button" type="button" onClick={() => setTab('logs')}>Open profile logs <ArrowRight size={14} /></button>
            </div>
          </article>)}
        </div> : diagnosticChecks.length ? <div className="panel troubleshooter-success"><StatusBadge status={diagnosticStatus} kind="validation" /><div><h3>No failing checks detected</h3><p>Checks marked not tested still need the corresponding UE or session evidence before the end-to-end flow is confirmed.</p></div></div> : <div className="panel empty-state"><h3>Run a diagnosis to begin</h3><p>The profile checks its core, radio and UE evidence, then lists the next repair steps here.</p></div>}
        <p className="scenario-troubleshooter-boundary">Safe checks and core-only actions are available here. RF transmission, FPGA flashing and configuration changes always require their own explicit workflow.</p>
      </section> : null}
      {tab === 'logs' ? <><div className="logs-toolbar"><label>Service<select value={container} onChange={(event) => setContainer(event.target.value)}><option value="all">All services</option>{(deployment?.components || []).map((item) => <option key={item} value={item}>{item}</option>)}</select></label><ActionButton variant="secondary" onClick={() => logs.refetch()} loading={logs.isFetching}>Fetch logs</ActionButton><span className="log-state">WebSocket unavailable: manual fetch</span></div>{logs.error ? <ErrorAlert error={logs.error} onRetry={() => logs.refetch()} /> : null}<LogsViewer response={logs.data} isLoading={logs.isLoading} /></> : null}
      {tab === 'runs' ? <div className="run-timeline">{runs.data?.length ? runs.data.map((run) => <Link className={`run-card ${String(run.status || '').toLowerCase()}`} to={`/runs/${run.run_id}`} key={run.run_id}><span className="run-marker" /><div><div className="run-title">{run.run_id}</div><div className="run-meta">{formatDate(run.finished_at || run.started_at)} · {run.git_commit || 'Commit not recorded'}</div></div><StatusBadge status={String(run.status || 'unknown')} kind="validation" /></Link>) : <div className="empty-state"><h3>No scenario runs</h3><p>Completed scripts will add evidence under runs/.</p></div>}</div> : null}
    </section>
    <ConfirmDialog open={confirm !== null} title={confirm === 'emergency' ? 'Emergency stop RF service' : confirm === 'restart' ? 'Restart deployment' : 'Stop deployment'} message="This request is executed by the backend through guarded operational scripts. Continue only if this is the intended laboratory action." confirmLabel={confirm === 'emergency' ? 'Emergency stop' : confirm === 'restart' ? 'Restart' : 'Stop'} onConfirm={runConfirmed} onCancel={() => setConfirm(null)} />
    <RfStartDialog scenarioId={scenarioId} open={rfStartOpen} loading={actions.startRf.isPending || pullComponents.isPending} missingImages={missingImages} pullJob={pullComponents.job} onCancel={() => setRfStartOpen(false)} onConfirm={confirmRfStart} />
    {deployment ? <SimulationStartDialog deployment={deployment} open={simulationStartOpen} loading={actions.start.isPending || pullComponents.isPending} missingImages={missingImages} pullJob={pullComponents.job} onCancel={() => { startIntentToken.current += 1; setStartAfterPull(false); verifyAfterSimulationRepair.current = false; setSimulationStartOpen(false); }} onConfirm={confirmSimulationStart} /> : null}
    <ConfirmDialog open={Boolean(conflictResolution)} title="Another profile is active" message={`The backend detected ${activeScenarioName} running. Stop that profile and its services, then continue starting ${deployment?.name || scenarioId}? If it is transmitting RF, this will stop its radio service. The new profile will still use its own safety checks.`} confirmLabel="Stop profile and continue" onConfirm={() => void stopOtherScenarioAndContinue()} onCancel={() => { setConflictResolution(null); conflictResolution?.reset(); }} />
  </div>;
}
