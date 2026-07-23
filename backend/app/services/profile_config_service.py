from __future__ import annotations

import difflib
import math
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ProfileConfigError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PlannedChange:
    path: Path
    before: str
    after: str


class ProfileConfigService:
    PROFILE_IDS = {"4g-lte-sim", "4g-volte-sim", "4g-lte-x310", "5g-sa", "5g-sa-x310", "5g-nsa-x310", "5g-vonr"}
    CATALOG_PROFILE_IDS = {"4g-lte-sim", "4g-lte-x310", "5g-sa", "5g-sa-x310", "5g-nsa-x310"}
    SECRET_KEYS = {"SUBSCRIBER_KEY", "SUBSCRIBER_OPC", "SUBSCRIBER_SQN", "IMS_AUTH_PASSWORD", "K", "KI", "OPC"}
    LTE_BAND_EARFCN_RANGES = {7: range(2750, 3450)}
    SRSRAN_4G_N_PRB_BY_BANDWIDTH = {1.4: 6, 3.0: 15, 5.0: 25, 10.0: 50, 15.0: 75, 20.0: 100}
    NETWORK_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,61}[A-Za-z0-9])?$")
    COMPONENT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

    def __init__(self, settings: Any):
        self.settings = settings
        self.root = settings.project_root.resolve()
        self.profiles_dir = self._confined(self.root / "config" / "profiles")
        self.backups_dir = self._confined(self.root / ".backups" / "config")

    def list_profiles(self) -> list[dict[str, Any]]:
        return [self._summary(self.get_profile(profile_id)) for profile_id in sorted(self.CATALOG_PROFILE_IDS)]

    def get_profile(self, profile_id: str) -> dict[str, Any]:
        self._assert_profile(profile_id)
        path = self._profile_path(profile_id)
        if not path.exists():
            raise ProfileConfigError(404, "PROFILE_NOT_FOUND", f"Profile {profile_id} was not found.")
        data = _loads_yaml(path.read_text(encoding="utf-8"))
        if data.get("profile") != profile_id:
            raise ProfileConfigError(422, "PROFILE_INVALID", f"Profile file {path} has an invalid profile id.")
        return data

    def update_profile(self, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.get_profile(profile_id)
        unknown = _unknown_paths(current, payload)
        if unknown:
            raise ProfileConfigError(422, "PROFILE_VALIDATION_FAILED", f"Unknown profile fields: {', '.join(unknown)}")
        merged = _deep_merge(current, payload)
        merged["profile"] = profile_id
        errors = self._validate_shape(merged)
        if errors:
            raise ProfileConfigError(422, "PROFILE_VALIDATION_FAILED", "; ".join(errors))
        self._profile_path(profile_id).write_text(_dumps_yaml(merged), encoding="utf-8")
        return self.get_profile(profile_id)

    def validate_profile(self, profile_id: str) -> dict[str, Any]:
        profile = self.get_profile(profile_id)
        errors = self._validate_shape(profile) + self._validate_consistency(profile)
        if profile.get("radio"):
            errors.extend(self._validate_rf_readiness(profile))
            errors.extend(self._validate_rf_safety(profile))
        return {"profile": profile_id, "valid": not errors, "errors": errors}

    def diff_profile(self, profile_id: str) -> dict[str, Any]:
        profile = self.get_profile(profile_id)
        changes = self._planned_changes(profile)
        return {"profile": profile_id, "files": [self._change_payload(change) for change in changes]}

    def apply_profile(self, profile_id: str) -> dict[str, Any]:
        validation = self.validate_profile(profile_id)
        if not validation["valid"]:
            raise ProfileConfigError(422, "PROFILE_VALIDATION_FAILED", "; ".join(validation["errors"]))
        profile = self.get_profile(profile_id)
        changes = self._planned_changes(profile)
        backup_dir = self._backup(profile_id, changes)
        for change in changes:
            change.path.parent.mkdir(parents=True, exist_ok=True)
            change.path.write_text(change.after, encoding="utf-8")
        return {"profile": profile_id, "modified_files": [self._rel(change.path) for change in changes if change.before != change.after], "backup": self._rel(backup_dir)}

    def restore_profile(self, profile_id: str) -> dict[str, Any]:
        self._assert_profile(profile_id)
        profile_backup_dir = self._confined(self.backups_dir / profile_id)
        backups = sorted([p for p in profile_backup_dir.glob("*") if p.is_dir()])
        if not backups:
            raise ProfileConfigError(404, "PROFILE_BACKUP_NOT_FOUND", f"No backups found for {profile_id}.")
        latest = self._confined(backups[-1])
        restored: list[str] = []
        for source in latest.rglob("*"):
            if not source.is_file():
                continue
            resolved_source = self._confined(source)
            if resolved_source != latest and latest not in resolved_source.parents:
                raise ProfileConfigError(400, "PROFILE_PATH_INVALID", "Backup contains a path outside its directory.")
            rel = source.relative_to(latest)
            target = self._confined(self.root / rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolved_source, target)
            restored.append(str(rel))
        return {"profile": profile_id, "restored_files": restored, "backup": self._rel(latest)}

    def _summary(self, profile: dict[str, Any]) -> dict[str, Any]:
        return {"profile": profile["profile"], "rf_capable": bool(profile.get("radio")), "rf_allowed": bool(profile.get("safety", {}).get("rf_allowed"))}

    def _assert_profile(self, profile_id: str) -> None:
        if profile_id not in self.PROFILE_IDS:
            raise ProfileConfigError(404, "PROFILE_NOT_FOUND", f"Unknown profile: {profile_id}")

    def _profile_path(self, profile_id: str) -> Path:
        return self._confined(self.profiles_dir / f"{profile_id}.yaml")

    def _rel(self, path: Path) -> str:
        return str(self._confined(path).relative_to(self.root))

    def _confined(self, path: Path) -> Path:
        resolved = path.resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise ProfileConfigError(400, "PROFILE_PATH_INVALID", "Profile path is outside the project root.")
        return resolved

    def _validate_shape(self, profile: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for path, value in _string_values(profile):
            if any(character in value for character in ("\x00", "\r", "\n")):
                errors.append(f"{path} contains unsupported control characters")
        network = profile.get("network", {})
        mcc = str(network.get("mcc", ""))
        mnc = str(network.get("mnc", ""))
        if not re.fullmatch(r"\d{3}", mcc):
            errors.append("MCC must contain exactly 3 digits")
        if not re.fullmatch(r"\d{2,3}", mnc):
            errors.append("MNC must contain 2 or 3 digits")
        if not _is_int(network.get("tac"), 1, 16777215):
            errors.append("TAC must be a positive integer")
        for key in ("dnn", "dnn_internet", "dnn_ims", "apn_internet", "apn_ims"):
            if key in network and not self.NETWORK_NAME_RE.fullmatch(str(network.get(key) or "")):
                errors.append(f"{key} must be a safe network name")
        slice_cfg = network.get("slice") or {}
        if slice_cfg:
            if not _is_int(slice_cfg.get("sst"), 1, 255):
                errors.append("SST must be 1..255")
            if not re.fullmatch(r"[0-9A-Fa-f]{6}", str(slice_cfg.get("sd", ""))):
                errors.append("SD must be 6 hexadecimal characters")
        for section in ("core", "ran", "radio"):
            for key, value in (profile.get(section) or {}).items():
                if key.endswith("addr") and value not in (None, "") and not _is_ip(str(value)):
                    errors.append(f"{section}.{key} must be an IPv4 address")
        subscriber = profile.get("subscriber") or {}
        if "imsi" in subscriber and not re.fullmatch(r"\d{5,15}", str(subscriber.get("imsi", ""))):
            errors.append("IMSI must contain 5 to 15 digits")
        if "msisdn" in subscriber and not re.fullmatch(r"\d{5,20}", str(subscriber.get("msisdn", ""))):
            errors.append("MSISDN must contain 5 to 20 digits")
        safety = profile.get("safety") or {}
        if safety.get("rf_allowed") is not False:
            errors.append("RF authorization must be false by default in the central profile")
        if "maximum_duration_seconds" in safety and not _is_int(safety.get("maximum_duration_seconds"), 1, 600):
            errors.append("maximum_duration_seconds must be 1..600")
        radio = profile.get("radio") or {}
        if radio:
            if "bandwidth_mhz" in radio and radio.get("bandwidth_mhz") is not None and _bandwidth_key(radio.get("bandwidth_mhz")) is None:
                errors.append("radio.bandwidth_mhz must be numeric")
            for key in ("device", "clock_source", "time_source"):
                if key in radio and not self.COMPONENT_NAME_RE.fullmatch(str(radio.get(key) or "")):
                    errors.append(f"radio.{key} contains unsupported characters")
        ims = profile.get("ims") or {}
        if "domain" in ims and (len(str(ims.get("domain") or "")) > 253 or not self.NETWORK_NAME_RE.fullmatch(str(ims.get("domain") or ""))):
            errors.append("ims.domain must be a safe domain name")
        operator_note = str(safety.get("operator_note") or "")
        if len(operator_note) > 240:
            errors.append("safety.operator_note must not exceed 240 characters")
        return errors

    def _validate_rf_readiness(self, profile: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        radio = profile.get("radio") or {}
        if profile["profile"] == "4g-lte-x310":
            for key in ("lte_band", "earfcn", "tx_gain", "rx_gain"):
                if radio.get(key) in (None, ""):
                    errors.append(f"radio.{key} is required for 4G RF profiles")
            if not _valid_bandwidth_mhz(radio.get("bandwidth_mhz"), self.SRSRAN_4G_N_PRB_BY_BANDWIDTH):
                errors.append("radio.bandwidth_mhz must be one of 1.4, 3, 5, 10, 15, 20 for srsRAN 4G")
        if profile["profile"] == "5g-sa-x310":
            for key in ("band", "dl_arfcn", "tx_gain", "rx_gain"):
                if radio.get(key) in (None, ""):
                    errors.append(f"radio.{key} is required for 5G RF profiles")
            if not _valid_bandwidth_mhz(radio.get("bandwidth_mhz"), {5.0: 0, 10.0: 0, 15.0: 0, 20.0: 0, 40.0: 0, 50.0: 0, 100.0: 0}):
                errors.append("radio.bandwidth_mhz must be one of 5, 10, 15, 20, 40, 50, 100 for 5G RF profiles")
        if profile["profile"] == "5g-nsa-x310":
            required = ("device", "usrp_addr", "lte_band", "earfcn", "bandwidth_mhz", "nr_band", "nr_dl_arfcn", "subcarrier_spacing_khz", "tx_gain", "rx_gain", "clock_source", "time_source")
            for key in required:
                if radio.get(key) in (None, ""):
                    errors.append(f"radio.{key} is required for 5G NSA RF profiles")
            if not _valid_bandwidth_mhz(radio.get("bandwidth_mhz"), {10.0: 0}):
                errors.append("radio.bandwidth_mhz must be 10 for the current NSA EN-DC profile")
            for key in ("tx_gain", "rx_gain"):
                if not _is_finite_number(radio.get(key), 0, 100):
                    errors.append(f"radio.{key} must be a finite value between 0 and 100")
        return errors

    def _validate_rf_safety(self, profile: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        safety = profile.get("safety") or {}
        environment = str(safety.get("environment", "")).strip().lower()
        shielded = safety.get("shielded_environment") is True
        if environment != "cabled" and not shielded:
            errors.append("RF profiles require a cabled laboratory mode or shielded environment")
        if safety.get("authorization_confirmed") is not True:
            errors.append("RF authorization must be confirmed before apply")
        if safety.get("auto_stop") is not True:
            errors.append("RF profiles require auto_stop=true")
        if not str(safety.get("operator_note") or "").strip():
            errors.append("safety.operator_note must not be empty")
        if not _is_int(safety.get("maximum_duration_seconds"), 1, 600):
            errors.append("maximum_duration_seconds must be 1..600")
        if not _is_int(safety.get("attenuation_db"), 0, 120):
            errors.append("safety.attenuation_db must be 0..120")
        elif environment == "cabled" and int(safety.get("attenuation_db")) < 30:
            errors.append("safety.attenuation_db must be at least 30 dB for cabled RF profiles")
        if safety.get("antenna_connected") is True and not shielded:
            errors.append("antenna_connected=true requires shielded_environment=true")
        if profile["profile"] == "5g-nsa-x310":
            if safety.get("nr_rf_path_connected") is not True:
                errors.append("5G NSA requires nr_rf_path_connected=true")
            if safety.get("authorized_lab_frequencies") is not True:
                errors.append("5G NSA requires authorized_lab_frequencies=true")
            if environment not in {"cabled", "shielded"}:
                errors.append("5G NSA laboratory mode must be cabled or shielded")
        return errors

    def _validate_consistency(self, profile: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        profile_id = profile["profile"]
        network = profile.get("network", {})
        radio = profile.get("radio") or {}
        if profile_id == "4g-lte-x310" and radio.get("lte_band") not in (None, "") and radio.get("earfcn") not in (None, ""):
            try:
                band = int(radio["lte_band"])
                earfcn = int(radio["earfcn"])
            except (TypeError, ValueError):
                errors.append("radio.lte_band and radio.earfcn must be numeric")
            else:
                valid_range = self.LTE_BAND_EARFCN_RANGES.get(band)
                if valid_range is not None and earfcn not in valid_range:
                    errors.append(f"radio.earfcn is outside LTE band {band} downlink EARFCN range")
        if profile_id == "5g-nsa-x310":
            if radio.get("device") != "x300":
                errors.append("radio.device must be x300 for the current X310 NSA runtime")
            if radio.get("lte_band") != 7:
                errors.append("radio.lte_band must be 7 for the current NSA anchor")
            if radio.get("nr_band") != 3:
                errors.append("radio.nr_band must be 3 for the current NSA secondary carrier")
            if radio.get("subcarrier_spacing_khz") != 15:
                errors.append("radio.subcarrier_spacing_khz must be 15 for the current NSA runtime")
            if _is_int(radio.get("earfcn"), 0, 100000) and int(radio["earfcn"]) not in self.LTE_BAND_EARFCN_RANGES[7]:
                errors.append("radio.earfcn is outside LTE band 7 downlink EARFCN range")
            if _is_int(radio.get("nr_dl_arfcn"), 0, 1000000):
                nr_arfcn = int(radio["nr_dl_arfcn"])
                if not 361000 <= nr_arfcn <= 376000 or (nr_arfcn - 361000) % 20:
                    errors.append("radio.nr_dl_arfcn must use the NR n3 100 kHz raster (361000..376000)")
        return errors

    def _planned_changes(self, profile: dict[str, Any]) -> list[PlannedChange]:
        profile_id = profile["profile"]
        if profile_id == "5g-sa":
            return self._changes_5g_sa(profile)
        if profile_id == "5g-sa-x310":
            return self._changes_5g_sa_x310(profile)
        if profile_id == "5g-nsa-x310":
            return self._changes_5g_nsa_x310(profile)
        if profile_id == "5g-vonr":
            return self._changes_5g_vonr(profile)
        if profile_id == "4g-volte-sim":
            return self._changes_4g_volte_sim(profile)
        if profile_id == "4g-lte-sim":
            return self._changes_4g_lte_sim(profile)
        if profile_id == "4g-lte-x310":
            return self._changes_4g_lte_x310(profile)
        raise ProfileConfigError(404, "PROFILE_NOT_FOUND", f"Unknown profile: {profile_id}")

    def _change(self, rel: str, after: str) -> PlannedChange:
        path = self._confined(self.root / rel)
        return PlannedChange(path, _read(path), after)

    def _changes_5g_sa(self, profile: dict[str, Any]) -> list[PlannedChange]:
        n, c, s = profile["network"], profile["core"], profile["subscriber"]
        sl = n["slice"]
        changes = []
        env = _update_env(_read(self.root / "deployments/5g-sa/.env"), {
            "MCC": n["mcc"], "MNC": n["mnc"], "TAC": n["tac"], "SST": sl["sst"], "SD": sl["sd"], "DNN": n["dnn"], "SUBSCRIBER_IMSI": s["imsi"],
        })
        changes.append(self._change("deployments/5g-sa/.env", env))
        changes.append(self._change("deployments/5g-sa/open5gs/amf.yaml", _patch_5g_amf(_read(self.root / "deployments/5g-sa/open5gs/amf.yaml"), n)))
        changes.append(self._change("deployments/5g-sa/open5gs/smf.yaml", _patch_5g_smf(_read(self.root / "deployments/5g-sa/open5gs/smf.yaml"), n["dnn"], None, sl)))
        changes.append(self._change("deployments/5g-sa/ueransim/gnb.yaml", _patch_ueransim_gnb(_read(self.root / "deployments/5g-sa/ueransim/gnb.yaml"), n, c["amf_addr"], c["gnb_addr"])))
        changes.append(self._change("deployments/5g-sa/ueransim/ue.yaml", _patch_ueransim_ue(_read(self.root / "deployments/5g-sa/ueransim/ue.yaml"), n, s["imsi"], [n["dnn"]], c["gnb_addr"])))
        return changes

    def _changes_5g_sa_x310(self, profile: dict[str, Any]) -> list[PlannedChange]:
        n, c, r, safety = profile["network"], profile["core"], profile["radio"], profile["safety"]
        sl = n["slice"]
        sample_rates = {5.0: 15.36, 10.0: 15.36, 15.0: 23.04, 20.0: 23.04, 40.0: 46.08, 50.0: 61.44, 100.0: 122.88}
        sample_rate = sample_rates[float(r["bandwidth_mhz"])]
        env = _update_env(_read(self.root / "deployments/5g-sa-x310/.env"), {
            "AMF_ADDR": c["amf_addr"], "GNB_BIND_ADDR": c["gnb_bind_addr"], "N3_BIND_ADDR": c["n3_bind_addr"],
            "USRP_ADDR": r["usrp_addr"], "USRP_TYPE": r["device"], "USRP_CLOCK_SOURCE": r["clock_source"], "USRP_TIME_SOURCE": r["time_source"],
            "MCC": n["mcc"], "MNC": n["mnc"], "TAC": n["tac"], "SST": sl["sst"], "SD": sl["sd"],
            "CHANNEL_BANDWIDTH_MHZ": r["bandwidth_mhz"], "SAMPLE_RATE_MHZ": sample_rate, "DL_ARFCN": r["dl_arfcn"], "NR_BAND": r["band"], "TX_GAIN": r["tx_gain"], "RX_GAIN": r["rx_gain"],
            "MAXIMUM_DURATION_SECONDS": safety["maximum_duration_seconds"], "LAIN5G_ALLOW_5G_RF_START": "false",
        })
        channel_rel = "deployments/5g-sa-x310/rf/channel-plan.yaml"
        channel_data = _loads_yaml(_read(self.root / channel_rel))
        channel_data.update({"nr_band": r["band"], "dl_arfcn": r["dl_arfcn"], "channel_bandwidth_mhz": r["bandwidth_mhz"], "authorized_lab_frequency": safety["authorization_confirmed"], "operator_note": safety["operator_note"]})
        safety_rel = "deployments/5g-sa-x310/rf/safety-manifest.yaml"
        safety_data = _loads_yaml(_read(self.root / safety_rel))
        safety_data.update({
            "lab_mode": safety["environment"], "authorization_confirmed": safety["authorization_confirmed"],
            "antenna_connected": safety["antenna_connected"], "attenuation_db": safety["attenuation_db"],
            "shielded_environment": safety["shielded_environment"], "maximum_duration_seconds": safety["maximum_duration_seconds"],
            "auto_stop": safety["auto_stop"], "capture_logs": True, "operator_note": safety["operator_note"],
        })
        return [
            self._change("deployments/5g-sa-x310/.env", env),
            self._change("deployments/5g-sa-x310/open5gs/amf.yaml", _patch_5g_amf(_read(self.root / "deployments/5g-sa-x310/open5gs/amf.yaml"), n)),
            self._change("deployments/5g-sa-x310/open5gs/smf.yaml", _patch_5g_smf(_read(self.root / "deployments/5g-sa-x310/open5gs/smf.yaml"), n["dnn"], None, sl)),
            self._change(channel_rel, _dumps_yaml(channel_data)),
            self._change(safety_rel, _dumps_yaml(safety_data)),
        ]

    def _changes_5g_nsa_x310(self, profile: dict[str, Any]) -> list[PlannedChange]:
        n, core, ran, radio = profile["network"], profile["core"], profile["ran"], profile["radio"]
        subscriber, safety = profile["subscriber"], profile["safety"]
        common_env = _update_env(_read(self.root / "deployments/4g-volte/common/.env"), {
            "MCC": n["mcc"], "MNC": n["mnc"], "TAC": n["tac"], "APN_INTERNET": n["apn_internet"], "SUBSCRIBER_IMSI": subscriber["imsi"],
        })
        nsa_env = _update_env(_read(self.root / "deployments/5g-nsa-x310/.env"), {
            "USRP_ADDR": radio["usrp_addr"], "USRP_TYPE": radio["device"], "RF_DURATION_SECONDS": safety["maximum_duration_seconds"],
            "LAIN5G_ALLOW_5G_NSA_RF_START": "false",
        })
        enb_rel = "deployments/5g-nsa-x310/ran/enb.conf"
        enb = _patch_enb_conf(
            _read(self.root / enb_rel), n, core["mme_addr"], ran["enb_bind_addr"], radio["earfcn"], radio["tx_gain"], radio["rx_gain"],
            radio["bandwidth_mhz"], radio["usrp_addr"], radio["device"], radio["clock_source"], radio["time_source"],
        )
        rr_rel = "deployments/5g-nsa-x310/ran/rr.conf"
        rr = _patch_nsa_rr_conf(_read(self.root / rr_rel), n["tac"], radio["earfcn"], radio["nr_dl_arfcn"], radio["nr_band"])
        channel_rel = "deployments/5g-nsa-x310/rf/channel-plan.yaml"
        channel = _loads_yaml(_read(self.root / channel_rel))
        lte_dl, lte_ul = _lte_band7_frequencies_mhz(radio["earfcn"])
        nr_dl, nr_ul = _nr_n3_frequencies_mhz(radio["nr_dl_arfcn"])
        channel.update({
            "mode": "NSA_EN_DC_EXPERIMENTAL", "lte_band": radio["lte_band"], "lte_dl_earfcn": radio["earfcn"],
            "lte_bandwidth_mhz": radio["bandwidth_mhz"], "lte_downlink_frequency_mhz": lte_dl, "lte_uplink_frequency_mhz": lte_ul,
            "nr_band": radio["nr_band"], "nr_dl_arfcn": radio["nr_dl_arfcn"], "nr_bandwidth_mhz": radio["bandwidth_mhz"],
            "nr_downlink_frequency_mhz": nr_dl, "nr_uplink_frequency_mhz": nr_ul, "subcarrier_spacing_khz": radio["subcarrier_spacing_khz"],
            "rf_channels": 2, "authorized_lab_frequencies": safety["authorized_lab_frequencies"], "operator_note": safety["operator_note"],
        })
        safety_rel = "deployments/5g-nsa-x310/rf/safety-manifest.yaml"
        manifest = _loads_yaml(_read(self.root / safety_rel))
        manifest.update({
            "authorization_confirmed": safety["authorization_confirmed"], "auto_stop": safety["auto_stop"], "capture_logs": True,
            "maximum_duration_seconds": safety["maximum_duration_seconds"], "lab_mode": safety["environment"], "attenuation_db": safety["attenuation_db"],
            "antenna_connected": safety["antenna_connected"], "nr_rf_path_connected": safety["nr_rf_path_connected"],
            "shielded_environment": safety["shielded_environment"], "operator_note": safety["operator_note"],
        })
        return [
            self._change("deployments/4g-volte/common/.env", common_env),
            self._change("deployments/4g-volte/x310/open5gs/mme.yaml", _patch_4g_mme(_read(self.root / "deployments/4g-volte/x310/open5gs/mme.yaml"), n)),
            self._change("deployments/4g-volte/x310/open5gs/pgwc.yaml", _patch_4g_pgwc(_read(self.root / "deployments/4g-volte/x310/open5gs/pgwc.yaml"), n)),
            self._change("deployments/5g-nsa-x310/.env", nsa_env),
            self._change(enb_rel, enb),
            self._change(rr_rel, rr),
            self._change(channel_rel, _dumps_yaml(channel)),
            self._change(safety_rel, _dumps_yaml(manifest)),
        ]

    def _changes_5g_vonr(self, profile: dict[str, Any]) -> list[PlannedChange]:
        n, c, s, ims = profile["network"], profile["core"], profile["subscriber"], profile["ims"]
        sl = n["slice"]
        env = _update_env(_read(self.root / "deployments/5g-vonr/.env"), {
            "MCC": n["mcc"], "MNC": n["mnc"], "TAC": n["tac"], "SST": sl["sst"], "SD": sl["sd"],
            "DNN_INTERNET": n["dnn_internet"], "DNN_IMS": n["dnn_ims"], "SUBSCRIBER_IMSI": s["imsi"], "SUBSCRIBER_MSISDN": s["msisdn"], "IMS_DOMAIN": ims["domain"],
        })
        return [
            self._change("deployments/5g-vonr/.env", env),
            self._change("deployments/5g-vonr/open5gs/amf.yaml", _patch_5g_amf(_read(self.root / "deployments/5g-vonr/open5gs/amf.yaml"), n)),
            self._change("deployments/5g-vonr/open5gs/smf.yaml", _patch_5g_smf(_read(self.root / "deployments/5g-vonr/open5gs/smf.yaml"), n["dnn_internet"], n["dnn_ims"], sl)),
            self._change("deployments/5g-vonr/ueransim/gnb.yaml", _patch_ueransim_gnb(_read(self.root / "deployments/5g-vonr/ueransim/gnb.yaml"), n, c["amf_addr"], c["gnb_addr"])),
            self._change("deployments/5g-vonr/ueransim/ue-ims.yaml", _patch_ueransim_ue(_read(self.root / "deployments/5g-vonr/ueransim/ue-ims.yaml"), n, None, [n["dnn_internet"], n["dnn_ims"]], c["gnb_addr"])),
        ]

    def _changes_4g_volte_sim(self, profile: dict[str, Any]) -> list[PlannedChange]:
        return self._changes_4g(profile, "sim", "10.41.0.40")

    def _changes_4g_lte_sim(self, profile: dict[str, Any]) -> list[PlannedChange]:
        n, core, ran, subscriber = profile["network"], profile["core"], profile["ran"], profile["subscriber"]
        env = _update_env(_read(self.root / "deployments/4g-volte/common/.env"), {
            "MCC": n["mcc"], "MNC": n["mnc"], "TAC": n["tac"], "APN_INTERNET": n["apn_internet"], "SUBSCRIBER_IMSI": subscriber["imsi"],
        })
        enb_rel = "deployments/4g-lte-sim/ran/enb.conf"
        ue_rel = "deployments/4g-lte-sim/ran/ue.conf"
        return [
            self._change("deployments/4g-volte/common/.env", env),
            self._change("deployments/4g-lte-sim/open5gs/mme.yaml", _patch_4g_mme(_read(self.root / "deployments/4g-lte-sim/open5gs/mme.yaml"), n)),
            self._change("deployments/4g-lte-sim/open5gs/pgwc.yaml", _patch_4g_pgwc(_read(self.root / "deployments/4g-lte-sim/open5gs/pgwc.yaml"), n)),
            self._change(enb_rel, _patch_enb_conf(_read(self.root / enb_rel), n, core["mme_addr"], ran["enb_bind_addr"], ran["dl_earfcn"], ran["tx_gain"], ran["rx_gain"])),
            self._change(ue_rel, _patch_ue_conf(_read(self.root / ue_rel), n, subscriber["imsi"], ran["dl_earfcn"])),
        ]

    def _changes_4g_lte_x310(self, profile: dict[str, Any]) -> list[PlannedChange]:
        n, core, ran, r, safety = profile["network"], profile["core"], profile["ran"], profile["radio"], profile["safety"]
        subscriber, ims = profile["subscriber"], profile["ims"]
        env = _update_env(_read(self.root / "deployments/4g-volte/common/.env"), {
            "MCC": n["mcc"], "MNC": n["mnc"], "TAC": n["tac"], "APN_INTERNET": n["apn_internet"], "APN_IMS": n["apn_ims"],
            "SUBSCRIBER_IMSI": subscriber["imsi"], "SUBSCRIBER_MSISDN": subscriber["msisdn"], "IMS_DOMAIN": ims["domain"],
        })
        enb_rel = "deployments/4g-volte/x310/ran/enb.conf"
        enb = _patch_enb_conf(_read(self.root / enb_rel), n, core["mme_addr"], ran["enb_bind_addr"], r["earfcn"], r["tx_gain"], r["rx_gain"], r["bandwidth_mhz"], r.get("usrp_addr"), r.get("device"), r.get("clock_source"), r.get("time_source"))
        channel_rel = "deployments/4g-volte/x310/rf/channel-plan.yaml"
        channel_data = _loads_yaml(_read(self.root / channel_rel))
        channel_data.update({"band": r["lte_band"], "earfcn": r["earfcn"], "bandwidth_mhz": r["bandwidth_mhz"], "tx_gain": r["tx_gain"], "rx_gain": r["rx_gain"]})
        manifest = _dumps_yaml({
            "lab_mode": safety["environment"],
            "authorization_confirmed": safety["authorization_confirmed"],
            "antenna_connected": safety["antenna_connected"],
            "attenuation_db": safety["attenuation_db"],
            "shielded_environment": safety["shielded_environment"],
            "maximum_duration_seconds": safety["maximum_duration_seconds"],
            "auto_stop": safety["auto_stop"],
            "capture_logs": True,
            "operator_note": safety["operator_note"],
        })
        return [
            self._change("deployments/4g-volte/common/.env", env),
            self._change("deployments/4g-volte/x310/open5gs/mme.yaml", _patch_4g_mme(_read(self.root / "deployments/4g-volte/x310/open5gs/mme.yaml"), n)),
            self._change("deployments/4g-volte/x310/open5gs/pgwc.yaml", _patch_4g_pgwc(_read(self.root / "deployments/4g-volte/x310/open5gs/pgwc.yaml"), n)),
            self._change(enb_rel, enb),
            self._change(channel_rel, _dumps_yaml(channel_data)),
            self._change("deployments/4g-volte/x310/rf/safety-manifest.yaml", manifest),
        ]

    def _changes_4g(self, profile: dict[str, Any], variant: str, bind_addr: str) -> list[PlannedChange]:
        n, core, ran, s, ims = profile["network"], profile["core"], profile["ran"], profile["subscriber"], profile.get("ims", {})
        env = _update_env(_read(self.root / "deployments/4g-volte/common/.env"), {
            "MCC": n["mcc"], "MNC": n["mnc"], "TAC": n["tac"], "APN_INTERNET": n["apn_internet"], "APN_IMS": n["apn_ims"],
            "SUBSCRIBER_IMSI": s["imsi"], "SUBSCRIBER_MSISDN": s["msisdn"], "IMS_DOMAIN": ims.get("domain", ""),
        })
        base = f"deployments/4g-volte/{'common' if variant == 'sim' else 'x310'}"
        enb_rel = f"deployments/4g-volte/{variant}/ran/enb.conf"
        enb = _patch_enb_conf(_read(self.root / enb_rel), n, core["mme_addr"], bind_addr, ran.get("dl_earfcn") or profile.get("radio", {}).get("earfcn"), ran.get("tx_gain") or profile.get("radio", {}).get("tx_gain"), ran.get("rx_gain") or profile.get("radio", {}).get("rx_gain"), usrp_addr=profile.get("radio", {}).get("usrp_addr"))
        changes = [
            self._change("deployments/4g-volte/common/.env", env),
            self._change(f"{base}/open5gs/mme.yaml", _patch_4g_mme(_read(self.root / f"{base}/open5gs/mme.yaml"), n)),
            self._change(f"{base}/open5gs/pgwc.yaml", _patch_4g_pgwc(_read(self.root / f"{base}/open5gs/pgwc.yaml"), n)),
            self._change(enb_rel, enb),
        ]
        if variant == "sim":
            changes.append(self._change("deployments/4g-volte/sim/ran/ue.conf", _patch_ue_conf(_read(self.root / "deployments/4g-volte/sim/ran/ue.conf"), n, s["imsi"], ran["dl_earfcn"])))
        return changes

    def _backup(self, profile_id: str, changes: list[PlannedChange]) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        backup_dir = self._confined(self.backups_dir / profile_id / timestamp)
        for change in changes:
            if not change.path.exists():
                continue
            target = self._confined(backup_dir / change.path.relative_to(self.root))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(change.path, target)
        return backup_dir

    def _change_payload(self, change: PlannedChange) -> dict[str, Any]:
        before = _redact_env_secrets(change.before, self.SECRET_KEYS)
        after = _redact_env_secrets(change.after, self.SECRET_KEYS)
        return {
            "path": self._rel(change.path),
            "changed": change.before != change.after,
            "diff": "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=f"a/{self._rel(change.path)}", tofile=f"b/{self._rel(change.path)}")),
        }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _string_values(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            values.extend(_string_values(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            values.extend(_string_values(item, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        values.append((prefix or "value", value))
    return values


def _redact_env_secrets(text: str, secret_keys: set[str]) -> str:
    pattern = re.compile(rf"^({'|'.join(re.escape(key) for key in sorted(secret_keys))})=.*$", re.MULTILINE)
    return pattern.sub(r"\1=<redacted>", text)


def _is_int(value: Any, minimum: int, maximum: int) -> bool:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return False
    return minimum <= number <= maximum


def _is_finite_number(value: Any, minimum: float, maximum: float) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and minimum <= number <= maximum


def _is_ip(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def _loads_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, value = raw.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value.strip())
    return root


def _parse_scalar(value: str) -> Any:
    if value in {"null", "~"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _dumps_yaml(data: dict[str, Any], indent: int = 0) -> str:
    lines: list[str] = []
    for key, value in data.items():
        prefix = " " * indent
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dumps_yaml(value, indent + 2).rstrip("\n"))
        else:
            lines.append(f"{prefix}{key}: {_format_scalar(value)}")
    return "\n".join(lines) + "\n"


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    text = str(value)
    if text == "" or re.fullmatch(r"0[0-9]+", text) or any(ch in text for ch in ":#{}[]"):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _unknown_paths(base: dict[str, Any], patch: dict[str, Any], prefix: str = "") -> list[str]:
    unknown: list[str] = []
    for key, value in patch.items():
        path = f"{prefix}.{key}" if prefix else key
        if key not in base:
            unknown.append(path)
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            unknown.extend(_unknown_paths(base[key], value, path))
    return sorted(unknown)


def _update_env(text: str, updates: dict[str, Any]) -> str:
    seen: set[str] = set()
    lines: list[str] = []
    for line in text.splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            lines.append(line)
            continue
        key = line.split("=", 1)[0]
        if key in updates and key not in ProfileConfigService.SECRET_KEYS:
            lines.append(f"{key}={'' if updates[key] is None else updates[key]}")
            seen.add(key)
        else:
            lines.append(line)
            seen.add(key)
    for key, value in updates.items():
        if key not in seen and key not in ProfileConfigService.SECRET_KEYS:
            lines.append(f"{key}={'' if value is None else value}")
    return "\n".join(lines) + "\n"


def _replace_all(text: str, pattern: str, repl: str) -> str:
    return re.sub(pattern, repl, text, flags=re.MULTILINE)


def _patch_5g_amf(text: str, n: dict[str, Any]) -> str:
    sl = n["slice"]
    text = _replace_all(text, r"mcc:\s*\d+", f"mcc: {n['mcc']}")
    text = _replace_all(text, r"mnc:\s*\d+", f"mnc: {n['mnc']}")
    text = _replace_all(text, r"tac:\s*\d+", f"tac: {n['tac']}")
    text = _replace_all(text, r"sst:\s*\d+", f"sst: {sl['sst']}")
    return _replace_all(text, r"sd:\s*[0-9A-Fa-f]+", f"sd: {sl['sd']}")


def _patch_5g_smf(text: str, dnn1: str, dnn2: str | None, sl: dict[str, Any]) -> str:
    text = _replace_all(text, r"sst:\s*\d+", f"sst: {sl['sst']}")
    text = _replace_all(text, r"sd:\s*[0-9A-Fa-f]+", f"sd: {sl['sd']}")
    dnns = [dnn1] + ([dnn2] if dnn2 else [])
    for old, new in zip(["internet", "ims"], dnns):
        text = re.sub(rf"dnn:\s*{old}\b", f"dnn: {new}", text)
        text = re.sub(rf"-\s+{old}\b", f"- {new}", text)
    return text


def _patch_ueransim_gnb(text: str, n: dict[str, Any], amf_addr: str, gnb_addr: str) -> str:
    sl = n["slice"]
    text = _replace_all(text, r"mcc:\s*'[^']+'", f"mcc: '{n['mcc']}'")
    text = _replace_all(text, r"mnc:\s*'[^']+'", f"mnc: '{n['mnc']}'")
    text = _replace_all(text, r"tac:\s*\d+", f"tac: {n['tac']}")
    text = _replace_all(text, r"(linkIp|ngapIp|gtpIp):\s*[0-9.]+", rf"\1: {gnb_addr}")
    text = _replace_all(text, r"address:\s*[0-9.]+", f"address: {amf_addr}")
    text = _replace_all(text, r"sst:\s*\d+", f"sst: {sl['sst']}")
    return _replace_all(text, r"sd:\s*[0-9A-Fa-f]+", f"sd: {sl['sd']}")


def _patch_ueransim_ue(text: str, n: dict[str, Any], imsi: str | None, dnns: list[str], gnb_addr: str) -> str:
    sl = n["slice"]
    if imsi:
        text = _replace_all(text, r"supi:\s*'imsi-[^']+'", f"supi: 'imsi-{imsi}'")
    text = _replace_all(text, r"mcc:\s*'[^']+'", f"mcc: '{n['mcc']}'")
    text = _replace_all(text, r"mnc:\s*'[^']+'", f"mnc: '{n['mnc']}'")
    text = _replace_all(text, r"-\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", f"- {gnb_addr}")
    text = _replace_all(text, r"sst:\s*\d+", f"sst: {sl['sst']}")
    text = _replace_all(text, r"sd:\s*[0-9A-Fa-f]+", f"sd: {sl['sd']}")
    for old, new in zip(["internet", "ims"], dnns):
        text = re.sub(rf"apn:\s*{old}\b", f"apn: {new}", text)
    return text


def _patch_4g_mme(text: str, n: dict[str, Any]) -> str:
    text = _replace_all(text, r"mcc:\s*\d+", f"mcc: {n['mcc']}")
    text = _replace_all(text, r"mnc:\s*\d+", f"mnc: {n['mnc']}")
    return _replace_all(text, r"tac:\s*\d+", f"tac: {n['tac']}")


def _patch_4g_pgwc(text: str, n: dict[str, Any]) -> str:
    text = re.sub(r"dnn:\s*internet\b", f"dnn: {n['apn_internet']}", text)
    return re.sub(r"dnn:\s*ims\b", f"dnn: {n['apn_ims']}", text) if "apn_ims" in n else text


def _patch_enb_conf(text: str, n: dict[str, Any], mme_addr: str, bind_addr: str, earfcn: Any, tx_gain: Any, rx_gain: Any, bandwidth_mhz: Any = None, usrp_addr: Any = None, usrp_type: Any = None, clock_source: Any = None, time_source: Any = None) -> str:
    replacements = {"mcc": n["mcc"], "mnc": n["mnc"], "mme_addr": mme_addr, "gtp_bind_addr": bind_addr, "s1c_bind_addr": bind_addr, "dl_earfcn": earfcn, "tx_gain": tx_gain, "rx_gain": rx_gain}
    if bandwidth_mhz is not None:
        replacements["n_prb"] = _srsran_4g_n_prb(bandwidth_mhz)
    for key, value in replacements.items():
        text = _replace_all(text, rf"^{key}\s*=.*$", f"{key} = {value}")
    if usrp_addr:
        text = re.sub(r"addr=[0-9.]+", f"addr={usrp_addr}", text)
    if usrp_type:
        text = re.sub(r"type=[^,\s]+", f"type={usrp_type}", text)
    if clock_source:
        text = re.sub(r"clock=[^,\s]+", f"clock={clock_source}", text)
    if time_source:
        text = re.sub(r"time_source=[^,\s]+", f"time_source={time_source}", text)
    return text


def _bandwidth_key(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return round(number, 1)


def _valid_bandwidth_mhz(value: Any, allowed: dict[float, Any]) -> bool:
    key = _bandwidth_key(value)
    return key in allowed if key is not None else False


def _srsran_4g_n_prb(bandwidth_mhz: Any) -> int:
    key = _bandwidth_key(bandwidth_mhz)
    if key not in ProfileConfigService.SRSRAN_4G_N_PRB_BY_BANDWIDTH:
        raise ProfileConfigError(422, "PROFILE_VALIDATION_FAILED", "Unsupported srsRAN 4G channel bandwidth")
    return ProfileConfigService.SRSRAN_4G_N_PRB_BY_BANDWIDTH[key]


def _patch_ue_conf(text: str, n: dict[str, Any], imsi: str, earfcn: Any) -> str:
    for key, value in {"dl_earfcn": earfcn, "imsi": imsi, "apn": n["apn_internet"]}.items():
        text = _replace_all(text, rf"^{key}\s*=.*$", f"{key} = {value}")
    return text


def _patch_nsa_rr_conf(text: str, tac: Any, lte_earfcn: Any, nr_arfcn: Any, nr_band: Any) -> str:
    text = re.sub(r"(tac\s*=\s*)0x[0-9A-Fa-f]+", rf"\g<1>0x{int(tac):04X}", text)
    text = _replace_all(text, r"^\s*dl_earfcn\s*=.*$", f"    dl_earfcn = {lte_earfcn};")
    text = _replace_all(text, r"^\s*dl_arfcn\s*=.*$", f"    dl_arfcn = {nr_arfcn};")
    return _replace_all(text, r"^\s*band\s*=.*$", f"    band = {nr_band};")


def _lte_band7_frequencies_mhz(earfcn: Any) -> tuple[float, float]:
    offset = int(earfcn) - 2750
    return round(2620.0 + 0.1 * offset, 3), round(2500.0 + 0.1 * offset, 3)


def _nr_n3_frequencies_mhz(arfcn: Any) -> tuple[float, float]:
    downlink = int(arfcn) * 0.005
    return round(downlink, 3), round(downlink - 95.0, 3)
