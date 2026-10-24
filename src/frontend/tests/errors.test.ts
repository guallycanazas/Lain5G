import { describe, expect, it } from 'vitest';
import { ApiError } from '../src/types/api';
import { diagnoseApplicationError } from '../src/utils/errors';

describe('diagnoseApplicationError', () => {
  it('explains a detected X310 with RFNoC initialization failure', () => {
    const diagnosis = diagnoseApplicationError(new ApiError('NSA RF failed', 500, 'X310_RFNOC_INIT_FAILED'));
    expect(diagnosis.cause).toMatch(/RFNoC radio graph/);
    expect(diagnosis.fix).toMatch(/FPGA image/);
  });

  it('explains local RF web-control restrictions', () => {
    const diagnosis = diagnoseApplicationError(new ApiError('RF web control is disabled by the local operator configuration', 400, 'BAD_REQUEST'));
    expect(diagnosis.cause).toMatch(/local operator/);
    expect(diagnosis.fix).toMatch(/local RF start procedure/);
  });

  it('provides useful generic guidance for unknown API failures', () => {
    const diagnosis = diagnoseApplicationError(new ApiError('Unexpected storage error', 500, 'STORAGE_ERROR'));
    expect(diagnosis.cause).toBe('Unexpected storage error');
    expect(diagnosis.fix).toMatch(/Open Logs/);
  });
});
