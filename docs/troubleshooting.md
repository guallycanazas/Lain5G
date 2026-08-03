# Troubleshooting

Start with the selected profile's current state rather than assuming a single
cause. Replace `PROFILE` with one of the public profile IDs:

```bash
./lain5g scenario status PROFILE
./lain5g scenario validate PROFILE
./lain5g scenario logs PROFILE
```

Keep logs private until they have been reviewed and sanitized. Do not publish
subscriber credentials, complete identifiers, private addresses, RF settings,
device serials, or authorization records.

## Local Configuration

If a profile reports missing or incomplete local configuration, prepare it with:

```bash
./lain5g scenario setup PROFILE
```

The command creates ignored local files and synthetic credentials without
printing secret values. After manual changes, validate the profile again and
restart the affected scenario so rendered configuration is refreshed.

## Container and Service Readiness

Inspect scenario status and bounded service logs. Check for unhealthy or
restarting containers, missing images, invalid rendered configuration, port or
volume conflicts, and host resource limits. A running container proves only
process state; use the scenario validator for protocol and data-plane checks.

## Docker Networking

Check whether the configured Docker subnet overlaps another Docker network, a
VPN, a host route, or the local LAN. For static addressing, confirm that every
address is unused inside the selected subnet and that all related environment
and Compose settings agree. Recreate only the affected application or scenario
networks after reviewing the effective configuration; do not remove unrelated
volumes or networks as a generic remedy.

## RAN and Core Signaling

For S1 or NG setup failures, compare the rendered RAN endpoint with the
MME/AMF listener and verify transport reachability. Then check PLMN, TAC, slice,
and DNN/APN consistency. Host firewalls, SCTP support, container routing, and a
stale process can also prevent signaling even when configuration values match.

## UE Registration

Review the subscriber-provisioning, core authentication, and UE logs together.
Common categories include a missing subscriber, inconsistent PLMN or subscriber
data, authentication or sequence-number state, unsupported slice/DNN settings,
and stale rendered configuration. Use synthetic credentials for reproducible
tests and never print or publish real authentication material.

## Data-Plane Connectivity

Use the validator to determine whether failure occurs at session establishment,
tunnel creation, address assignment, forwarding, NAT, firewall policy, or
target reachability. Confirm that the expected tunnel exists, has an address,
and is used by the test traffic. Required host capabilities and `/dev/net/tun`
availability depend on the selected profile.

## Checked-In 5G SA Defaults

The included `5g-sa` profile uses the `10.20.0.0/24` Docker subnet. Within that
specific profile, MongoDB and subscriber initialization use `10.20.0.2` and
`10.20.0.3`, the AMF endpoint is `10.20.0.5:38412`, and the application backend
reserves `10.20.0.250` when it joins the core network. These are reproducibility
defaults, not universal requirements. Custom deployments must choose an
available subnet and addresses, then update every related setting consistently.
