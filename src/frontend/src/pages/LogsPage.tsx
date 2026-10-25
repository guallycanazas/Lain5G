import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router';
import { Activity, AlertTriangle, CircleAlert, Search, X } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ErrorAlert } from '../components/ErrorAlert';
import { LogsViewer } from '../components/LogsViewer';
import { deploymentsApi } from '../services/deploymentsApi';
import { useDeployments, useScenarioStatus } from '../hooks/useDeployment';
import { formatDate } from '../utils/dates';
import type { ImsActivityEvent } from '../types/deployment';

function activityLabel(event: ImsActivityEvent): string {
  if (event.phase === 'observed') return 'Observed at P-CSCF';
  if (event.phase === 'forwarded') return 'Forwarded by S-CSCF';
  if (event.phase === 'not_routed') return event.status_code === 480 ? 'Destination not registered (SIP 480)' : `Not routed${event.status_code ? ` (SIP ${event.status_code})` : ''}`;
  if (event.status_code === 100) return 'Trying';
  if (event.status_code === 180) return 'Ringing';
  if (event.status_code === 200 && event.method === 'INVITE') return 'Answered (SIP 200 OK)';
  if (event.status_code === 200 && event.method === 'BYE') return 'Call ended (SIP 200 OK)';
  if (event.status_code === 200 && event.method === 'CANCEL') return 'Call cancelled (SIP 200 OK)';
  if (event.status_code === 200 && event.method === 'MESSAGE') return 'Accepted by SIP destination (SIP 200 OK)';
  if (event.status_code && event.status_code >= 400) return `Rejected or failed (SIP ${event.status_code})`;
  return event.status_code ? `SIP ${event.status_code}` : 'No response recorded';
}

function activityKind(method: ImsActivityEvent['method']): string {
  if (method === 'INVITE') return 'Call setup';
  if (method === 'MESSAGE') return 'SIP message';
  if (method === 'BYE') return 'Call ended';
  return 'Call cancelled';
}

