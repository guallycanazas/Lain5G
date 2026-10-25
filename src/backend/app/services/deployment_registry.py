from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DeploymentDefinition:
    id: str
    name: str
    description: str
    deployment_path: str
    mode: str
    supported_actions: list[str]
    validation_checks: list[str]
    rf_capable: bool = False
    expected_services: list[str] = field(default_factory=list)
    log_services: list[str] = field(default_factory=list)
    scripts_path: str | None = None
    core_start_script: str | None = None
    rf_start_script: str | None = None
    rf_guard_variable: str | None = None
    rf_service: str | None = None
    catalog_visible: bool = True

    @property
    def scripts_dir(self) -> str:
        return self.scripts_path or f"{self.deployment_path}/scripts"


COMMON_5G_CHECKS = ["ng_setup", "ue_registration", "pdu_session", "ue_ip", "ue_tun", "ping"]

DEPLOYMENTS: dict[str, DeploymentDefinition] = {
    "5g-sa": DeploymentDefinition(
        id="5g-sa",
        name="5G - UERANSIM Simulation",
        description="Software-only 5G SA with Open5GS and UERANSIM gNB/UE, including a data PDU session; VoNR is not included.",
        deployment_path="deployments/5g-sa",
        mode="simulation",
        supported_actions=["start", "stop", "restart", "status", "logs", "validate"],
        validation_checks=COMMON_5G_CHECKS,
        expected_services=["mongo", "nrf", "amf", "smf", "upf", "ausf", "udm", "udr", "pcf", "gnb", "ue"],
        log_services=["mongo", "nrf", "amf", "smf", "upf", "ausf", "udm", "udr", "pcf", "gnb", "ue"],
    ),
    "4g-volte-sim": DeploymentDefinition(
        id="4g-volte-sim",
        name="4G LTE + VoLTE Signaling",
        description="srsRAN 4G ZMQ LTE, Open5GS EPC, and lab IMS with virtual SIP phones for call, RTP, and MESSAGE checks.",
        deployment_path="deployments/4g-volte/sim",
        mode="simulation",
        supported_actions=["start", "stop", "restart", "status", "logs", "validate"],
        validation_checks=["s1_setup", "ue_registration", "default_bearer", "ue_ip", "ue_tun", "data_ping", "ims_dns", "sip_register", "virtual_phones"],
        expected_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf", "enb", "ue", "pcscf", "icscf", "scscf", "dns"],
        log_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf", "enb", "ue", "pcscf", "icscf", "scscf", "dns", "sip-register"],
        catalog_visible=True,
    ),
    "4g-lte-sim": DeploymentDefinition(
        id="4g-lte-sim",
        name="4G - srsRAN ZMQ Simulation",
        description="Software-only LTE with Open5GS EPC, srsENB, and srsUE over ZMQ; IMS and VoLTE are not included.",
        deployment_path="deployments/4g-lte-sim",
        mode="simulation",
        supported_actions=["start", "stop", "restart", "status", "logs", "validate"],
        validation_checks=["s1_setup", "ue_registration", "default_bearer", "ue_ip", "ue_tun", "data_ping"],
        expected_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf", "enb", "ue"],
        log_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf", "enb", "ue"],
    ),
    "5g-vonr-sim": DeploymentDefinition(
        id="5g-vonr-sim",
        name="5G SA + VoNR Signaling",
        description="5G SA simulation with internet and IMS PDU sessions, authenticated SIP registration over the UE IMS path, and a separate virtual SIP call/RTP check on the isolated IMS bridge.",
        deployment_path="deployments/5g-vonr",
        mode="simulation",
        supported_actions=["start", "stop", "restart", "status", "logs", "validate"],
        validation_checks=["mongo", "nrf", "amf", "smf", "upf", "ausf", "udm", "udr", "pcf", "ng_setup", "ue_registration", "pdu_internet", "pdu_ims", "ue_internet_ip", "ue_ims_ip", "ue_internet_tun", "ue_ims_tun", "data_ping", "ims_database", "pcscf", "icscf", "scscf", "ims_dns", "pcscf_reachable_over_ims", "sip_register", "virtual_call"],
        expected_services=["mongo", "nrf", "amf", "smf", "upf", "ausf", "udm", "udr", "pcf", "gnb", "ue", "ims-database", "pcscf", "icscf", "scscf", "dns"],
        log_services=["mongo", "nrf", "amf", "smf", "upf", "ausf", "udm", "udr", "pcf", "gnb", "ue", "ims-database", "pcscf", "icscf", "scscf", "dns", "sip-register"],
        catalog_visible=True,
    ),
    "4g-lte-x310": DeploymentDefinition(
        id="4g-lte-x310",
        name="4G - Guarded LTE RF",
        description="Controlled LTE RF with Open5GS EPC, compact IMS, an isolated virtual SIP call check, srsRAN eNB, and compatible USRP hardware.",
        deployment_path="deployments/4g-volte/x310",
        mode="rf-controlled",
        supported_actions=["stop", "status", "logs", "validate", "hardware-check", "preflight", "start-core", "start-epc", "start-rf", "emergency-stop"],
        validation_checks=["hardware_detected", "ethernet_link", "uhd_available", "uhd_fpga_compatible", "epc_services", "mme_ready", "ims_services", "virtual_call", "rf_preflight", "enb_started", "s1_setup", "auto_stop", "logs_captured"],
        rf_capable=True,
        expected_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf", "ims-database", "pcscf", "icscf", "scscf", "dns", "enb-x310"],
        log_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf", "ims-database", "ims-provisioner", "pcscf", "icscf", "scscf", "dns", "virtual-phones", "enb-x310"],
        core_start_script="start-epc",
        rf_start_script="start-enb",
        rf_guard_variable="LAIN5G_ALLOW_RF_START",
        rf_service="enb-x310",
    ),
    "5g-sa-x310": DeploymentDefinition(
        id="5g-sa-x310",
        name="5G - Guarded SA RF",
        description="Controlled 5G SA RF with Open5GS, compact IMS, an isolated virtual SIP call check, srsRAN Project gNB, and compatible USRP hardware.",
        deployment_path="deployments/5g-sa-x310",
        mode="rf-controlled",
        supported_actions=["stop", "status", "logs", "validate", "hardware-check", "preflight", "start-core", "start-rf", "emergency-stop"],
        validation_checks=["hardware_detected", "uhd_available", "core_services", "amf_ready", "ims_services", "virtual_call", "rf_preflight", "gnb_started", "ng_setup", "auto_stop", "logs_captured"],
        rf_capable=True,
        expected_services=["mongo", "nrf", "ausf", "udm", "udr", "pcf", "upf", "smf", "amf", "ims-database", "pcscf", "icscf", "scscf", "dns", "gnb-x310"],
        log_services=["mongo", "nrf", "ausf", "udm", "udr", "pcf", "upf", "smf", "amf", "ims-database", "ims-provisioner", "pcscf", "icscf", "scscf", "dns", "virtual-phones", "gnb-x310"],
        core_start_script="start-core",
        rf_start_script="start-gnb",
        rf_guard_variable="LAIN5G_ALLOW_5G_RF_START",
        rf_service="gnb-x310",
    ),
    "5g-nsa-x310": DeploymentDefinition(
        id="5g-nsa-x310",
        name="5G NSA - Guarded EN-DC RF",
        description="Lab-validated LTE anchor plus 5G NR secondary carrier over a guarded X-Series radio and shared Open5GS EPC/IMS, with an isolated virtual SIP call check.",
        deployment_path="deployments/5g-nsa-x310",
        mode="rf-controlled",
        supported_actions=["stop", "status", "logs", "validate", "hardware-check", "preflight", "start-core", "start-rf", "emergency-stop"],
        validation_checks=["hardware_detected", "dual_rf_chains", "epc_services", "ims_services", "virtual_call", "rf_preflight", "rfnoc_initialization", "enb_started", "s1_setup", "nr_secondary_cell", "ue_registration", "auto_stop", "logs_captured"],
        rf_capable=True,
        expected_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "ims-database", "pcscf", "icscf", "scscf", "dns", "enb-nsa-x310"],
        log_services=["mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "ims-database", "ims-provisioner", "pcscf", "icscf", "scscf", "dns", "virtual-phones", "enb-nsa-x310"],
        core_start_script="start-core",
        rf_start_script="start-rf",
        rf_guard_variable="LAIN5G_ALLOW_5G_NSA_RF_START",
        rf_service="enb-nsa-x310",
    ),
}


def get_deployment_definition(scenario: str) -> DeploymentDefinition | None:
    return DEPLOYMENTS.get(scenario)


def list_deployment_definitions() -> list[DeploymentDefinition]:
    return list(DEPLOYMENTS.values())


def list_catalog_deployment_definitions() -> list[DeploymentDefinition]:
    return [definition for definition in DEPLOYMENTS.values() if definition.catalog_visible]
