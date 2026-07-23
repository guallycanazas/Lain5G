import type { ValidationCheck } from '../types/validation';
import { extractDetectedValue, validationDescription } from '../utils/status';
import { StatusBadge } from './StatusBadge';

export function ValidationTable({ checks, checkedAt }: { checks: ValidationCheck[]; checkedAt?: string | null }) {
  if (!checks.length) return <div className="empty-state"><h3>No validation evidence</h3><p>Run validation to inspect infrastructure, control plane and user-plane checks.</p></div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Check</th><th>Status</th><th>Value</th><th>Evidence</th><th>Date</th></tr>
        </thead>
        <tbody>
          {checks.map((check) => {
            return (
              <tr key={check.id}>
                <td>{validationDescription(check.id)}<span className="validation-item-id">{check.id}</span></td>
                <td><StatusBadge status={check.status} kind="validation" /></td>
                <td>{extractDetectedValue(check.detail)}</td>
                <td>{check.detail || 'No evidence reported'}</td>
                <td>{checkedAt || 'No date'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
