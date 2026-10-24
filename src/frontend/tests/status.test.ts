import { describe, expect, it } from 'vitest';
import { aggregateValidationStatus } from '../src/utils/status';
import type { ValidationCheck } from '../src/types/validation';

describe('aggregateValidationStatus', () => {
  it('reports partial when checks pass but UE registration is untested', () => {
    const checks: ValidationCheck[] = [
      { id: 'enb_started', status: 'PASS', detail: null },
      { id: 'ue_registration', status: 'NOT_TESTED', detail: null },
    ];

    expect(aggregateValidationStatus(checks)).toBe('PARTIAL');
  });

  it('keeps a failed check higher priority than partial evidence', () => {
    const checks: ValidationCheck[] = [
      { id: 's1_setup', status: 'FAIL', detail: null },
      { id: 'ue_registration', status: 'NOT_TESTED', detail: null },
    ];

    expect(aggregateValidationStatus(checks)).toBe('FAIL');
  });
});
