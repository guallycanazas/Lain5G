import { Link } from 'react-router-dom';
import { EmptyState } from '../components/EmptyState';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useLatestValidation } from '../hooks/useValidation';

export function MetricsPage() {
  const validation = useLatestValidation();
  const checks = validation.data?.checks || [];
  const passed = checks.filter((check) => check.status === 'PASS').length;
  const warnings = checks.filter((check) => check.status === 'WARNING').length;
  const failed = checks.filter((check) => check.status === 'FAIL').length;
  return <section className="page-panel">
    <div className="page-heading"><div><span className="eyebrow">Observability</span><h1>Metrics</h1><p className="page-subtitle">Validation-derived indicators. Live SDR and packet telemetry require a backend metrics endpoint.</p></div><Link className="action-link" to="/validation">Open validation</Link></div>
    {validation.isLoading ? <LoadingState /> : null}
    {validation.error ? <ErrorAlert error={validation.error} onRetry={() => validation.refetch()} /> : null}
    {validation.data ? <><div className="summary-grid"><article className="summary-card"><div className="summary-label">Passed checks</div><div className="summary-value">{passed}</div></article><article className="summary-card"><div className="summary-label">Warnings</div><div className="summary-value">{warnings}</div></article><article className="summary-card"><div className="summary-label">Failed checks</div><div className="summary-value">{failed}</div></article><article className="summary-card"><div className="summary-label">Report state</div><div className="summary-value"><StatusBadge status={validation.data.status} kind="validation" /></div></article></div><div className="validation-layers" style={{ marginTop: 18 }}>{checks.map((check) => <article className="validation-layer" key={check.id}><div className="validation-layer-header"><div><h3>{check.id}</h3><span className="muted-text">{check.detail || 'No evidence reported'}</span></div><StatusBadge status={check.status} kind="validation" /></div></article>)}</div></> : <EmptyState title="No metrics available" message="Run validation to create evidence-derived indicators. The current backend does not expose time-series SDR, Docker or user-plane metrics." />}
  </section>;
}
