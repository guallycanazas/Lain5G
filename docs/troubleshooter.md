# Troubleshooter coverage

The profile Troubleshooter turns validation failures into a likely cause, a concrete next step, and a profile log link. It only runs an automatic action where the action is already supported by that profile. It never enables guarded RF, changes host networking, flashes an FPGA, edits subscriber secrets, or deletes containers.

## Recovery actions

| Failure | Profiles | Troubleshooter behavior |
| --- | --- | --- |
| Required simulation core/RAN services are down | 4G LTE simulation, 5G SA simulation | Offers **Start simulation and verify**. After the existing start confirmation, it starts the simulation and immediately runs validation again. |
| EPC/5GC services are down | 4G X310, 5G SA X310, 5G NSA X310 | Offers **Start core and verify (no RF)**. It starts core services only and runs validation again; it never starts the eNB/gNB or transmits. |
| Ethernet link missing, competing route, or X310 unreachable | X310 profiles | Gives cable/NIC/subnet/route checks and allows a non-transmitting Hardware check. It cannot repair a cable or alter host routes automatically. |
| UHD/FPGA RFNoC protocol mismatch, e.g. SW 2.0 vs HW 1.0 | X310 profiles | Identifies software/FPGA incompatibility and requires a compatible image/power cycle. It does not flash the radio. |
| UHD management transaction timeout / RAN exits during UHD initialization | X310 profiles | Points to the session log and checks Ethernet, UHD/FPGA compatibility, and RFNoC initialization. It does not retry RF automatically. |
| RF web control disabled by operator configuration | X310 profiles | Explains that an administrator must review the local setting; it will not bypass the guard. |
| Previous containers still active / repeated start | All profiles | Asks the operator to sync inventory and inspect logs. Stop only a stale profile session; shared core services must be preserved. |
| MongoDB subscriber request timeout | Subscribers / core-backed profiles | Identifies database health and routing as likely causes and warns that a timeout does not prove a write failed. Retry is explicit; it does not duplicate or delete a subscriber. |
| IMS provisioning, DNS, or SIP REGISTER/authentication failure | VoLTE/IMS-capable profiles | Checks IMS database, DNS, P-CSCF reachability, identities and authentication against the subscriber store; it does not invent or overwrite credentials. |
| UE registration, bearer/PDU session, APN/DNN, IP, TUN, or ping failure | 4G/5G profiles | Checks subscription, selected APN/DNN, slice/session policy, address pools, routing, NAT and UE evidence. It does not claim a subscriber record proves a successful attach. |
| Auto-stop or missing validation logs | X310 profiles | Checks run/session records, process timeout and log permissions. Operator inspects and stops a process if it is actually still active. |

## Safe induced-failure tests

`src/frontend/tests/profileTroubleshooter.test.tsx` injects synthetic failures through mocked API responses for every public profile. The simulated core/container error starts as `FAIL`; the test invokes the Troubleshooter action, the mock reports the service start, and the next validation returns `PASS`. Hardware, Ethernet, RFNoC and RF-control errors are injected separately and must remain visible; the tests assert no RF start request is sent.

These tests exercise the UI and recovery flow without stopping real containers, changing host network settings, touching an X310, or transmitting RF.
