import type { ContainerStatus } from '../types/deployment';
import type { ValidationCheck } from '../types/validation';
import { StatusBadge } from './StatusBadge';

const labels: Record<string, string> = {
  mongo: 'MongoDB', nrf: 'NRF', amf: 'AMF', smf: 'SMF', upf: 'UPF', ausf: 'AUSF', udm: 'UDM', udr: 'UDR', pcf: 'PCF',
  gnb: 'gNB', enb: 'eNB', ue: 'UE', mme: 'MME', hss: 'HSS', pgwu: 'PGW-U', pgwc: 'PGW-C', pcscf: 'P-CSCF', icscf: 'I-CSCF', scscf: 'S-CSCF',
};

function evidenceFor(service: string, checks: ValidationCheck[]) {
  const normalized = service.toLowerCase();
  return checks.some((check) => check.id.toLowerCase().includes(normalized) && check.status === 'PASS');
}

function protocolFor(service: string, checks: ValidationCheck[]) {
  const related: Record<string, string[]> = { amf: ['ng_connection', 'ng_setup', 'ue_registration'], mme: ['s1_setup', 'ue_attach'], gnb: ['ng_connection', 'ng_setup'], enb: ['s1_setup'], smf: ['pdu_session'], upf: ['ping'] };
  return (related[service.toLowerCase()] || []).some((id) => checks.some((check) => check.id === id && check.status === 'PASS'));
}

export function TopologyPanel({ containers, checks = [], title = 'Network topology', checkedAt }: { containers: ContainerStatus[]; checks?: ValidationCheck[]; title?: string; checkedAt?: string }) {
  if (!containers.length) {
    return <div className="empty-state"><h3>Deployment stopped</h3><p>Service telemetry will become available after startup.</p></div>;
  }

  return (
    <section>
      <div className="panel-heading"><div><span className="eyebrow">Live inventory</span><h3>{title}</h3></div><StatusBadge status={containers.some((container) => container.running) ? 'running' : 'stopped'} /></div>
      <div className="topology" aria-label="Network topology based on services reported by the API">
        <div className="topology-grid">
          {containers.map((container) => {
            const healthy = container.running;
            const evidence = evidenceFor(container.service || container.name, checks);
            const protocol = protocolFor(container.service || '', checks);
            return (
              <article className={`topology-node ${healthy && evidence ? 'active' : ''}`} key={container.name}>
                <strong>{labels[(container.service || '').toLowerCase()] || container.service || container.name}</strong>
                <small>{container.name}</small>
                <div className="node-signals" title="Container, connectivity, and validation evidence">
                  <span className={`node-signal ${healthy ? 'good' : 'warning'}`} /><span className={`node-signal ${protocol ? 'good' : 'warning'}`} /><span className={`node-signal ${evidence ? 'good' : 'warning'}`} />
                </div>
                <small>{healthy ? 'Container running' : 'Container stopped'}{protocol ? ' / protocol evidence' : ' / protocol not evidenced'}</small>
                <small>Last update: {checkedAt || 'Not reported'}</small>
              </article>
            );
          })}
        </div>
      </div>
      <div className="topology-legend"><span className="legend-item"><span className="node-signal good" /> Container health, protocol, validation</span><span className="legend-item"><span className="node-signal warning" /> Evidence not reported</span><span>Links become active only when validation evidence is available.</span></div>
    </section>
  );
}
