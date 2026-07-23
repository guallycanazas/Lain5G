export type RealImsMode = '4g' | '5g';

export interface RealImsCheck {
  id: string;
  status: string;
  message: string;
  evidence: unknown;
}

export interface RealImsReport {
  mode: RealImsMode;
  status: string;
  checks: RealImsCheck[];
}

export interface RealImsSubscriber {
  imsi: string;
  msisdn: string;
  impi: string;
  impu: string;
  domain: string;
  scscf: string | null;
  enabled: boolean;
  apns: string[];
  open5gs_present: boolean;
  pyhss_present: boolean;
}

export interface RealImsSubscriberList {
  mode: RealImsMode;
  count: number;
  subscribers: RealImsSubscriber[];
  secrets_redacted: true;
}

export interface RealImsActionResponse {
  status?: string;
  message?: string;
  execute?: boolean;
  [key: string]: unknown;
}

export interface RealImsStartPayload {
  mode: RealImsMode;
  execute: boolean;
  mcc: string;
  mnc: string;
}

export interface RealImsStopPayload {
  mode: RealImsMode;
  execute: boolean;
}

export interface RealImsProvisionPayload {
  mode: RealImsMode;
  execute: boolean;
  mcc: string;
  mnc: string;
  imsi: string;
  msisdn: string;
  ki: string;
  opc: string;
  amf: string;
  sqn: string;
  apn_internet: string;
  apn_ims: string;
  enabled: boolean;
}
