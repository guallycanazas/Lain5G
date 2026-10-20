import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ActionButton } from '../components/ActionButton';
import { ErrorAlert } from '../components/ErrorAlert';
import { LogsViewer } from '../components/LogsViewer';
import { deploymentsApi } from '../services/deploymentsApi';
import { useDeployments } from '../hooks/useDeployment';
import { formatDate } from '../utils/dates';
import { serviceLabel } from '../utils/serviceLabels';

export function LogsPage() {
  const deployments = useDeployments();
  const [scenario, setScenario] = useState('5g-sa');
  const [container, setContainer] = useState('all');
  const [tail, setTail] = useState(500);
  const [paused, setPaused] = useState(false);
  const [severity, setSeverity] = useState('all');
  const [search, setSearch] = useState('');
  const deploymentList = Array.isArray(deployments.data) ? deployments.data : [];
  const logs = useQuery({ queryKey: ['logs', scenario, container, tail], queryFn: () => deploymentsApi.logs(container === 'all' ? null : container, tail, scenario), refetchInterval: paused ? false : 2500, refetchIntervalInBackground: false });
  const raw = logs.data?.command.stdout || '';
  const selectedDeployment = deploymentList.find((item) => item.id === scenario);
  const matchesSeverity = (line: string) => severity === 'all' || (severity === 'error' ? /\b(error|fail|fatal|critical)\b/i.test(line) : line.toLowerCase().includes(severity));
  const visible = raw.split('\n').filter((line) => matchesSeverity(line) && (!search || line.toLowerCase().includes(search.toLowerCase()))).join('\n');

  return <section className="page-panel"><div className="page-heading"><div><span className="eyebrow">Observability</span><h1>Logs</h1><p className="page-subtitle">Live log polling is available for every profile and its configured services.</p></div><span className="log-state">{paused ? 'Polling paused' : 'Polling every 2.5 seconds'}</span></div>
    <div className="panel logs-toolbar"><label>Scenario<select value={scenario} onChange={(event) => { setScenario(event.target.value); setContainer('all'); }}>{deploymentList.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Service<select value={container} onChange={(event) => setContainer(event.target.value)}><option value="all">All services</option>{(selectedDeployment?.components || []).map((service) => <option key={service} value={service}>{serviceLabel(service)}</option>)}</select></label><label>Tail<select value={tail} onChange={(event) => setTail(Number(event.target.value))}>{[100, 300, 500, 1000, 5000].map((item) => <option key={item} value={item}>{item} lines</option>)}</select></label><label>Severity<select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="all">All</option><option value="error">Error</option><option value="warn">Warning</option><option value="info">Info</option></select></label><label className="spacer">Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter visible lines" /></label><ActionButton variant="secondary" onClick={() => setPaused((value) => !value)}>{paused ? 'Resume' : 'Pause'}</ActionButton><ActionButton variant="secondary" onClick={() => logs.refetch()} loading={logs.isFetching}>Refresh</ActionButton></div>
    {logs.error ? <ErrorAlert error={logs.error} onRetry={() => logs.refetch()} /> : null}<LogsViewer response={logs.data} text={visible || (raw ? 'No lines match the current filters.' : undefined)} title={`${selectedDeployment?.name || 'Profile'} logs`} /><p className="muted-text">Last update: {logs.data ? formatDate(logs.data.command.finished_at) : 'Not fetched yet'}. Logs are fetched through the existing allow-listed backend endpoint.</p>
  </section>;
}
