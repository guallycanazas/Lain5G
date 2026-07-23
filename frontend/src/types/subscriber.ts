export type SubscriberConnectionState = 'connected' | 'disconnected' | 'timeout' | 'misconfigured' | 'error' | 'dry_run';

export interface SubscriberConnectionStatus {
  status: SubscriberConnectionState;
  database: string;
  collection: string;
  server: string;
  latency_ms: number | null;
  checked_at: string;
  message?: string | null;
}

export interface SubscriberSecurityRedacted {
  k_configured: boolean;
  op_configured: boolean;
  opc_configured: boolean;
  amf?: string | null;
  sqn?: string | null;
}

export interface SubscriberSummary {
  imsi: string;
  msisdn?: string | null;
  dnn?: string | null;
  sst?: number | null;
  sd?: string | null;
  security: SubscriberSecurityRedacted;
}

export interface SubscriberDetail extends SubscriberSummary {
  checked_at: string;
  note: string;
}

export interface SubscriberListResponse {
  items: SubscriberSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface SubscriberFormPayload {
  imsi?: string;
  msisdn?: string | null;
  security?: {
    k?: string | null;
    op?: string | null;
    opc?: string | null;
    amf?: string | null;
    sqn?: string | null;
  };
  slice?: {
    sst?: number;
    sd?: string | null;
  };
  dnn?: string;
}

export interface SubscriberClonePayload {
  new_imsi: string;
  new_msisdn?: string | null;
}

export interface SubscriberValidationResult {
  valid: boolean;
  errors: string[];
}

export interface SubscriberOperationResponse {
  subscriber?: SubscriberDetail | null;
  dry_run: boolean;
  persisted: boolean;
  message: string;
}
