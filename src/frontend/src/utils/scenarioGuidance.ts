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
  '5g-vonr-sim': {
    generation: '5G',
    variant: 'VoNR SIMULATION',
    profileTitle: 'Simulated 5G with IMS voice signaling',
    purpose: 'Validate a 5G UE IMS PDU and SIP registration, plus a separate call between two synthetic SIP phones on the isolated IMS bridge.',
    includes: ['Open5GS 5GC and UERANSIM gNB/UE', 'Internet and IMS PDU sessions', 'SIP registration and virtual call/RTP checks'],
    excludes: ['USRP or RF transmission', 'Audible speech or a two-UE VoNR media path'],
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
  '4g-volte-sim': {
    generation: '4G',
    variant: 'VoLTE SIMULATION',
    profileTitle: 'Simulated LTE with IMS voice signaling',
    purpose: 'Validate LTE attach, IMS registration, and a separate call between two synthetic SIP phones on the isolated IMS bridge.',
    includes: ['Open5GS EPC and srsENB/srsUE over ZMQ', 'IMS services and authenticated SIP registration', 'Virtual call setup/teardown, silent RTP packets, and SIP MESSAGE delivery'],
    excludes: ['USRP or RF transmission', 'Audible speech or call media through the srsUE'],
    hardware: 'CPU, Docker, and /dev/net/tun only.',
  },
  '4g-lte-x310': {
    generation: '4G',
    variant: 'GUARDED LTE RF',
    profileTitle: '4G LTE with X-Series radio',
    purpose: 'Operate LTE over controlled RF with Open5GS EPC, compact IMS, and a guarded srsRAN eNB. Validation also checks a separate virtual SIP call on the IMS bridge.',
    includes: ['Open5GS EPC', 'Compact IMS and an isolated virtual SIP call check', 'srsRAN eNB with a compatible USRP', 'Preflight, auto-stop, and emergency stop'],
    excludes: ['Virtual call check uses SIP phones', 'RF start requires authorization', 'Validation evidence is saved per run'],
    hardware: 'Requires a compatible USRP, laboratory UE/SIM, isolation, and RF authorization.',
  },
  '5g-sa-x310': {
    generation: '5G',
    variant: 'GUARDED SA RF',
    profileTitle: '5G SA with X-Series radio',
    purpose: 'Operate a guarded 5G SA RF base with Open5GS and compact IMS. Validation can run an isolated virtual SIP call when the shared network is available.',
    includes: ['Open5GS 5GC', 'Compact IMS and an isolated virtual SIP call check', 'srsRAN Project gNB with a compatible USRP', 'Preflight, auto-stop, and emergency stop'],
    excludes: ['Virtual call check uses SIP phones', 'RF start requires authorization', 'Validation evidence is saved per run'],
    hardware: 'Requires a compatible USRP, 5G SA laboratory UE/SIM, isolation, and RF authorization.',
  },
  '5g-nsa-x310': {
    generation: '5G',
    variant: 'GUARDED NSA EN-DC RF',
    profileTitle: '5G NSA with X-Series radio',
    purpose: 'Operate a lab-validated LTE Band 7 anchor with an NR n3 secondary carrier using srsRAN EN-DC and the shared Open5GS EPC/IMS. Validation also checks an isolated virtual SIP call.',
    includes: ['Shared Open5GS EPC/IMS and virtual SIP call check', 'srsRAN eNB with LTE and NR RF chains', 'Hardware check, preflight, session auto-stop, and emergency stop'],
    excludes: ['A compatible EN-DC UE and matching LTE/NR band combination are required for attachment', 'RF transmission stays blocked until the NSA profile and both RF paths are authorized'],
    hardware: 'Requires an X-Series USRP with two compatible RF chains, a cabled or shielded lab, attenuated LTE and NR paths, an EN-DC UE/SIM, and authorization for both carriers.',
  },
};

export function getScenarioGuidance(id: string) {
  return scenarioGuidance[id];
}
