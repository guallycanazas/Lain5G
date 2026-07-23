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
    variant: 'GUARDED VOLTE RF',
    profileTitle: '4G VoLTE preparation with X-Series radio',
    purpose: 'Prepare LTE over controlled RF with EPC and IMS before validating a physical UE and a VoLTE call.',
    includes: ['Open5GS EPC and IMS', 'srsRAN eNB with a compatible USRP', 'Preflight, auto-stop, and emergency stop'],
    excludes: ['Physical UE attach is not yet demonstrated', 'End-to-end SIP call and RTP are not validated'],
    hardware: 'Requires a compatible USRP, laboratory UE/SIM, isolation, and RF authorization.',
  },
  '5g-sa-x310': {
    generation: '5G',
    variant: 'GUARDED VONR RF',
    profileTitle: '5G VoNR preparation with X-Series radio',
    purpose: 'Prepare the 5G SA RF base before integrating IMS, registering a physical UE, and validating VoNR.',
    includes: ['Open5GS 5GC', 'srsRAN Project gNB with a compatible USRP', 'Preflight, auto-stop, and emergency stop'],
    excludes: ['IMS and SIP client are not yet integrated', 'VoNR call and RTP are not validated'],
    hardware: 'Requires a compatible USRP, 5G SA laboratory UE/SIM, isolation, and RF authorization.',
  },
  '5g-nsa-x310': {
    generation: '5G',
    variant: 'NSA EXPERIMENTAL',
    profileTitle: '5G NSA with LTE anchor and X-Series radio',
    purpose: 'Configure EN-DC with an LTE anchor and NR secondary carrier over two RF chains.',
    includes: ['Shared Open5GS EPC', 'srsENB EN-DC with LTE + NR', 'TX/RX, dual RF paths, preflight, and auto-stop'],
    excludes: ['Applying the profile does not start RF', 'Compatibility with every commercial UE is not guaranteed'],
    hardware: 'Requires a compatible USRP with two connected, attenuated, and authorized RF paths.',
  },
};

export function getScenarioGuidance(id: string) {
  return scenarioGuidance[id];
}
