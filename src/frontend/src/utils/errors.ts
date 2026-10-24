import { ApiError } from '../types/api';

function isNetworkConflict(error: unknown) {
  return error instanceof ApiError && /pool overlaps|network conflict|address space/i.test(`${error.message} ${JSON.stringify(error.details)}`);
}

export function errorTitle(error: unknown): string {
  if (isNetworkConflict(error)) return 'Docker network conflict';
  if (error instanceof ApiError) {
    if (error.status === 0) return 'Backend unavailable';
    if (error.status === 409) return 'State conflict';
    if (error.status === 504) return 'Command timeout';
    if (error.status >= 500) return 'Backend error';
    return 'Invalid request';
  }
  if (error instanceof TypeError) return 'Backend unavailable';
  return 'Unexpected error';
}

export function errorMessage(error: unknown): string {
  if (isNetworkConflict(error)) return 'The subnet requested by this deployment overlaps with another Docker network.';
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) return 'Could not connect to the API.';
  if (error instanceof Error) return error.message;
  return 'The operation could not be completed.';
}

export function technicalDetails(error: unknown): string {
  if (error instanceof ApiError) return JSON.stringify({ status: error.status, code: error.code, details: error.details }, null, 2);
  if (error instanceof Error) return error.stack || error.message;
  return JSON.stringify(error, null, 2);
}

export interface ErrorDiagnosis {
  cause: string;
  fix: string;
}

export function diagnoseApplicationError(error: unknown): ErrorDiagnosis {
  const message = errorMessage(error);
  const code = error instanceof ApiError ? error.code || '' : '';
  const details = error instanceof ApiError ? JSON.stringify(error.details || '') : '';
  const evidence = `${code} ${message} ${details}`;

  if (code === 'DEPLOYMENT_CONFLICT') {
    const activeScenario = error instanceof ApiError && error.details && typeof error.details === 'object'
      ? (error.details as { active_scenario?: unknown }).active_scenario
      : null;
    return {
      cause: typeof activeScenario === 'string' ? `${activeScenario} is still active, and only one laboratory scenario can run at a time.` : 'Another laboratory scenario is still active, and only one scenario can run at a time.',
      fix: 'Stop the active profile before starting another one. The profile workspace can stop it and continue the requested start after confirmation.',
    };
  }
  if (/X310_RFNOC_INIT_FAILED|RFNOC::GRAPH|RfnocError|RFNoC protocol mismatch|rfnoc_graph|Management operation failed|Incorrect number of operations/i.test(evidence)) {
    return { cause: 'The X310 was detected, but the RAN could not initialize its UHD/RFNoC radio graph.', fix: 'Check that the X310 FPGA image matches the exact UHD version in the selected RAN image, then verify the X310 management Ethernet path and run Hardware check before retrying.' };
  }
  if (/RF web control is disabled/i.test(evidence)) {
    return { cause: 'The local operator has disabled RF start actions from the web interface.', fix: 'Use the approved local RF start procedure or ask the system operator to enable web RF control in the local application configuration.' };
  }
  if (/SUBSCRIBER_MONGO_TIMEOUT|MongoDB.*(timeout|did not respond|unavailable)/i.test(evidence)) {
    return { cause: 'MongoDB did not answer the subscriber request before the timeout.', fix: 'Check MongoDB health and logs, confirm the backend is on the correct Docker network, then retry the operation.' };
  }
  if (/pool overlaps|network conflict|address space/i.test(evidence)) {
    return { cause: 'The requested Docker subnet overlaps with another configured network.', fix: 'Choose a subnet that does not overlap with existing Docker or host networks, then apply the configuration again.' };
  }
  if (/X310_RF_START_FAILED|X310_RF_START|guarded RF session could not be started/i.test(evidence)) {
    return { cause: 'The guarded radio process did not start; the underlying reason is in the command output.', fix: 'Open the profile Logs and latest run evidence, resolve the first RAN/UHD/core error, then rerun Hardware check and Preflight before another RF attempt.' };
  }
  if (/X310_CORE_START_FAILED|core could not be started/i.test(evidence)) {
    return { cause: 'One or more required core services failed to start.', fix: 'Open Logs for the selected profile, identify the first unhealthy service, correct its configuration or image issue, then start the core again.' };
  }
  if (/timeout|timed out|504/i.test(evidence)) {
    return { cause: 'The operation took longer than the configured response timeout.', fix: 'Check the relevant service logs and system load; confirm dependencies are healthy, then retry. For a persistent timeout, review the operation timeout setting.' };
  }
  if (/connection refused|network is unreachable|no route to host|ECONNREFUSED|Backend unavailable/i.test(evidence)) {
    return { cause: 'The application could not reach the required backend or service endpoint.', fix: 'Check that the backend and dependency containers are running, then verify the configured host, port, Docker network and firewall rules.' };
  }
  if (/image.*(missing|not found)|no such image/i.test(evidence)) {
    return { cause: 'A required container image is unavailable locally.', fix: 'Open Preparation and build or pull the image required by this profile, then retry.' };
  }
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return { cause: 'The request was rejected because a required value, state or operator setting did not meet the API requirements.', fix: 'Review the form and current profile state. Read the message above for the rejected condition, correct it, and submit again.' };
  }
  return { cause: message, fix: 'Open Logs for the selected profile and inspect the first related error. Correct that configuration or service issue, then retry. If it persists, share the run ID and relevant log excerpt.' };
}
