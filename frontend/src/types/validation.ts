export type ValidationState = 'PASS' | 'PARTIAL' | 'FAIL' | 'WARNING' | 'NOT_TESTED' | 'RUNNING';

export interface ValidationCheck {
  id: string;
  status: ValidationState;
  detail: string | null;
}

export interface ValidationReport {
  run_id: string | null;
  scenario: string;
  status: ValidationState;
  validation: Record<string, ValidationState>;
  checks: ValidationCheck[];
  checked_at: string | null;
}
