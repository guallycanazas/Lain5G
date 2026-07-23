import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'danger';
}

export function ActionButton({ loading, children, variant = 'primary', disabled, ...props }: ActionButtonProps) {
  return (
    <button className={`action-button ${variant}`} disabled={disabled || loading} {...props}>
      {loading ? 'Processing...' : children}
    </button>
  );
}
