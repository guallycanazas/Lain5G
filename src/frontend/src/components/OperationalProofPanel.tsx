import { Fragment } from 'react';
import { Link } from 'react-router';
import { ArrowRight, RadioTower, ShieldCheck } from 'lucide-react';
import type { ValidationCheck, ValidationState } from '../types/validation';
import { formatDate } from '../utils/dates';
import { aggregateValidationStatus, validationDescription } from '../utils/status';
import { ActionButton } from './ActionButton';
import { StatusBadge } from './StatusBadge';

interface ProofStage {
  label: string;
  description: string;
  source: string;
  checkIds: string[];
}

interface OperationalProofPanelProps {
  scenarioId: string;
  rfCapable: boolean;
  checks: ValidationCheck[];
  checkedAt?: string | null;
  runId?: string | null;
  loading: boolean;
  onValidate: () => void;
  onOpenLogs: () => void;
}

const core4g = ['mongo', 'mme', 'hss', 'sgwc', 'sgwu', 'pgwc', 'pgwu', 'pcrf'];
const core5g = ['mongo', 'nrf', 'amf', 'smf', 'upf', 'ausf', 'udm', 'udr', 'pcf'];

function stagesFor(scenarioId: string, rfCapable: boolean): ProofStage[] {
  const is4g = scenarioId.startsWith('4g-');
  if (rfCapable) {
    return [
      {
        label: 'X310 detected',
        description: 'Host, Ethernet and UHD evidence for the physical SDR.',
        source: 'hardware-check + UHD probe',
        checkIds: is4g
          ? ['hardware_detected', 'ethernet_link', 'uhd_available', 'uhd_fpga_compatible']
          : ['hardware_detected', 'uhd_available'],
      },
      {
        label: 'RF safety gate',
        description: 'Authorization, attenuation and guarded preflight.',
        source: 'RF preflight artifact',
        checkIds: ['rf_preflight'],
      },
      {
        label: is4g ? 'EPC + IMS ready' : '5G Core + IMS ready',
        description: 'Core and compact IMS services required by the RF profile are ready.',
        source: 'Docker runtime + core readiness logs',
        checkIds: is4g ? ['epc_services', 'mme_ready', 'ims_services'] : ['core_services', 'amf_ready', 'ims_services'],
      },
      {
        label: is4g ? 'LTE eNB active' : '5G gNB active',
        description: 'Time-limited RF-capable process observed; this alone does not prove over-air reception.',
        source: is4g ? 'enb-x310 session log' : 'gnb-x310 session log',
        checkIds: [is4g ? 'enb_started' : 'gnb_started'],
      },
      {
        label: is4g ? 'S1 control link' : 'NG control link',
        description: 'RAN-to-core signaling found in session-scoped logs.',
        source: is4g ? 'eNB/MME logs' : 'gNB/AMF logs',
        checkIds: [is4g ? 's1_setup' : 'ng_setup'],
      },
      {
        label: 'UE over air',
        description: 'External UE reception and registration; never inferred from a running RAN process.',
        source: 'UE/core registration evidence',
        checkIds: ['ue_registration'],
      },
    ];
  }

  return [
    {
      label: is4g ? 'EPC ready' : '5G Core ready',
      description: 'Required core processes respond and remain active.',
      source: 'Docker runtime + core checks',
      checkIds: is4g ? core4g : core5g,
    },
    {
      label: is4g ? 'S1 connected' : 'NG connected',
      description: 'The simulated RAN completed control-plane setup.',
      source: is4g ? 'eNB/MME logs' : 'gNB/AMF logs',
      checkIds: [is4g ? 's1_setup' : 'ng_setup'],
    },
    {
      label: is4g ? 'UE + bearer' : 'UE + PDU session',
      description: 'Registration and session establishment were observed.',
      source: is4g ? 'MME/eNB/UE logs' : 'AMF/UE logs',
      checkIds: is4g ? ['ue_registration', 'default_bearer'] : ['ue_registration', 'pdu_session'],
    },
    {
      label: 'UE network',
      description: 'A tunnel interface and assigned IPv4 address exist inside the UE.',
      source: is4g ? 'ip link/addr on tun_srsue' : 'ip link/addr on uesimtun0',
      checkIds: ['ue_tun', 'ue_ip'],
    },
    {
      label: 'User-plane traffic',
      description: 'Ping succeeded while explicitly bound to the UE tunnel.',
      source: is4g ? 'ping -I tun_srsue' : 'ping -I uesimtun0',
      checkIds: [is4g ? 'data_ping' : 'ping'],
    },
  ];
}

