export function LoadingState({ label = 'Loading...' }: { label?: string }) {
  return <div className="panel muted" aria-live="polite">{label}</div>;
}
