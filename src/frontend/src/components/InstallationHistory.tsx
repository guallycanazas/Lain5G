import { Download, FileText, History } from 'lucide-react';
import type { InstallationRecord } from '../types/preparation';

const statusLabels: Record<InstallationRecord['status'], string> = {
  running: 'In progress',
  succeeded: 'Completed',
  failed: 'Failed',
  dry_run: 'Preview only',
  partial: 'Partially completed',
};

function formatDate(value: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatDuration(durationMs: number | null) {
  if (durationMs === null) return 'In progress';
  if (durationMs < 1000) return `${durationMs} ms`;
  const seconds = durationMs / 1000;
  return seconds < 60 ? `${seconds.toFixed(1)} s` : `${Math.floor(seconds / 60)} min ${Math.round(seconds % 60)} s`;
}

export function InstallationHistory({ records, isLoading, error, onRefresh, isRefreshing }: {
  records: InstallationRecord[];
  isLoading: boolean;
  error: unknown;
  onRefresh: () => void;
  isRefreshing: boolean;
}) {
  return <section className="panel installation-history">
    <div className="panel-heading"><div><span className="eyebrow">Preparation records</span><h2><History size={20} /> Installation history</h2></div><button className="quiet-button" type="button" onClick={onRefresh} disabled={isRefreshing}>{isRefreshing ? 'Refreshing…' : 'Refresh history'}</button></div>
    {error ? <p className="installation-history-message error" role="alert">Could not load installation history. Check that the backend is available, then refresh.</p> : null}
    {isLoading ? <p className="installation-history-message">Loading installation history…</p> : null}
    {!isLoading && !error && records.length === 0 ? <p className="installation-history-message">No installation records yet. Component downloads and bootstrap runs will appear here.</p> : null}
    <div className="installation-record-list">{records.map((record) => <article className={`installation-record ${record.status}`} key={record.id}>
      <header className="installation-record-heading"><div><span className={`installation-status ${record.status}`}>{statusLabels[record.status]}</span><h3>{record.kind === 'bootstrap' ? 'System installation' : 'Component download'} · {record.scope}</h3><code>{record.id}</code></div><div className="installation-record-links"><a href={`/api/preparation/installations/${encodeURIComponent(record.id)}/download`} download aria-label={`Download JSON report for ${record.id}`}><Download size={15} /> Report</a>{record.log_available ? <a href={`/api/preparation/installations/${encodeURIComponent(record.id)}/log`} download aria-label={`Download log for ${record.id}`}><FileText size={15} /> Log</a> : null}</div></header>
      <p className="installation-record-reason"><strong>Why:</strong> {record.reason}</p>
      <dl className="installation-record-meta"><div><dt>Started</dt><dd>{formatDate(record.started_at || record.created_at)}</dd></div><div><dt>Finished</dt><dd>{formatDate(record.finished_at)}</dd></div><div><dt>Duration</dt><dd>{formatDuration(record.duration_ms)}</dd></div><div><dt>Machine</dt><dd>{record.environment.machine_type}</dd></div><div><dt>Host</dt><dd>{record.environment.host_os} · {record.environment.host_architecture}</dd></div><div><dt>Runtime</dt><dd>{record.environment.runtime} · {record.environment.runtime_os}/{record.environment.runtime_architecture}</dd></div></dl>
      {record.installed_components.length ? <div className="installation-components"><strong>Installed or prepared</strong><ul>{record.installed_components.map((name) => <li key={name}><code>{name}</code></li>)}</ul></div> : null}
      {record.steps.length ? <details className="installation-steps"><summary>Step details ({record.steps.length})</summary><ul>{record.steps.map((step, index) => <li className={step.status} key={`${step.name}-${index}`}><div><strong>{step.name}</strong><p>{step.reason}</p>{step.message ? <p className="installation-step-message">{step.message}</p> : null}</div><span>{step.status}{step.duration_ms === null ? '' : ` · ${formatDuration(step.duration_ms)}`}{step.exit_code === null ? '' : ` · exit ${step.exit_code}`}</span></li>)}</ul></details> : null}
    </article>)}</div>
  </section>;
}
