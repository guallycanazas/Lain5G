import { useEffect } from 'react';
import { Link, useSearchParams } from 'react-router';
import { EmptyState } from '../components/EmptyState';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useDeployments } from '../hooks/useDeployment';
import { useLatestValidation } from '../hooks/useValidation';
import { formatDate } from '../utils/dates';

export function MetricsPage() {
  const deployments = useDeployments();
  const [searchParams, setSearchParams] = useSearchParams();
  const deploymentList = Array.isArray(deployments.data) ? deployments.data : [];
  const requestedScenario = searchParams.get('scenario') || '5g-sa';
  const selectedDeployment = deploymentList.find((item) => item.id === requestedScenario)
    || deploymentList.find((item) => item.id === '5g-sa')
    || deploymentList[0];
  const selectedScenario = selectedDeployment?.id || requestedScenario;
  const validation = useLatestValidation(selectedScenario);
  const checks = validation.data?.checks || [];
  const passed = checks.filter((check) => check.status === 'PASS').length;
  const warnings = checks.filter((check) => check.status === 'WARNING').length;
  const failed = checks.filter((check) => check.status === 'FAIL').length;
  const grafanaUrl = `${window.location.origin}/grafana/d/openlain5g-runtime/openlain5g-runtime?orgId=1&refresh=15s`;
  const componentsUrl = `${window.location.origin}/grafana/d/openlain5g-components/openlain5g-components?orgId=1&refresh=15s`;

  useEffect(() => {
    if (selectedDeployment && searchParams.get('scenario') !== selectedDeployment.id) {
      setSearchParams({ scenario: selectedDeployment.id }, { replace: true });
    }
  }, [searchParams, selectedDeployment, setSearchParams]);

  const selectScenario = (scenario: string) => setSearchParams({ scenario });
  const simulationProfiles = deploymentList.filter((item) => item.mode === 'simulation');
  const rfProfiles = deploymentList.filter((item) => item.mode !== 'simulation');

  return <section className="page-panel">
    <header className="console-page-hero observability-page-hero">
      <div className="console-page-hero-copy">
        <span className="eyebrow">📊 Observability</span>
        <h1>Metrics</h1>
        <p className="page-subtitle">Application telemetry, component activity, and validation evidence for each lab profile.</p>
        <div className="inline-actions">
          <label>Profile
            <select value={selectedScenario} onChange={(event) => selectScenario(event.target.value)} disabled={!deploymentList.length}>
              {simulationProfiles.length ? <optgroup label="Simulation profiles">{simulationProfiles.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup> : null}
              {rfProfiles.length ? <optgroup label="Guarded RF profiles">{rfProfiles.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup> : null}
            </select>
          </label>
          <a className="action-link" href={grafanaUrl} target="_blank" rel="noreferrer">Application runtime</a>
          <a className="action-link" href={componentsUrl} target="_blank" rel="noreferrer">Network components</a>
          <Link className="action-link" to={`/validation?scenario=${encodeURIComponent(selectedScenario)}`}>Open validation</Link>
        </div>
      </div>
      <figure>
        <img src="/images/lain5g/metrics-observability.webp" width="1672" height="941" alt="Isometric spectrum analyzer and abstract measurement charts for a mobile network lab" loading="lazy" decoding="async" />
        <figcaption><span>Runtime monitoring</span><strong>Prometheus · Grafana</strong></figcaption>
      </figure>
    </header>

    <div className="panel" style={{ marginTop: 18 }}>
      <div className="panel-heading">
        <div>
          <h3>Application runtime</h3>
          <p className="muted-text">Prometheus measures the OpenLain5G backend (API rate, latency, HTTP errors, process CPU and memory) and checks monitoring services. Network Components groups srsRAN, Open5GS, Kamailio/IMS, and data-service logs. Native radio and protocol KPIs are not exported by the current profile images yet.</p>
        </div>
        <a className="action-link" href={grafanaUrl} target="_blank" rel="noreferrer">View runtime dashboard</a>
      </div>
    </div>

    {deployments.isLoading || validation.isLoading ? <LoadingState /> : null}
    {deployments.error ? <ErrorAlert error={deployments.error} onRetry={() => deployments.refetch()} /> : null}
    {validation.error ? <ErrorAlert error={validation.error} onRetry={() => validation.refetch()} /> : null}
    {validation.data ? <>
      <section className="panel" style={{ marginTop: 18 }}>
        <div className="panel-heading">
          <div>
            <h3>Latest validation · {selectedDeployment?.name || selectedScenario}</h3>
            <p className="muted-text">Saved evidence for this profile · {validation.data.run_id ? `Run ${validation.data.run_id}` : 'No run recorded'} · {formatDate(validation.data.checked_at)}. Validation checks describe the last report; they do not indicate whether services are currently running.</p>
          </div>
          <StatusBadge status={validation.data.status} kind="validation" />
        </div>
      </section>
      <div className="summary-grid">
        <article className="summary-card"><div className="summary-label">Passed checks</div><div className="summary-value">{passed}</div></article>
        <article className="summary-card"><div className="summary-label">Warnings</div><div className="summary-value">{warnings}</div></article>
        <article className="summary-card"><div className="summary-label">Failed checks</div><div className="summary-value">{failed}</div></article>
        <article className="summary-card"><div className="summary-label">Report state</div><div className="summary-value"><StatusBadge status={validation.data.status} kind="validation" /></div></article>
      </div>
      {checks.length ? <div className="validation-layers" style={{ marginTop: 18 }}>{checks.map((check) => <article className="validation-layer" key={check.id}>
        <div className="validation-layer-header"><div><h3>{check.id}</h3><span className="muted-text">{check.detail || 'No evidence reported'}</span></div><StatusBadge status={check.status} kind="validation" /></div>
      </article>)}</div> : <EmptyState title="No checks in this report" message="Run validation for this profile to collect component and service evidence." />}
    </> : null}
  </section>;
}
