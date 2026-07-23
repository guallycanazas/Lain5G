import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { TopologyPanel } from '../components/TopologyPanel';
import { useDeploymentActions, useDeploymentStatus, useHealth } from '../hooks/useDeployment';
import { useRuns } from '../hooks/useRuns';
import { useLatestValidation } from '../hooks/useValidation';
import { useProfileComponents } from '../hooks/usePreparation';
import { usePreferences } from '../preferences/PreferencesProvider';
import { formatDate } from '../utils/dates';

function checkState(checks: { id: string; status: string }[], id: string) {
  return checks.find((check) => check.id === id)?.status === 'PASS';
}

export function DashboardPage() {
  const health = useHealth();
  const status = useDeploymentStatus();
  const validation = useLatestValidation();
  const runs = useRuns();
  const actions = useDeploymentActions();
  const components = useProfileComponents('5g-sa');
  const { t } = usePreferences();
  const [confirm, setConfirm] = useState<'stop' | 'restart' | null>(null);
  const report = validation.data;
  const checks = report?.checks || [];
  const activeServices = status.data?.containers.filter((container) => container.running).length || 0;
  const passRate = checks.length ? Math.round((checks.filter((check) => check.status === 'PASS').length / checks.length) * 100) : null;
  const busy = actions.start.isPending || actions.stop.isPending || actions.restart.isPending || actions.validate.isPending;
  const actionError = actions.start.error || actions.stop.error || actions.restart.error || actions.validate.error;

  const runConfirmed = () => {
    if (confirm === 'stop') actions.stop.mutate();
    if (confirm === 'restart') actions.restart.mutate();
    setConfirm(null);
  };

  return (
    <div className="page-grid">
      <section className="hero-panel panel wide">
        <div>
          <span className="eyebrow">{t('dashboard.eyebrow')}</span>
          <h1 className="hero-title">Lain5G-Lab</h1>
          <p className="page-subtitle">{t('dashboard.subtitle')}</p>
        </div>
        <div className="hero-actions">
          {status.data ? <StatusBadge status={status.data.status} /> : <StatusBadge status="unknown" />}
          <ActionButton variant="secondary" onClick={() => status.refetch()} loading={status.isFetching}>{t('dashboard.sync')}</ActionButton>
          <ActionButton loading={actions.start.isPending} disabled={busy || components.data?.ready !== true} onClick={() => actions.start.mutate()}>{t('dashboard.start')}</ActionButton>
          <ActionButton variant="secondary" loading={actions.validate.isPending} disabled={busy} onClick={() => actions.validate.mutate()}>{t('dashboard.validate')}</ActionButton>
          <ActionButton variant="danger" disabled={busy} onClick={() => setConfirm('stop')}>{t('dashboard.stop')}</ActionButton>
        </div>
      </section>

      <section className="summary-grid wide" aria-label="Operations overview">
        <article className="summary-card"><div className="summary-label">{t('dashboard.activeServices')}</div><div className="summary-value">{activeServices}</div><div className="summary-note">{status.data?.containers.length || 0} {t('dashboard.reportedByApi')}</div></article>
        <article className="summary-card"><div className="summary-label">{t('dashboard.registeredUes')}</div><div className="summary-value">{checkState(checks, 'ue_registration') ? '1+' : '0'}</div><div className="summary-note">{t('dashboard.validationEvidence')}</div></article>
        <article className="summary-card"><div className="summary-label">{t('dashboard.dataSessions')}</div><div className="summary-value">{checkState(checks, 'pdu_session') ? '1+' : '0'}</div><div className="summary-note">{t('dashboard.pduEvidence')}</div></article>
        <article className="summary-card"><div className="summary-label">{t('dashboard.passRate')}</div><div className="summary-value">{passRate === null ? '--' : `${passRate}%`}</div><div className="summary-note">{report ? formatDate(report.checked_at) : t('dashboard.noValidation')}</div></article>
      </section>

      {health.error ? <ErrorAlert error={health.error} onRetry={() => health.refetch()} /> : null}
      {status.error ? <ErrorAlert error={status.error} onRetry={() => status.refetch()} /> : null}
      {components.error ? <ErrorAlert error={components.error} onRetry={() => components.refetch()} /> : null}
      {actionError ? <ErrorAlert error={actionError} /> : null}
      {status.isLoading ? <LoadingState /> : null}

      <section className="panel wide"><TopologyPanel containers={status.data?.containers || []} checks={checks} checkedAt={status.data?.checked_at} title="5G SA service topology" /></section>

      <section className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Execution</span><h3>Deployment control</h3></div><StatusBadge status={health.data?.dry_run ? 'dry_run' : 'running'} /></div>
        <dl className="facts"><dt>Backend</dt><dd>{health.data?.status || 'Unavailable'}</dd><dt>Mode</dt><dd>{health.data?.dry_run ? 'Dry-run' : 'Real'}</dd><dt>Last sync</dt><dd>{status.data ? formatDate(status.data.checked_at) : 'No telemetry'}</dd><dt>Action</dt><dd>{busy ? 'Operation in progress' : 'Ready'}</dd></dl>
        <div className="actions-row" style={{ marginTop: 18 }}><ActionButton variant="secondary" disabled={busy || components.data?.ready !== true} onClick={() => setConfirm('restart')}>Restart</ActionButton><Link className="action-link" to="/scenarios/5g-sa">Open workspace</Link></div>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><span className="eyebrow">{t('nav.preparation')}</span><h3>{t('dashboard.requiredComponents')}</h3></div><StatusBadge status={components.data?.ready ? 'PASS' : 'FAIL'} kind="validation" /></div>
        <p className="muted-text">{components.data ? `${components.data.installed_count}/${components.data.total_count} images installed for 5G SA.` : 'Checking published images...'}</p>
        <Link className="action-link" to="/preparation">{t('dashboard.openPreparation')}</Link>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><span className="eyebrow">RF safety</span><h3>Operator guardrails</h3></div><Link to="/rf-safety">Review</Link></div>
        <p className="muted-text">RF actions remain guarded by backend scripts and local manifests. This console does not treat container state as authorization.</p>
        <div className="warning-box">Emergency stop is available only through the guarded X310 backend action. Review authorization before any RF operation.</div>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Validation</span><h3>Layer summary</h3></div><Link to="/validation">Open validation</Link></div>
        {report ? <ul className="claims-list">{checks.slice(0, 8).map((check) => <li key={check.id}>{check.id}: {check.status}</li>)}</ul> : <div className="empty-state"><h3>No validation evidence</h3><p>Run validation to populate protocol and user-plane evidence.</p></div>}
      </section>

      <section className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Recent runs</span><h3>Execution history</h3></div><Link to="/runs">All runs</Link></div>
        {runs.data?.length ? <div className="run-timeline">{runs.data.slice(0, 3).map((run) => <Link className={`run-card ${String(run.status || '').toLowerCase()}`} to={`/runs/${run.run_id}`} key={run.run_id}><span className="run-marker" /><div><div className="run-title">{run.run_id}</div><div className="run-meta">{run.scenario || 'Unknown scenario'} · {formatDate(run.finished_at || run.started_at)}</div></div><StatusBadge status={String(run.status || 'unknown')} kind="validation" /></Link>)}</div> : <div className="empty-state"><h3>No runs recorded</h3><p>Validation artifacts will appear here after an execution.</p></div>}
      </section>

      <ConfirmDialog open={confirm !== null} title={confirm === 'stop' ? 'Stop 5G SA deployment' : 'Restart 5G SA deployment'} message="The backend will execute the configured operational script. Review the run and logs after completion." confirmLabel={confirm === 'stop' ? 'Stop deployment' : 'Restart deployment'} onConfirm={runConfirmed} onCancel={() => setConfirm(null)} />
    </div>
  );
}
