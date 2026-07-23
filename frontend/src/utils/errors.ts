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
