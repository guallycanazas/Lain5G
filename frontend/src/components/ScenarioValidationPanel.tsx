import { Activity, CheckCircle2 } from 'lucide-react';
import type { ValidationCheck } from '../types/validation';
import { formatDate } from '../utils/dates';
import { validationDescription } from '../utils/status';
import { ActionButton } from './ActionButton';
import { StatusBadge } from './StatusBadge';

interface ScenarioValidationPanelProps {
  expectedChecks: string[];
  checks: ValidationCheck[];
  status: string;
  checkedAt?: string | null;
  runId?: string | null;
  loading: boolean;
  onValidate: () => void;
}

export function ScenarioValidationPanel({ expectedChecks, checks, status, checkedAt, runId, loading, onValidate }: ScenarioValidationPanelProps) {
  const byId = new Map(checks.map((check) => [check.id, check]));
  const ids = [...expectedChecks, ...checks.map((check) => check.id).filter((id) => !expectedChecks.includes(id))];
  const displayedChecks: ValidationCheck[] = ids.map((id) => byId.get(id) || { id, status: 'NOT_TESTED', detail: 'No evidence was recorded for this check in the latest completed validation.' });
  const passed = displayedChecks.filter((check) => check.status === 'PASS').length;
  const failed = displayedChecks.filter((check) => check.status === 'FAIL').length;
  const untested = displayedChecks.filter((check) => check.status === 'NOT_TESTED').length;
  const effectiveStatus = checks.length ? status : 'NOT_TESTED';

  return <div className="scenario-validation-overview">
    <div className="scenario-validation-summary"><div><span>{checks.length ? <CheckCircle2 size={17} /> : <Activity size={17} />}</span><div><strong>{passed}/{displayedChecks.length} checks passed</strong><small>{failed} failed · {untested} not tested</small></div></div><StatusBadge status={effectiveStatus} kind="validation" /></div>
    <div className="scenario-check-list">{displayedChecks.map((check) => <article key={check.id} className={check.status.toLowerCase()}><div><strong>{validationDescription(check.id)}</strong><code>{check.id}</code></div><StatusBadge status={check.status} kind="validation" /><p>{check.detail || 'No reason or evidence was reported by the validator.'}</p></article>)}</div>
    <div className="scenario-validation-footer"><span>{runId ? <>Evidence from <code>{runId}</code>{checkedAt ? ` · ${formatDate(checkedAt)}` : ''}</> : 'No completed validation run is available.'}</span><ActionButton variant="secondary" loading={loading} onClick={onValidate}>Run validation</ActionButton></div>
  </div>;
}
