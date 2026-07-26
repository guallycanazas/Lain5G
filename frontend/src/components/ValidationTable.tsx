import type { ValidationCheck } from '../types/validation';
import { extractDetectedValue, validationDescription } from '../utils/status';
import { StatusBadge } from './StatusBadge';

export function ValidationTable({ checks, checkedAt, expectedChecks = [] }: { checks: ValidationCheck[]; checkedAt?: string | null; expectedChecks?: string[] }) {
  const byId = new Map(checks.map((check) => [check.id, check]));
  const ids = [...expectedChecks, ...checks.map((check) => check.id).filter((id) => !expectedChecks.includes(id))];
  const displayedChecks: ValidationCheck[] = ids.map((id) => byId.get(id) || { id, status: 'NOT_TESTED', detail: 'No evidence was recorded for this check in the latest completed validation.' });
  if (!displayedChecks.length) return <div className="empty-state"><h3>No validation evidence</h3><p>Run validation to inspect infrastructure, control plane and user-plane checks.</p></div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Check</th><th>Status</th><th>Value</th><th>Evidence</th><th>Date</th></tr>
        </thead>
        <tbody>
          {displayedChecks.map((check) => {
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
