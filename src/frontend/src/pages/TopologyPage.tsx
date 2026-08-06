import { useState } from 'react';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { TopologyPanel } from '../components/TopologyPanel';
import { useDeployments, useScenarioStatus } from '../hooks/useDeployment';
import { useLatestValidation } from '../hooks/useValidation';

export function TopologyPage() {
  const deployments = useDeployments();
  const [scenario, setScenario] = useState('5g-sa');
  const status = useScenarioStatus(scenario);
  const validation = useLatestValidation();

  return <section className="page-panel">
    <div className="page-heading"><div><span className="eyebrow">Observability</span><h1>Topology</h1><p className="page-subtitle">Container health and validation evidence are shown independently.</p></div><label>Scenario<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{(deployments.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div>
    {status.isLoading ? <LoadingState /> : null}
    {status.error ? <ErrorAlert error={status.error} onRetry={() => status.refetch()} /> : null}
    <TopologyPanel containers={status.data?.containers || []} checks={validation.data?.scenario === scenario ? validation.data.checks : []} checkedAt={status.data?.checked_at} title={`${scenario} topology`} />
  </section>;
}