function activityStatusClass(event: ImsActivityEvent): string {
  if (event.phase === 'observed' || event.phase === 'forwarded') return 'status-partial';
  if (event.phase === 'not_routed' || (event.status_code !== null && event.status_code >= 400)) return 'status-fail';
  if (event.status_code === 180) return 'status-warning';
  if (event.status_code === 200) return 'status-pass';
  return 'status-unknown';
}

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
  const currentDeployment = deploymentList.find((item) => item.id === scenario);
  const supportsImsActivity = Boolean(currentDeployment?.components.some((component) => component === 'pcscf' || component === 'scscf'));
  const logs = useQuery({ queryKey: ['logs', scenario, container, tail], queryFn: () => deploymentsApi.logs(container === 'all' ? null : container, tail, scenario), refetchInterval: paused ? false : 5000 });
  const activity = useQuery({ queryKey: ['ims-activity', scenario, tail], queryFn: () => deploymentsApi.imsActivity(tail, scenario), enabled: supportsImsActivity, refetchInterval: paused ? false : 5000 });
  const raw = logs.data?.command.stdout || '';
  const allLines = useMemo(() => raw.split('\n').filter(Boolean), [raw]);
  const classify = (line: string) => /\b(fatal|critical|error|err)\b/i.test(line) ? 'error' : /\b(warn|warning)\b/i.test(line) ? 'warn' : /\b(info|notice)\b/i.test(line) ? 'info' : /\b(debug|trace)\b/i.test(line) ? 'debug' : 'other';
  const visibleLines = allLines.filter((line) => (severity === 'all' || classify(line) === severity) && (!search || line.toLowerCase().includes(search.toLowerCase())));
  const visible = visibleLines.join('\n');
  const errorCount = allLines.filter((line) => classify(line) === 'error').length;
  const warningCount = allLines.filter((line) => classify(line) === 'warn').length;

  return <section className="page-panel logs-page"><header className="console-page-hero logs-hero"><div className="console-page-hero-copy"><span className="eyebrow"><Activity size={14} /> Observability</span><h1>Logs</h1><p className="page-subtitle">Find service events and export filtered logs.</p><div className="log-state"><span className={`live-indicator ${paused ? 'paused' : ''}`} />{paused ? 'Auto refresh paused' : 'Auto refresh every 5 seconds'}</div></div><figure><img src="/images/lain5g/logs-investigation-v2.webp" width="1672" height="941" alt="Service log viewer tracing an error to the affected container" loading="lazy" decoding="async" /><figcaption><span>Service investigation</span><strong>Find · correlate · export</strong></figcaption></figure></header>
    <div className="panel logs-toolbar"><label>Scenario<select value={scenario} onChange={(event) => { setScenario(event.target.value); setContainer('all'); }}>{deploymentList.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Service<select value={container} onChange={(event) => setContainer(event.target.value)}><option value="all">All services</option>{(status.data?.containers || []).map((item) => <option key={item.name} value={item.service || item.name}>{item.service || item.name}</option>)}</select></label><label>Latest<select value={tail} onChange={(event) => setTail(Number(event.target.value))}>{[100, 300, 500, 1000, 5000].map((item) => <option key={item} value={item}>{item} lines</option>)}</select></label><label>Level<select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="all">All levels</option><option value="error">Errors</option><option value="warn">Warnings</option><option value="info">Info</option><option value="debug">Debug</option></select></label><label className="log-search"><span><Search size={14} /> Search logs</span><div><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Text, service, or message" />{search ? <button type="button" aria-label="Clear search" onClick={() => setSearch('')}><X size={14} /></button> : null}</div></label><ActionButton variant="secondary" onClick={() => setPaused((value) => !value)}>{paused ? 'Resume' : 'Pause'}</ActionButton><ActionButton variant="secondary" onClick={() => { void logs.refetch(); if (supportsImsActivity) void activity.refetch(); }} loading={logs.isFetching || activity.isFetching}>Refresh</ActionButton></div>
    {supportsImsActivity ? <section className="panel ims-activity-panel"><div className="panel-heading"><div><span className="eyebrow">IMS signaling</span><h3>Calls and messages</h3></div></div><p className="ims-activity-note">SIP signaling events · message content hidden</p>{activity.error ? <ErrorAlert error={activity.error} onRetry={() => activity.refetch()} /> : null}{activity.isLoading ? <div className="ims-activity-empty">Loading IMS events…</div> : activity.data?.events.length ? <div className="table-wrap ims-activity-table-wrap"><table className="ims-activity-table"><thead><tr><th>Time</th><th>Type</th><th>From → To</th><th>Observed result</th><th>Service</th></tr></thead><tbody>{activity.data.events.map((event, index) => <tr key={`${event.flow_id}-${event.phase}-${event.status_code}-${index}`}><td>{event.timestamp ? formatDate(event.timestamp) : 'Time unavailable'}</td><td><span className="ims-method">{event.method}</span><small>{activityKind(event.method)}</small></td><td><code>{event.from_user}</code><span className="ims-activity-arrow">→</span><code>{event.to_user}</code></td><td><span className={`status-badge ${activityStatusClass(event)}`}>{activityLabel(event)}</span></td><td>{event.service}</td></tr>)}</tbody></table></div> : <div className="ims-activity-empty"><strong>No SIP events yet</strong><p>Start an IMS profile and place a call or send a SIP message.</p></div>}<small className="muted-text">{activity.data?.source === 'container_logs' ? 'Container logs' : 'IMS logs'} · {activity.data?.events.length ?? 0} events</small></section> : null}
    <div className="log-summary"><span>{visibleLines.length} shown / {allLines.length} lines</span><span className="log-count-error"><CircleAlert size={14} />{errorCount} errors</span><span className="log-count-warning"><AlertTriangle size={14} />{warningCount} warnings</span></div>
    {logs.error ? <ErrorAlert error={logs.error} onRetry={() => logs.refetch()} /> : null}<LogsViewer response={logs.data} text={visible || (raw ? 'No lines match the current filters.' : undefined)} title={`${scenario} · ${container === 'all' ? 'all services' : container}`} isLoading={logs.isLoading} /><p className="muted-text">Updated: {logs.data ? formatDate(logs.data.command.finished_at) : 'Not yet'}.</p>
  </section>;
}
