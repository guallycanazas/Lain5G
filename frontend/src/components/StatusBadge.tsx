import { deploymentLabel, validationLabel } from '../utils/status';

interface StatusBadgeProps {
  status: string;
  kind?: 'deployment' | 'validation';
}

export function StatusBadge({ status, kind = 'deployment' }: StatusBadgeProps) {
  const label = kind === 'validation' ? validationLabel(status) : deploymentLabel(status);
  return <span className={`status-badge status-${status.toLowerCase().replace('_', '-')}`}>{label}</span>;
}
