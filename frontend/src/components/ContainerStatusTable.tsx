import type { ContainerStatus, DeploymentState } from '../types/deployment';
import { StatusBadge } from './StatusBadge';

type DisplayContainer = ContainerStatus & { expected: boolean; missing: boolean; conditional: boolean };

export function ContainerStatusTable({ containers, expectedServices = [], conditionalServices = [], deploymentState = 'unknown' }: { containers: ContainerStatus[]; expectedServices?: string[]; conditionalServices?: string[]; deploymentState?: DeploymentState }) {
  const expected = new Set(expectedServices);
  const conditional = new Set(conditionalServices);
  const requiredServices = expectedServices.filter((service) => !conditional.has(service));
  const byService = new Map(containers.filter((container) => container.service).map((container) => [container.service as string, container]));
  const rows: DisplayContainer[] = [
    ...expectedServices.map((service) => {
      const detected = byService.get(service);
      return detected
        ? { ...detected, expected: true, missing: false, conditional: conditional.has(service) }
        : conditional.has(service)
          ? { name: `expected-${service}`, service, status: 'Guarded standby', running: false, expected: true, missing: false, conditional: true }
          : { name: `expected-${service}`, service, status: deploymentState === 'stopped' ? 'Not started' : 'Expected service is not running', running: false, expected: true, missing: true, conditional: false };
    }),
    ...containers.filter((container) => !container.service || !expected.has(container.service)).map((container) => ({ ...container, expected: false, missing: false, conditional: false })),
  ];
  const runningExpected = requiredServices.filter((service) => byService.get(service)?.running).length;
  const aggregateStatus = requiredServices.length && runningExpected === requiredServices.length ? 'PASS' : deploymentState === 'stopped' ? 'stopped' : runningExpected ? 'PARTIAL' : 'FAIL';

  if (!rows.length) return <div className="empty-state"><h3>Deployment stopped</h3><p>No service inventory is registered for this scenario.</p></div>;
  return (
    <div className="service-inventory">
      <div className="service-inventory-summary"><div><strong>{runningExpected}/{requiredServices.length} required services running</strong><span>{containers.length} detected by Docker · {Math.max(requiredServices.length - runningExpected, 0)} required services missing · {conditionalServices.length} guarded service in standby</span></div><StatusBadge status={aggregateStatus} kind={aggregateStatus === 'stopped' ? 'deployment' : 'validation'} /></div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Component</th><th>Service</th><th>Status</th><th>Identifier</th><th>Reason</th></tr>
          </thead>
          <tbody>
            {rows.map((container) => {
              const stoppedStatus = container.conditional ? 'standby' : deploymentState === 'stopped' ? 'stopped' : 'FAIL';
              const reason = container.conditional && !container.running
                ? 'Guarded RF service; starts only during an authorized, time-limited RF session.'
                : container.missing
                ? deploymentState === 'stopped' ? 'Expected by the profile; start the scenario to detect it.' : 'Expected by the profile but not running. Inspect its logs and dependencies.'
                : container.expected ? container.status : `${container.status} · Additional runtime service.`;
              return (
                <tr key={container.name} className={container.missing ? 'service-missing' : ''}>
                  <td>{(container.service || container.name).toUpperCase()}</td>
                  <td>{container.service || 'Unmapped service'}</td>
                  <td><StatusBadge status={container.running ? 'running' : stoppedStatus} kind={container.running || stoppedStatus === 'stopped' || stoppedStatus === 'standby' ? 'deployment' : 'validation'} /></td>
                  <td>{container.missing || (container.conditional && !container.running) ? <span className="muted-text">Not active</span> : <code>{container.name}</code>}</td>
                  <td>{reason}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
