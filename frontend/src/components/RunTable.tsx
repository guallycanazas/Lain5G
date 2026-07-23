import { Link } from 'react-router-dom';
import type { RunSummary } from '../types/run';
import { durationBetween, formatDate } from '../utils/dates';
import { StatusBadge } from './StatusBadge';

export function RunTable({ runs }: { runs: RunSummary[] }) {
  const sortedRuns = [...runs].sort((a, b) => (b.started_at || '').localeCompare(a.started_at || ''));
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Run</th><th>Scenario</th><th>Date</th><th>Status</th><th>Duration</th><th>PASS/Claims</th></tr>
        </thead>
        <tbody>
          {sortedRuns.map((run) => (
            <tr key={run.run_id}>
              <td><Link to={`/runs/${encodeURIComponent(run.run_id)}`}>{run.run_id}</Link></td>
              <td>{run.scenario || 'Unavailable'}</td>
              <td>{formatDate(run.started_at)}</td>
              <td><StatusBadge status={run.status || 'unknown'} /></td>
              <td>{durationBetween(run.started_at, run.finished_at)}</td>
              <td>{run.validated_claims.length} claims</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
