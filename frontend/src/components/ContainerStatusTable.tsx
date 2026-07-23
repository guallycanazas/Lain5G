import type { ContainerStatus } from '../types/deployment';
import { StatusBadge } from './StatusBadge';

export function ContainerStatusTable({ containers }: { containers: ContainerStatus[] }) {
  if (!containers.length) return <div className="empty-state"><h3>Deployment stopped</h3><p>Service telemetry will become available after startup.</p></div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Component</th><th>Service</th><th>Status</th><th>Identifier</th><th>Notes</th></tr>
        </thead>
        <tbody>
          {containers.map((container) => {
            return (
              <tr key={container.name}>
                <td>{(container.service || container.name).toUpperCase()}</td>
                <td>{container.service || 'Unmapped service'}</td>
                <td><StatusBadge status={container.running ? 'running' : 'stopped'} /></td>
                <td><code>{container.name}</code></td>
                <td>{container.status}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
