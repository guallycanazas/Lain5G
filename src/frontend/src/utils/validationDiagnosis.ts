import type { ValidationCheck } from '../types/validation';

export interface ValidationDiagnosis {
  cause: string;
  fix: string;
}

const checkGuidance: Record<string, ValidationDiagnosis> = {
  hardware_detected: { cause: 'The host could not confirm the SDR hardware.', fix: 'Check power, the X310 Ethernet/control connection, host IP configuration, and UHD device discovery.' },
  dual_rf_chains: { cause: 'The required two RF chains or daughterboards were not detected.', fix: 'Check that both daughterboards are installed and supported, then rerun Hardware check.' },
  ethernet_link: { cause: 'The host-to-radio Ethernet path is missing or on an unexpected subnet.', fix: 'Check the cable/NIC, configure the documented radio subnet, and verify that no competing route uses the X310 address.' },
  uhd_available: { cause: 'The selected RAN runtime could not use UHD or discover the radio.', fix: 'Use the UHD version required by this profile, confirm the UHD tools are available in its image, then rerun Hardware check.' },
  uhd_fpga_compatible: { cause: 'The FPGA image could not be confirmed compatible with the active UHD runtime.', fix: 'Check the FPGA compatibility report and install the image matching the UHD version used by this profile; then power-cycle the X310 if the image was changed.' },
  rfnoc_initialization: { cause: 'The SDR was detected, but the RAN process could not initialize its RFNoC radio graph.', fix: 'Compare the X310 FPGA/RFNoC compatibility with the exact UHD build in the selected RAN image, then check the X310 management Ethernet link and retry Hardware check before RF.' },
  epc_services: { cause: 'One or more required LTE core services are not running.', fix: 'Open the profile Logs, identify the first unhealthy EPC service, resolve its startup/configuration error, and start or validate the core again.' },
  core_services: { cause: 'One or more required 5G core services are not running.', fix: 'Open the profile Logs, identify the first unhealthy network function, resolve its startup/configuration error, and start or validate the core again.' },
  ims_services: { cause: 'One or more compact IMS services are unavailable.', fix: 'Check the IMS database and SIP service logs, verify service health and shared network connectivity, then rerun validation.' },
  mme_ready: { cause: 'The LTE MME is not ready.', fix: 'Check MME logs and its connection to MongoDB/HSS and the EPC network; fix the first startup error and restart the core.' },
  amf_ready: { cause: 'The 5G AMF is not ready.', fix: 'Check AMF logs and its connection to NRF, MongoDB, PLMN, TAC and slice configuration; fix the first startup error and restart the core.' },
  rf_preflight: { cause: 'One or more profile or RF safety requirements failed.', fix: 'Open the preflight artifact and correct each failed item (profile values, authorization, channel plan, RF paths, attenuation, or auto-stop) before starting RF.' },
  enb_started: { cause: 'The LTE eNB did not reach its started state.', fix: 'Open the session-scoped eNB log and resolve the first configuration, UHD, RFNoC, or core-connectivity error; then run Hardware check and Preflight again.' },
  gnb_started: { cause: 'The 5G gNB did not reach its started state.', fix: 'Open the session-scoped gNB log and resolve the first configuration, UHD/FPGA, RFNoC, or core-connectivity error; then run Hardware check and Preflight again.' },
  s1_setup: { cause: 'The LTE eNB did not establish its S1 control connection to the MME.', fix: 'Check that the MME is healthy and that the eNB and MME use matching PLMN/TAC and reachable bind addresses; inspect both session logs.' },
  ng_setup: { cause: 'The gNB did not establish NG Setup with the AMF.', fix: 'Check AMF health, PLMN/TAC/slice agreement, and gNB N2 bind/reachability; inspect the gNB and AMF logs.' },
  ue_registration: { cause: 'No successful UE registration was observed.', fix: 'Confirm the UE is attached to the intended cell and its IMSI/SUPI, Ki/OPc, PLMN and subscription profile match the core; inspect NAS/authentication logs.' },
  default_bearer: { cause: 'The LTE UE registered but did not establish its default data bearer.', fix: 'Check the subscriber APN, EPC APN/DNN mapping, PGW/UPF service health, and UE APN selection; inspect session-management logs.' },
  pdu_session: { cause: 'The UE registered but the requested 5G PDU session was not established.', fix: 'Check the subscriber DNN and S-NSSAI, SMF/UPF health, and that the UE requests a provisioned DNN/slice; inspect SMF and AMF logs.' },
  pdu_internet: { cause: 'The internet DNN PDU session was not established.', fix: 'Select the provisioned internet DNN for the subscriber and confirm matching SMF/UPF/APN configuration.' },
  pdu_ims: { cause: 'The IMS DNN PDU session was not established.', fix: 'Confirm the subscriber has the IMS DNN and matching slice/session policy, and that IMS routing is configured in the core.' },
  ue_ip: { cause: 'The UE did not receive an IP address.', fix: 'Check the APN/DNN address pool and gateway configuration, then inspect PGW/UPF and session-management logs.' },
  ue_tun: { cause: 'The UE tunnel interface was not created.', fix: 'Check that the UE session was accepted and that the host/container has the required TUN device permissions; inspect UE logs.' },
  ping: { cause: 'The user-plane connectivity probe failed.', fix: 'Check the UE IP/TUN state, UPF/PGW routes, NAT and firewall rules, and whether the target is reachable from the lab.' },
  data_ping: { cause: 'The LTE user-plane connectivity probe failed.', fix: 'Check bearer/IP assignment, SGi/PGW routing, NAT and firewall rules, then retry against a reachable target.' },
  ims_dns: { cause: 'The UE could not resolve the IMS domain through the configured path.', fix: 'Check the subscriber-provided DNS address, IMS DNS records and domain names, and DNS container logs.' },
  pcscf_reachable_over_ims: { cause: 'The P-CSCF could not be reached over the IMS data path.', fix: 'Check the IMS PDU/APN, P-CSCF address advertisement, routing and firewall rules between the UE and IMS network.' },
  sip_register: { cause: 'The UE did not complete SIP registration with the IMS.', fix: 'Check IMS connectivity and DNS, then confirm the IMS identity and authentication credentials match the HSS/pyHSS subscriber record; inspect SIP response codes in the IMS logs.' },
  virtual_call: { cause: 'The two synthetic SIP phones did not complete the IMS call check.', fix: 'Check the virtual phone identities, P-CSCF DNS and address, S-CSCF contact routing, and SIP/RTP connectivity. Inspect the Calls and messages panel and the validation log. The RTP payload is silence and does not verify UE media or audible speech.' },
  auto_stop: { cause: 'The guarded radio process did not complete its configured stop lifecycle.', fix: 'Check the session record and container timeout logs. If the process exited early, resolve its startup/runtime error; if it stayed active, stop it before another run.' },
  logs_captured: { cause: 'The validator could not save the logs needed to explain the run.', fix: 'Check Docker log access and the run directory permissions, then rerun validation.' },
  nr_secondary_cell: { cause: 'NR secondary-carrier tuning was not confirmed in the eNB session log.', fix: 'Check that the NSA eNB initialized RF successfully and that the NR carrier is configured on RF port 1; review the session log.' },
  mongo: { cause: 'MongoDB is unavailable to this profile.', fix: 'Check MongoDB container health and profile network membership, inspect MongoDB logs, then rerun validation.' },
  mme: { cause: 'The LTE MME service is unavailable.', fix: 'Check MME logs and its MongoDB/HSS and EPC network connections. Use the profile’s core-only repair, then validate again.' },
  hss: { cause: 'The LTE HSS service is unavailable.', fix: 'Check HSS logs, MongoDB connectivity and subscriber provisioning. Restart the profile core only if its images are ready, then validate again.' },
  nrf: { cause: 'The 5G NRF service is unavailable.', fix: 'Check NRF logs and MongoDB/core network health. Use the profile’s core-only repair, then validate again.' },
  amf: { cause: 'The 5G AMF service is unavailable.', fix: 'Check AMF logs and NRF registration, PLMN/TAC and network reachability. Use the profile’s core-only repair, then validate again.' },
  smf: { cause: 'The 5G SMF service is unavailable.', fix: 'Check SMF logs and its NRF, UPF and DNN configuration. Use the profile’s core-only repair, then validate again.' },
  upf: { cause: 'The user-plane function is unavailable.', fix: 'Check UPF logs, interface/address-pool configuration and core network membership. Use the profile’s core-only repair, then validate again.' },
  ausf: { cause: 'The 5G AUSF authentication function is unavailable.', fix: 'Check AUSF logs and its UDM/NRF connectivity, then use the profile’s core-only repair and validate again.' },
  udm: { cause: 'The 5G UDM subscriber-data function is unavailable.', fix: 'Check UDM logs, MongoDB connectivity and subscriber data, then use the profile’s core-only repair and validate again.' },
  udr: { cause: 'The 5G UDR data repository is unavailable.', fix: 'Check UDR logs and MongoDB/core network health, then use the profile’s core-only repair and validate again.' },
  pcf: { cause: 'The 5G PCF policy function is unavailable.', fix: 'Check PCF logs and its NRF connectivity and policy configuration, then use the profile’s core-only repair and validate again.' },
  sgwc: { cause: 'The LTE SGW control-plane service is unavailable.', fix: 'Check SGW-C logs and EPC network connectivity, then start the EPC/core without RF and validate again.' },
  sgwu: { cause: 'The LTE SGW user-plane service is unavailable.', fix: 'Check SGW-U logs, interfaces and EPC network connectivity, then start the EPC/core without RF and validate again.' },
  pgwc: { cause: 'The LTE PGW control-plane service is unavailable.', fix: 'Check PGW-C logs, APN configuration and its connection to the user plane, then start the EPC/core without RF and validate again.' },
  pgwu: { cause: 'The LTE PGW user-plane service is unavailable.', fix: 'Check PGW-U logs, address pools, routing and EPC network connectivity, then start the EPC/core without RF and validate again.' },
  pcrf: { cause: 'The LTE policy and charging service is unavailable.', fix: 'Check PCRF logs and its database/core connectivity, then start the EPC/core without RF and validate again.' },
  ims_database: { cause: 'The IMS database or provisioning step is unavailable.', fix: 'Check database health, provisioning logs and IMS service connectivity; then rerun validation.' },
  'ims-database': { cause: 'The IMS database service is unavailable.', fix: 'Check database health, provisioning logs and IMS service connectivity; then rerun validation.' },
  pcscf: { cause: 'The IMS P-CSCF service is unavailable.', fix: 'Check P-CSCF logs, advertised address and reachability from the UE IMS network, then validate again.' },
  icscf: { cause: 'The IMS I-CSCF service is unavailable.', fix: 'Check I-CSCF logs, DNS/SIP routing and connectivity to the subscriber database, then validate again.' },
  scscf: { cause: 'The IMS S-CSCF service is unavailable.', fix: 'Check S-CSCF logs, subscriber authentication and connectivity to the subscriber database, then validate again.' },
  dns: { cause: 'The profile DNS service is unavailable.', fix: 'Check DNS container health, IMS/APN records and profile network connectivity, then validate again.' },
  subscriber_mongo: { cause: 'MongoDB did not answer the subscriber request in time.', fix: 'Check MongoDB health, backend-to-database routing and container logs, then retry the subscriber operation. The timeout alone does not prove that a write failed.' },
};

