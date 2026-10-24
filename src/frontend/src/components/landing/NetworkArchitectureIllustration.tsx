export function NetworkArchitectureIllustration() {
  return (
    <figure className="architecture-visual">
      <img
        src="/images/lain5g/control-plane-topology.webp"
        width="1672"
        height="941"
        alt="Illustrated private mobile network with radio access, core services, a SIM, and a laboratory handset"
        decoding="async"
        fetchPriority="high"
      />
      <figcaption>
        {['SDR + RAN', 'Open5GS core', 'Data session', 'Lab UE + SIM'].map((label) => <span key={label}>{label}</span>)}
        <small>eSIM and Kubernetes labels are design concepts, not validated runtime claims.</small>
      </figcaption>
    </figure>
  );
}