function stageStatus(stage: ProofStage, byId: Map<string, ValidationCheck>): ValidationState {
  const checks = stage.checkIds.map((id) => byId.get(id)).filter((check): check is ValidationCheck => Boolean(check));
  if (!checks.length) return 'NOT_TESTED';
  const status = aggregateValidationStatus(checks);
  if (status === 'PASS' && checks.length !== stage.checkIds.length) return 'NOT_TESTED';
  return status;
}

export function OperationalProofPanel({ scenarioId, rfCapable, checks, checkedAt, runId, loading, onValidate, onOpenLogs }: OperationalProofPanelProps) {
  const stages = stagesFor(scenarioId, rfCapable);
  const byId = new Map(checks.map((check) => [check.id, check]));
  const resolved = stages.map((stage) => ({ stage, status: stageStatus(stage, byId) }));
  const passed = resolved.filter((item) => item.status === 'PASS').length;
  const overall = checks.length ? aggregateValidationStatus(checks) : 'NOT_TESTED';

  return <section className={`operational-proof ${rfCapable ? 'rf' : 'simulation'}`} aria-label="Operational proof">
    <div className="operational-proof-heading">
      <div className="operational-proof-title">
        <span className="proof-mark">{rfCapable ? <RadioTower size={20} /> : <ShieldCheck size={20} />}</span>
        <div><span className="eyebrow">Independent operational proof</span><h3>{rfCapable ? 'Guarded RF evidence chain' : 'End-to-end simulation evidence chain'}</h3></div>
      </div>
      <div className="operational-proof-result"><strong>{passed}/{stages.length} stages proven</strong><StatusBadge status={overall} kind="validation" /></div>
    </div>
    <p className="proof-trust-note">Green means the validator observed the required command or log evidence. A running container alone never proves registration, RF reception, an assigned IP, or user-plane traffic.</p>
    <div className="proof-chain">
      {resolved.map(({ stage, status }, index) => {
        const observed = stage.checkIds.filter((id) => byId.get(id)?.status === 'PASS').length;
        return <Fragment key={stage.label}>
          <article className={`proof-stage ${status.toLowerCase()}`}>
            <div className="proof-stage-top"><span>{index + 1}</span><StatusBadge status={status} kind="validation" /></div>
            <strong>{stage.label}</strong>
            <p>{stage.description}</p>
            <dl><dt>Source</dt><dd>{stage.source}</dd><dt>Signals</dt><dd>{observed}/{stage.checkIds.length} PASS</dd></dl>
            <div className="proof-signal-list">{stage.checkIds.map((id) => <span key={id} title={validationDescription(id)} className={byId.get(id)?.status.toLowerCase() || 'not_tested'}>{id}</span>)}</div>
          </article>
          {index < resolved.length - 1 ? <ArrowRight className="proof-arrow" aria-hidden="true" /> : null}
        </Fragment>;
      })}
    </div>
    <div className="operational-proof-footer">
      <span>{runId ? <>Validator run <Link to={`/runs/${runId}`}><code>{runId}</code></Link>{checkedAt ? ` · ${formatDate(checkedAt)}` : ''}</> : 'No immutable validation run is available yet.'}</span>
      <div className="actions-row"><ActionButton loading={loading} onClick={onValidate}>Run evidence check</ActionButton><ActionButton variant="secondary" onClick={onOpenLogs}>Inspect live logs</ActionButton>{runId ? <Link className="action-link" to={`/runs/${runId}`}>Open run evidence</Link> : null}</div>
    </div>
  </section>;
}
