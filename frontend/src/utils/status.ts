import type { DeploymentState } from '../types/deployment';
import type { ValidationState } from '../types/validation';

export function deploymentLabel(status: DeploymentState | string): string {
  const labels: Record<string, string> = {
    running: 'Running',
    stopped: 'Stopped',
    partial: 'Partial',
    error: 'Error',
    starting: 'Starting',
    validating: 'Validating',
    standby: 'Standby',
    unknown: 'Unknown',
    dry_run: 'Dry-run',
  };
  return labels[status] || status;
}

export function validationLabel(status: ValidationState | string): string {
  const labels: Record<string, string> = {
    PASS: 'PASS',
    PARTIAL: 'PARTIAL',
    FAIL: 'FAIL',
    WARNING: 'WARNING',
    NOT_TESTED: 'NOT TESTED',
    RUNNING: 'RUNNING',
  };
  return labels[status] || status;
}

export function validationDescription(id: string): string {
  const labels: Record<string, string> = {
    mongo: 'MongoDB available',
    nrf: 'NRF active',
    amf: 'AMF active',
    smf: 'SMF active',
    upf: 'UPF active',
    ausf: 'AUSF active',
    udm: 'UDM active',
    udr: 'UDR active',
    pcf: 'PCF active',
    ng_connection: 'NG connection established',
    ue_registration: 'UE registered',
    pdu_session: 'PDU session established',
    pdu_internet: 'Internet PDU session established',
    pdu_ims: 'IMS PDU session established',
    ue_tun: 'TUN interface created',
    ue_ip: 'IP address assigned',
    ue_internet_ip: 'Internet UE IP assigned',
    ue_ims_ip: 'IMS UE IP assigned',
    ue_internet_tun: 'Internet TUN interface created',
    ue_ims_tun: 'IMS TUN interface created',
    ping: 'Data ping successful',
    data_ping: 'Internet data ping successful',
    ng_setup: 'NG Setup completed',
    s1_setup: 'S1 Setup completed',
    ims: 'IMS services available',
    ims_services: 'Compact IMS infrastructure services active',
    ims_database: 'IMS database available',
    pcscf: 'P-CSCF active',
    icscf: 'I-CSCF active',
    scscf: 'S-CSCF active',
    ims_dns: 'IMS DNS resolved through IMS path',
    pcscf_reachable_over_ims: 'P-CSCF reachable through IMS tunnel',
    sip_register: 'SIP registration observed',
    ims_registration: 'Physical UE IMS registration',
    volte_call: 'VoLTE call dialog established',
    vonr_call: 'VoNR call dialog established',
    rtp_media: 'RTP media path exercised',
    hardware: 'SDR hardware detected',
    preflight: 'Preflight passed',
  };
  return labels[id] || id;
}

export function extractDetectedValue(detail?: string | null): string {
  if (!detail) return 'Unavailable';
  const ip = detail.match(/\b(?:\d{1,3}\.){3}\d{1,3}\b/);
  if (ip) return ip[0];
  if (/succeeded|successful|exists|assigned|responds|running/i.test(detail)) return 'Detected';
  return 'Unavailable';
}
