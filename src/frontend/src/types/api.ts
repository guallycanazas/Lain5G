export interface ApiErrorDetail {
  code?: string;
  message?: string;
  exit_code?: number | null;
  stderr?: string | null;
  active_scenario?: string | null;
}

export interface ApiErrorResponse {
  detail?: ApiErrorDetail | string;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}
