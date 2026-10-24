import type { ValidationCheck } from '../types/validation';
import { diagnoseValidationCheck } from '../utils/validationDiagnosis';

export function ValidationDiagnosis({ check }: { check: ValidationCheck }) {
  const diagnosis = diagnoseValidationCheck(check);
  if (!diagnosis) return null;

  return <div className={`validation-diagnosis ${check.status.toLowerCase()}`}>
    <p><strong>Likely cause</strong>{diagnosis.cause}</p>
    <p><strong>Suggested fix</strong>{diagnosis.fix}</p>
    {check.detail ? <details><summary>Technical evidence</summary><code>{check.detail}</code></details> : null}
  </div>;
}
