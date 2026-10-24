import { describe, expect, it } from 'vitest';
import { diagnoseValidationCheck } from '../src/utils/validationDiagnosis';

describe('diagnoseValidationCheck', () => {
  it('explains RFNoC failures with a concrete next step', () => {
    const diagnosis = diagnoseValidationCheck({
      id: 'rfnoc_initialization',
      status: 'FAIL',
      detail: 'UHD could not initialize the RFNoC graph; Incorrect number of operations',
    });

    expect(diagnosis?.cause).toMatch(/RFNoC radio graph/);
    expect(diagnosis?.fix).toMatch(/FPGA\/RFNoC compatibility/);
  });

  it('uses evidence patterns to diagnose MongoDB timeouts on any profile', () => {
    const diagnosis = diagnoseValidationCheck({
      id: 'subscriber_mongo',
      status: 'FAIL',
      detail: 'MongoDB did not respond before timeout',
    });

    expect(diagnosis?.cause).toMatch(/MongoDB/);
    expect(diagnosis?.fix).toMatch(/Docker network/);
  });

  it.each([
    {
      id: 'rfnoc_initialization',
      detail: 'ERROR: Timed out getting recv buff for management transaction',
      cause: /X310 management interface/,
      fix: /Ethernet link.*UHD and FPGA protocol compatibility/,
    },
    {
      id: 'gnb_started',
      detail: '5G - Guarded SA RF guarded RF session could not be started; gNB exited during UHD initialization',
      cause: /RAN process exited while initializing the X310/,
      fix: /first UHD\/RFNoC error in the session log/,
    },
    {
      id: 'rf_preflight',
      detail: 'RF web control is disabled by the local operator configuration',
      cause: /operator has disabled RF control/,
      fix: /will not bypass this guard/,
    },
    {
      id: 'epc_services',
      detail: 'Containers are already active from the previous experiment',
      cause: /previous profile session may have left services active/,
      fix: /preserve shared core services/,
    },
    {
      id: 'sip_register',
      detail: 'SIP REGISTER rejected with 401 Unauthorized',
      cause: /IMS registration was rejected/,
      fix: /authentication credentials against the subscriber database/,
    },
    {
      id: 'pdu_session',
      detail: 'UE requested DNN internet but the session was rejected',
      cause: /requested subscriber data session does not match/,
      fix: /provisioned APN\/DNN/,
    },
  ])('diagnoses observed or likely failure $id without claiming an unsafe automatic repair', ({ id, detail, cause, fix }) => {
    const diagnosis = diagnoseValidationCheck({ id, status: 'FAIL', detail });

    expect(diagnosis?.cause).toMatch(cause);
    expect(diagnosis?.fix).toMatch(fix);
  });

  it.each(['mongo', 'mme', 'hss', 'sgwc', 'sgwu', 'pgwc', 'pgwu', 'pcrf', 'nrf', 'amf', 'smf', 'upf', 'ausf', 'udm', 'udr', 'pcf', 'ims-database', 'pcscf', 'icscf', 'scscf', 'dns'])('has a targeted explanation for recoverable service check %s', (id) => {
    const diagnosis = diagnoseValidationCheck({ id, status: 'FAIL', detail: '' });

    expect(diagnosis?.cause).not.toContain(`The ${id} check did not meet its pass condition`);
    expect(diagnosis?.fix).toBeTruthy();
  });

  it('does not show a failure diagnosis for passing checks', () => {
    expect(diagnoseValidationCheck({ id: 'ue_registration', status: 'PASS', detail: 'registered' })).toBeNull();
  });

  it('gives unknown failures a useful fallback and keeps raw evidence in the UI', () => {
    const diagnosis = diagnoseValidationCheck({ id: 'future_check', status: 'FAIL', detail: 'unexpected response 503' });

    expect(diagnosis?.cause).toContain('unexpected response 503');
    expect(diagnosis?.fix).toMatch(/Open Logs/);
  });
});
