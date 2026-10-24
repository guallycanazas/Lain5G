import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router';
import { Activity, AlertTriangle, CircleAlert, Info, Search, X } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ErrorAlert } from '../components/ErrorAlert';
import { LogsViewer } from '../components/LogsViewer';
import { deploymentsApi } from '../services/deploymentsApi';
import { useDeployments, useScenarioStatus } from '../hooks/useDeployment';
import { formatDate } from '../utils/dates';

export function LogsPage() {
  const deployments = useDeployments();
  const [searchParams] = useSearchParams();
  const [scenario, setScenario] = useState(searchParams.get('scenario') || '5g-sa');
  const [container, setContainer] = useState('all');
  const [tail, setTail] = useState(300);
  const [paused, setPaused] = useState(false);
  const [severity, setSeverity] = useState('all');
  const [search, setSearch] = useState('');
  const status = useScenarioStatus(scenario);
  const deploymentList = Array.isArray(deployments.data) ? deployments.data : [];
  const logs = useQuery({ queryKey: ['logs', scenario, container, tail], queryFn: () => deploymentsApi.logs(container === 'all' ? null : container, tail, scenario), refetchInterval: paused ? false : 5000 });
  const raw = logs.data?.command.stdout || '';
  const allLines = useMemo(() => raw.split('\n').filter(Boolean), [raw]);
  const classify = (line: string) => /\b(fatal|critical|error|err)\b/i.test(line) ? 'error' : /\b(warn|warning)\b/i.test(line) ? 'warn' : /\b(info|notice)\b/i.test(line) ? 'info' : /\b(debug|trace)\b/i.test(line) ? 'debug' : 'other';
  const visibleLines = allLines.filter((line) => (severity === 'all' || classify(line) === severity) && (!search || line.toLowerCase().includes(search.toLowerCase())));
  const visible = visibleLines.join('\n');
  const errorCount = allLines.filter((line) => classify(line) === 'error').length;
  const warningCount = allLines.filter((line) => classify(line) === 'warn').length;

  return <section className="page-panel logs-page"><header className="console-page-hero logs-hero"><div className="console-page-hero-copy"><span className="eyebrow"><Activity size={14} /> Observability</span><h1>Logs</h1><p className="page-subtitle">Trace service startup and shutdown, find errors, and save filtered evidence.</p><div className="log-state"><span className={`live-indicator ${paused ? 'paused' : ''}`} />{paused ? 'Auto refresh paused' : 'Auto refresh every 5 seconds'}</div></div><figure><img src="/images/lain5g/logs-investigation-v2.webp" width="1672" height="941" alt="Service log viewer tracing an error to the affected container" loading="lazy" decoding="async" /><figcaption><span>Service investigation</span><strong>Find · correlate · export</strong></figcaption></figure></header>
    <div className="panel logs-toolbar"><label>Scenario<select value={scenario} onChange={(event) => { setScenario(event.target.value); setContainer('all'); }}>{deploymentList.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Service<select value={container} onChange={(event) => setContainer(event.target.value)}><option value="all">All services</option>{(status.data?.containers || []).map((item) => <option key={item.name} value={item.service || item.name}>{item.service || item.name}</option>)}</select></label><label>Latest<select value={tail} onChange={(event) => setTail(Number(event.target.value))}>{[100, 300, 500, 1000, 5000].map((item) => <option key={item} value={item}>{item} lines</option>)}</select></label><label>Level<select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="all">All levels</option><option value="error">Errors</option><option value="warn">Warnings</option><option value="info">Info</option><option value="debug">Debug</option></select></label><label className="log-search"><span><Search size={14} /> Search logs</span><div><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Text, service, or message" />{search ? <button type="button" aria-label="Clear search" onClick={() => setSearch('')}><X size={14} /></button> : null}</div></label><ActionButton variant="secondary" onClick={() => setPaused((value) => !value)}>{paused ? 'Resume' : 'Pause'}</ActionButton><ActionButton variant="secondary" onClick={() => logs.refetch()} loading={logs.isFetching}>Refresh</ActionButton></div>
    <aside className="log-purpose"><Info size={17} /><div><strong>What logs are for</strong><p>Use these container messages to diagnose profile startup, shutdown, and service errors. Match their timestamps with <Link to="/runs">Runs</Link> or <Link to="/validation">Validation</Link>, then copy or download the filtered output as evidence. Live SDR and RF measurements belong in Metrics or the validation report.</p></div></aside>
    <div className="log-summary"><span>{visibleLines.length} shown / {allLines.length} lines</span><span className="log-count-error"><CircleAlert size={14} />{errorCount} errors</span><span className="log-count-warning"><AlertTriangle size={14} />{warningCount} warnings</span></div>
    {logs.error ? <ErrorAlert error={logs.error} onRetry={() => logs.refetch()} /> : null}<LogsViewer response={logs.data} text={visible || (raw ? 'No lines match the current filters.' : undefined)} title={`${scenario} · ${container === 'all' ? 'all services' : container}`} isLoading={logs.isLoading} /><p className="muted-text">Last update: {logs.data ? formatDate(logs.data.command.finished_at) : 'Not fetched yet'}. Logs are fetched through the existing allow-listed backend endpoint.</p>
  </section>;
}
