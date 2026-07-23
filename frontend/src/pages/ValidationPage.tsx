import { useState } from 'react';
import { ActionButton } from '../components/ActionButton';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useDeployments, useScenarioActions } from '../hooks/useDeployment';
import { useLatestValidation } from '../hooks/useValidation';
import type { ValidationCheck } from '../types/validation';
import { formatDate } from '../utils/dates';
import { validationDescription } from '../utils/status';

const layers = [
  { title: 'Infrastructure', ids: ['mongo', 'hardware', 'ethernet', 'uhd', 'fpga'] },
  { title: 'Core control plane', ids: ['nrf', 'amf', 'smf', 'ausf', 'udm', 'udr', 'pcf', 'mme', 'hss', 'ng_connection', 'ng_setup', 's1_setup'] },
  { title: 'Radio access', ids: ['preflight', 'enb_started', 'gnb_started', 'srsenb', 'auto_stop'] },
  { title: 'UE registration', ids: ['ue_registration', 'ue_attach'] },
  { title: 'Session establishment', ids: ['pdu_session', 'default_bearer', 'bearer'] },
  { title: 'IP and TUN', ids: ['ue_tun', 'ue_ip', 'tun'] },
  { title: 'User plane', ids: ['ping', 'data_plane'] },
  { title: 'IMS and voice', ids: ['ims', 'dns', 'sip_register', 'volte', 'vonr'] },
];

function layerFor(check: ValidationCheck) {
  const id = check.id.toLowerCase();
  return layers.find((layer) => layer.ids.some((item) => id.includes(item)))?.title || 'Other evidence';
}

export function ValidationPage() {
  const deployments = useDeployments();
  const [scenario, setScenario] = useState('5g-sa');
  const latest = useLatestValidation();
  const actions = useScenarioActions(scenario);
  const report = actions.validate.data || (latest.data?.scenario === scenario ? latest.data : undefined);
  const deploymentList = Array.isArray(deployments.data) ? deployments.data : [];
  const grouped = new Map<string, ValidationCheck[]>();
  (report?.checks || []).forEach((check) => { const layer = layerFor(check); grouped.set(layer, [...(grouped.get(layer) || []), check]); });
  const displayLayers = [...layers.map((layer) => layer.title), ...[...grouped.keys()].filter((layer) => !layers.some((item) => item.title === layer))];

  return <section className="page-panel"><div className="page-heading"><div><span className="eyebrow">Observability</span><h1>Validation</h1><p className="page-subtitle">Evidence is grouped by network layer. Container runtime does not prove protocol or user-plane success.</p></div><div className="inline-actions"><label>Scenario<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{deploymentList.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><ActionButton onClick={() => actions.validate.mutate()} loading={actions.validate.isPending}>Run validation</ActionButton></div></div>
    {latest.isLoading ? <LoadingState /> : null}{latest.error && !report ? <ErrorAlert error={latest.error} onRetry={() => latest.refetch()} /> : null}{actions.validate.error ? <ErrorAlert error={actions.validate.error} /> : null}
    {report ? <><section className="panel"><dl className="facts compact"><dt>Overall result</dt><dd><StatusBadge status={report.status} kind="validation" /></dd><dt>Run</dt><dd><code>{report.run_id || 'No run ID'}</code></dd><dt>Timestamp</dt><dd>{formatDate(report.checked_at)}</dd><dt>Scenario</dt><dd>{report.scenario}</dd></dl></section><div className="validation-layers" style={{ marginTop: 18 }}>{displayLayers.map((layer) => { const checks = grouped.get(layer) || []; return <section className="validation-layer" key={layer}><div className="validation-layer-header"><h3>{layer}</h3><span className="muted-text">{checks.length ? `${checks.length} checks` : 'No checks reported'}</span></div>{checks.length ? checks.map((check) => <article className="validation-item" key={check.id}><div><span className="validation-item-name">{validationDescription(check.id)}</span><span className="validation-item-id">{check.id}</span></div><StatusBadge status={check.status} kind="validation" /><div className="validation-item-detail">{check.detail || 'No evidence reported. Run the related validation or inspect logs.'}</div></article>) : <div className="validation-item"><div className="validation-item-name">Not tested</div><StatusBadge status="NOT_TESTED" kind="validation" /><div className="validation-item-detail">This report does not include evidence for this layer.</div></div>}</section>; })}</div></> : <div className="empty-state"><h3>No validation report selected</h3><p>Run validation for the selected scenario to collect protocol, UE and user-plane evidence.</p></div>}
  </section>;
}
