import { useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { Activity, ArrowRight, CircleHelp, Wrench } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { ValidationDiagnosis } from '../components/ValidationDiagnosis';
import { useDeployments, useScenarioActions } from '../hooks/useDeployment';
import { useLatestValidation } from '../hooks/useValidation';
import { validationDescription } from '../utils/status';

export function TroubleshooterPage() {
  const [searchParams] = useSearchParams();
  const [scenario, setScenario] = useState(searchParams.get('scenario') || '5g-sa');
  const deployments = useDeployments();
  const latest = useLatestValidation();
  const actions = useScenarioActions(scenario);
  const deployment = deployments.data?.find((item) => item.id === scenario);
  const report = actions.validate.data || (latest.data?.scenario === scenario ? latest.data : undefined);
  const issues = useMemo(() => (report?.checks || []).filter((check) => check.status !== 'PASS'), [report]);
  const supported = new Set(deployment?.supported_actions || []);
  const actionError = actions.hardwareCheck.error || actions.preflight.error || actions.startCore.error;

  return <section className="page-panel troubleshooter-page">
    <div className="page-heading"><div><span className="eyebrow">Guided diagnosis</span><h1>Troubleshooter</h1><p className="page-subtitle">Run profile checks and see the next action.</p></div><CircleHelp size={25} /></div>
    <section className="panel troubleshooter-controls">
      <label>Profile<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{(deployments.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <ActionButton onClick={() => actions.validate.mutate()} loading={actions.validate.isPending}><Activity size={15} />Run full diagnosis</ActionButton>
      {supported.has('hardware-check') ? <ActionButton variant="secondary" onClick={() => actions.hardwareCheck.mutate()} loading={actions.hardwareCheck.isPending}>Hardware check</ActionButton> : null}
      {supported.has('preflight') ? <ActionButton variant="secondary" onClick={() => actions.preflight.mutate()} loading={actions.preflight.isPending}>Preflight</ActionButton> : null}
      {supported.has('start-core') ? <ActionButton variant="secondary" onClick={() => actions.startCore.mutate()} loading={actions.startCore.isPending}>Start core (no RF)</ActionButton> : null}
    </section>
    {deployments.isLoading || latest.isLoading ? <LoadingState /> : null}
    {deployments.error ? <ErrorAlert error={deployments.error} onRetry={() => deployments.refetch()} /> : null}
    {latest.error && !report ? <ErrorAlert error={latest.error} onRetry={() => latest.refetch()} /> : null}
    {actionError ? <ErrorAlert error={actionError} /> : null}
    {actions.validate.error ? <ErrorAlert error={actions.validate.error} /> : null}
    {actions.validate.data?.status === 'FAIL' ? <div className="inline-result fail"><StatusBadge status="FAIL" kind="validation" /> Review the failed checks below.</div> : null}
    {report ? <>
      <section className="panel troubleshooter-result">
        <div><span className="eyebrow">Latest diagnostic</span><h2>{deployment?.name || scenario}</h2><p>Run <code>{report.run_id || 'not recorded'}</code>{report.checked_at ? ` · ${new Date(report.checked_at).toLocaleString()}` : ''}</p></div>
        <StatusBadge status={report.status} kind="validation" />
      </section>
      {issues.length ? <section className="troubleshooter-issues" aria-label="Checks to review">
        <div className="panel-heading"><div><h2>Checks to review</h2><p className="muted-text">{issues.length} checks need attention. Start with the first failed stage.</p></div><Wrench size={20} /></div>
        {issues.map((check, index) => <article className={`troubleshooter-issue ${check.status.toLowerCase()}`} key={check.id}>
          <div className="troubleshooter-issue-heading"><span className="troubleshooter-step">{index + 1}</span><div><h3>{validationDescription(check.id)}</h3><code>{check.id}</code></div><StatusBadge status={check.status} kind="validation" /></div>
          <ValidationDiagnosis check={check} />
          <div className="troubleshooter-issue-actions"><Link to={`/logs?scenario=${encodeURIComponent(scenario)}`}>Inspect this profile’s logs <ArrowRight size={14} /></Link><Link to={`/scenarios/${encodeURIComponent(scenario)}`}>Open profile <ArrowRight size={14} /></Link></div>
        </article>)}
      </section> : <section className="panel troubleshooter-success"><StatusBadge status="PASS" kind="validation" /><div><h2>Checks passed</h2><p>All checks included in the latest validation passed.</p></div></section>}
      <p className="troubleshooter-boundary">Diagnostics do not enable RF or change subscriber and profile settings.</p>
    </> : <section className="panel empty-state troubleshooter-empty"><h2>Ready to check</h2><p>Run diagnosis to inspect this profile.</p></section>}
  </section>;
}