const detailPatterns: Array<{ pattern: RegExp; diagnosis: ValidationDiagnosis }> = [
  { pattern: /RF web control is disabled by the local operator configuration/i, diagnosis: { cause: 'The operator has disabled RF control for this web application.', fix: 'An administrator must review the local operator configuration and explicitly enable RF control if this host is authorized. The Troubleshooter will not bypass this guard.' } },
  { pattern: /already active|already running|containers? (?:are )?active|container.*already exists/i, diagnosis: { cause: 'A previous profile session may have left services active, or the same core is shared with another profile.', fix: 'Sync the service inventory and inspect profile logs. Stop only the stale session through the profile controls; preserve shared core services used by another profile, then retry and validate.' } },
  { pattern: /(?:eNB|gNB) exited during UHD initialization|X310_RF_START_FAILED/i, diagnosis: { cause: 'The RAN process exited while initializing the X310 through UHD.', fix: 'Read the first UHD/RFNoC error in the session log. Check link, UHD/FPGA compatibility and RFNoC initialization, then rerun Hardware check and Preflight. Do not retry RF until those checks pass.' } },
  { pattern: /Timed out getting recv buff for management transaction|management transaction/i, diagnosis: { cause: 'The X310 management interface did not answer the UHD transaction in time.', fix: 'Check the host-to-X310 Ethernet link, NIC/subnet and competing routes; confirm UHD and FPGA protocol compatibility, then rerun Hardware check before any RF start.' } },
  { pattern: /mongo.*(timeout|not respond|unavailable)|database.*(timeout|unavailable)/i, diagnosis: { cause: 'MongoDB did not answer the request in time.', fix: 'Check MongoDB health and logs, confirm the application is using the correct Docker network/address, then retry.' } },
  { pattern: /timed out|timeout|did not respond/i, diagnosis: { cause: 'A required device or service did not respond before the timeout.', fix: 'Check that the device/service is reachable and healthy, inspect its logs, and retry after resolving the underlying delay.' } },
  { pattern: /RFNoC protocol mismatch|protocol mismatch.*(FPGA|RFNoC)/i, diagnosis: { cause: 'The UHD software and X310 FPGA use incompatible RFNoC protocol versions.', fix: 'Install an FPGA image compatible with the exact UHD version in the RAN runtime, then power-cycle and rerun Hardware check.' } },
  { pattern: /RFNOC::GRAPH|RfnocError|rfnoc_graph|Management operation failed|Incorrect number of operations/i, diagnosis: checkGuidance.rfnoc_initialization },
  { pattern: /UHD.*(not found|missing|unavailable)|uhd_usrp_probe.*(failed|not found)/i, diagnosis: checkGuidance.uhd_available },
  { pattern: /FPGA.*(incompat|unknown|mismatch)/i, diagnosis: checkGuidance.uhd_fpga_compatible },
  { pattern: /APN|DNN|default bearer|PDU session/i, diagnosis: { cause: 'The requested subscriber data session does not match the provisioned APN/DNN or session policy.', fix: 'Use a provisioned APN/DNN for the selected profile and verify the subscriber, core session policy, and address pool agree.' } },
  { pattern: /SIP.*(401|403|unauthori[sz]ed|forbidden)|REGISTER/i, diagnosis: { cause: 'IMS registration was rejected or did not reach the IMS registrar.', fix: 'Check UE-to-P-CSCF connectivity, IMS public/private identity, and authentication credentials against the subscriber database; inspect the SIP response in IMS logs.' } },
  { pattern: /connection refused|network is unreachable|no route to host/i, diagnosis: { cause: 'A required network endpoint is unreachable.', fix: 'Check service health, container networks, bind addresses, routes, and firewall rules for the endpoint named in the evidence.' } },
  { pattern: /image.*(missing|not found)|no such image/i, diagnosis: { cause: 'A required container image is not available locally.', fix: 'Open Preparation, build or pull the exact image required by this profile, then retry the action.' } },
];

export function diagnoseValidationCheck(check: ValidationCheck): ValidationDiagnosis | null {
  if (check.status === 'PASS') return null;
  const detail = check.detail || '';
  for (const item of detailPatterns) {
    if (item.pattern.test(detail)) return item.diagnosis;
  }
  const known = checkGuidance[check.id];
  if (known) return known;
  if (check.status === 'NOT_TESTED') {
    return {
      cause: detail || 'This check did not collect evidence in the latest validation.',
      fix: 'Complete the required profile step or provide the required external UE, then run validation again. Open Logs if the step ran but no evidence was recorded.',
    };
  }
  return {
    cause: detail || `The ${check.id} check did not meet its pass condition.`,
    fix: 'Open Logs for the selected profile, find the first related error, correct that configuration or service issue, and rerun validation. If it persists, share the run ID and relevant log excerpt.',
  };
}
