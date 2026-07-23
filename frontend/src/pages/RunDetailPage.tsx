import { Fragment } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { ValidationTable } from '../components/ValidationTable';
import { useRunDetail } from '../hooks/useRuns';
import type { ValidationCheck } from '../types/validation';
import { formatDate } from '../utils/dates';

export function RunDetailPage() {
  const { runId } = useParams();
  const run = useRunDetail(runId);
  const metadata = run.data?.metadata || {};
  const checks = ((run.data?.validation?.checks as ValidationCheck[] | undefined) || []);
  return <section className="page-panel">{run.isLoading ? <LoadingState /> : null}{run.error ? <ErrorAlert error={run.error} /> : null}{run.data ? <><div className="page-heading"><div><Link to="/runs" className="muted-text">Back to runs</Link><span className="eyebrow">Immutable evidence</span><h1>{run.data.run_id}</h1><p className="page-subtitle">Read-only execution metadata, validation evidence and available artifacts.</p></div><StatusBadge status={String(run.data.validation?.status || metadata.status || 'unknown')} kind="validation" /></div><div className="page-grid"><section className="panel"><h3>Run context</h3><dl className="facts"><dt>Scenario</dt><dd>{String(metadata.scenario || 'Not recorded')}</dd><dt>Started</dt><dd>{formatDate(String(metadata.started_at || ''))}</dd><dt>Finished</dt><dd>{formatDate(String(metadata.finished_at || ''))}</dd><dt>Git commit</dt><dd><code>{String(metadata.git_commit || 'Not recorded')}</code></dd><dt>Mode</dt><dd>{metadata.dry_run ? 'Dry-run' : 'Real or not recorded'}</dd></dl></section><section className="panel"><h3>Validated claims</h3>{Array.isArray(metadata.validated_claims) && metadata.validated_claims.length ? <ul className="claims-list">{(metadata.validated_claims as string[]).map((claim) => <li key={claim}>{claim}</li>)}</ul> : <div className="empty-state"><h3>No claims recorded</h3><p>The run metadata contains no validated claims.</p></div>}</section></div><section className="panel" style={{ marginTop: 18 }}><div className="panel-heading"><h3>Validation evidence</h3><span className="muted-text">{checks.length} checks</span></div><ValidationTable checks={checks} checkedAt={String(run.data.validation?.checked_at || '')} /></section><div className="page-grid" style={{ marginTop: 18 }}><section className="panel"><h3>Artifacts</h3>{run.data.logs.length ? <ul>{run.data.logs.map((log) => <li key={log}><code>{log}</code></li>)}</ul> : <p className="muted-text">No log artifacts were indexed for this run.</p>}</section><section className="panel"><h3>Metrics</h3>{run.data.metrics && Object.keys(run.data.metrics).length ? <dl className="facts">{Object.entries(run.data.metrics).map(([key, value]) => <Fragment key={key}><dt>{key}</dt><dd><code>{typeof value === 'string' ? value : JSON.stringify(value)}</code></dd></Fragment>)}</dl> : <div className="empty-state"><h3>No metrics recorded</h3><p>Metrics are shown only when the run artifact contains them.</p></div>}</section></div></> : null}</section>;
}
