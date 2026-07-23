import { Boxes, CheckCircle2, Network, Server, Smartphone, X } from 'lucide-react';
import type { DeploymentSummary } from '../types/deployment';
import { ActionButton } from './ActionButton';

interface SimulationStartDialogProps {
  deployment: DeploymentSummary;
  open: boolean;
  loading: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

const flows: Record<string, { label: string; summary: string; stages: { name: string; detail: string }[] }> = {
  '5g-sa': {
    label: '5GC + UERANSIM',
    summary: 'Starts the complete software-only 5G SA path, including the simulated gNB and UE.',
    stages: [
      { name: '5G Core', detail: 'Open5GS control and user plane' },
      { name: 'RAN', detail: 'UERANSIM gNB' },
      { name: 'UE', detail: 'UERANSIM subscriber and PDU session' },
    ],
  },
  '4g-volte-sim': {
    label: 'LTE + VoLTE simulation',
    summary: 'Starts the combined 4G LTE simulation and VoLTE signaling stack in one workspace.',
    stages: [
      { name: 'EPC', detail: 'Open5GS LTE core' },
      { name: 'RAN + UE', detail: 'srsRAN over ZMQ' },
      { name: 'IMS', detail: 'P/I/S-CSCF, DNS and SIP registration' },
    ],
  },
  '4g-lte-sim': {
    label: 'srsENB + srsUE simulation',
    summary: 'Starts an isolated LTE data lab over ZMQ without any IMS or SIP services.',
    stages: [
      { name: 'EPC', detail: 'Open5GS LTE core and internet APN' },
      { name: 'eNodeB', detail: 'srsENB using the ZMQ radio' },
      { name: 'UE', detail: 'srsUE attach and default bearer' },
    ],
  },
  '5g-vonr-sim': {
    label: '5G SA + VoNR simulation',
    summary: 'Starts the full 5G software path with internet and IMS PDU sessions plus SIP signaling.',
    stages: [
      { name: '5G Core', detail: 'Open5GS control and dual user plane' },
      { name: 'RAN + UE', detail: 'UERANSIM gNB and subscriber' },
      { name: 'IMS', detail: 'P/I/S-CSCF, DNS and SIP registration' },
    ],
  },
};

const stageIcons = [Server, Network, Smartphone];

export function SimulationStartDialog({ deployment, open, loading, onCancel, onConfirm }: SimulationStartDialogProps) {
  if (!open) return null;
  const flow = flows[deployment.id] || {
    label: 'Software simulation',
    summary: 'Starts every service registered for this software-only laboratory scenario.',
    stages: [{ name: 'Services', detail: `${deployment.components.length} registered components` }],
  };

  return (
    <div className="dialog-backdrop simulation-dialog-backdrop" role="presentation">
      <section className="simulation-start-dialog" role="dialog" aria-modal="true" aria-labelledby="simulation-start-title">
        <header>
          <div className="simulation-dialog-title">
            <span><Boxes size={20} /></span>
            <div><small>{flow.label}</small><h2 id="simulation-start-title">Start {deployment.name}</h2></div>
          </div>
          <button className="dialog-close" type="button" aria-label="Close start dialog" disabled={loading} onClick={onCancel}><X size={18} /></button>
        </header>
        <div className="simulation-safe-banner"><CheckCircle2 size={18} /><div><strong>Software-only scenario</strong><span>No SDR device or RF transmission is used by this launch.</span></div></div>
        <div className="simulation-dialog-body">
          <p>{flow.summary}</p>
          <div className="simulation-stage-grid">
            {flow.stages.map((stage, index) => {
              const Icon = stageIcons[index] || Boxes;
              return <div key={stage.name}><span><Icon size={17} /></span><strong>{stage.name}</strong><p>{stage.detail}</p></div>;
            })}
          </div>
          <div className="simulation-launch-note"><strong>What happens next</strong><p>The backend checks for another active scenario, starts this stack, and refreshes service status. Use <b>Validate</b> after startup to record registration, session and signaling evidence.</p></div>
        </div>
        <footer><ActionButton variant="secondary" disabled={loading} onClick={onCancel}>Cancel</ActionButton><ActionButton loading={loading} onClick={onConfirm}><Boxes size={15} />Start full simulation</ActionButton></footer>
      </section>
    </div>
  );
}
