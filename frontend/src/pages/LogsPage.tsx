import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ActionButton } from '../components/ActionButton';
import { ErrorAlert } from '../components/ErrorAlert';
import { LogsViewer } from '../components/LogsViewer';
import { deploymentsApi } from '../services/deploymentsApi';
import { useDeployments, useScenarioStatus } from '../hooks/useDeployment';
import { formatDate } from '../utils/dates';

export function LogsPage() {
  const deployments = useDeployments();
  const [scenario, setScenario] = useState('5g-sa');
  const [container, setContainer] = useState('all');
  const [tail, setTail] = useState(300);
  const [paused, setPaused] = useState(false);
  const [severity, setSeverity] = useState('all');
  const [search, setSearch] = useState('');
  const status = useScenarioStatus(scenario);
  const deploymentList = Array.isArray(deployments.data) ? deployments.data : [];
  const logs = useQuery({ queryKey: ['logs', scenario, container, tail], queryFn: () => deploymentsApi.logs(container === 'all' ? null : container, tail, scenario), refetchInterval: paused ? false : 5000 });
  const raw = logs.data?.command.stdout || '';
  const visible = raw.split('\n').filter((line) => (severity === 'all' || line.toLowerCase().includes(severity)) && (!search || line.toLowerCase().includes(search.toLowerCase()))).join('\n');

  return <section className="page-panel"><div className="page-heading"><div><span className="eyebrow">Observability</span><h1>Logs</h1><p className="page-subtitle">Controlled polling is active. WebSocket streaming is not available from the current backend.</p></div><span className="log-state">{paused ? 'Polling paused' : 'Polling every 5 seconds'}</span></div>
    <div className="panel logs-toolbar"><label>Scenario<select value={scenario} onChange={(event) => { setScenario(event.target.value); setContainer('all'); }}>{deploymentList.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Service<select value={container} onChange={(event) => setContainer(event.target.value)}><option value="all">All services</option>{(status.data?.containers || []).map((item) => <option key={item.name} value={item.service || item.name}>{item.service || item.name}</option>)}</select></label><label>Tail<select value={tail} onChange={(event) => setTail(Number(event.target.value))}>{[100, 300, 500, 1000, 5000].map((item) => <option key={item} value={item}>{item} lines</option>)}</select></label><label>Severity<select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="all">All</option><option value="error">Error</option><option value="warn">Warning</option><option value="info">Info</option></select></label><label className="spacer">Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter visible lines" /></label><ActionButton variant="secondary" onClick={() => setPaused((value) => !value)}>{paused ? 'Resume' : 'Pause'}</ActionButton><ActionButton variant="secondary" onClick={() => logs.refetch()} loading={logs.isFetching}>Refresh</ActionButton></div>
    {logs.error ? <ErrorAlert error={logs.error} onRetry={() => logs.refetch()} /> : null}<LogsViewer response={logs.data} text={visible || (raw ? 'No lines match the current filters.' : undefined)} title={`${scenario} logs`} /><p className="muted-text">Last update: {logs.data ? formatDate(logs.data.command.finished_at) : 'Not fetched yet'}. Logs are fetched through the existing allow-listed backend endpoint.</p>
  </section>;
}
