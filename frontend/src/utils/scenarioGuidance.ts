export interface ScenarioGuidance {
  generation: '4G' | '5G';
  variant: string;
  profileTitle: string;
  purpose: string;
  includes: string[];
  excludes: string[];
  hardware: string;
}

export const scenarioGuidance: Record<string, ScenarioGuidance> = {
  '5g-sa': {
    generation: '5G',
    variant: 'SIMULATION',
    profileTitle: 'Simulated 5G with UERANSIM',
    purpose: 'Learn and validate 5G SA registration, a PDU session, and data connectivity without real radio hardware.',
    includes: ['Open5GS 5GC', 'UERANSIM gNB and UE', 'Internet DNN and UE tunnel'],
    excludes: ['USRP or RF transmission', 'IMS, SIP, and VoNR calls'],
    hardware: 'CPU, Docker, and /dev/net/tun only.',
  },
  '4g-lte-sim': {
    generation: '4G',
    variant: 'SIMULATION',
    profileTitle: 'Simulated 4G with srsENB + srsUE',
    purpose: 'Validate LTE attach, bearer, and data checks over virtual ZMQ radio without IMS or SDR hardware.',
    includes: ['Open5GS EPC', 'srsENB and srsUE over ZMQ', 'Internet APN and UE tunnel'],
    excludes: ['USRP or RF transmission', 'IMS, SIP, and VoLTE calls'],
    hardware: 'CPU, Docker, and /dev/net/tun only.',
  },
  '4g-lte-x310': {
    generation: '4G',
    variant: 'GUARDED LTE RF',
    profileTitle: '4G LTE with X-Series radio',
    purpose: 'Operate LTE over controlled RF with an Open5GS EPC and a guarded srsRAN eNB.',
    includes: ['Open5GS EPC', 'srsRAN eNB with a compatible USRP', 'Preflight, auto-stop, and emergency stop'],
    excludes: ['Physical UE attach is not yet demonstrated', 'No voice-call claim is made'],
    hardware: 'Requires a compatible USRP, laboratory UE/SIM, isolation, and RF authorization.',
  },
  '5g-sa-x310': {
    generation: '5G',
    variant: 'GUARDED SA RF',
    profileTitle: '5G SA with X-Series radio',
    purpose: 'Operate a guarded 5G SA RF base with Open5GS and srsRAN Project.',
    includes: ['Open5GS 5GC', 'srsRAN Project gNB with a compatible USRP', 'Preflight, auto-stop, and emergency stop'],
    excludes: ['Physical UE registration is not yet demonstrated', 'No voice-call claim is made'],
    hardware: 'Requires a compatible USRP, 5G SA laboratory UE/SIM, isolation, and RF authorization.',
  },
};

export function getScenarioGuidance(id: string) {
  return scenarioGuidance[id];
}
