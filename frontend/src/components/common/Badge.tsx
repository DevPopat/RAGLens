import { ReactNode } from 'react';

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
  children: ReactNode;
  className?: string;
}

export default function Badge({
  variant = 'default',
  size = 'md',
  children,
  className = '',
}: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    error: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {children}
    </span>
  );
}

interface StatusBadgeProps {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'success' | 'error';
  size?: 'sm' | 'md';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const statusConfig = {
    pending: { variant: 'default' as const, label: 'Pending' },
    running: { variant: 'info' as const, label: 'Running' },
    completed: { variant: 'success' as const, label: 'Completed' },
    failed: { variant: 'error' as const, label: 'Failed' },
    success: { variant: 'success' as const, label: 'Success' },
    error: { variant: 'error' as const, label: 'Error' },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size={size}>
      <span
        className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
          status === 'running' ? 'animate-pulse' : ''
        } ${
          config.variant === 'default'
            ? 'bg-gray-500'
            : config.variant === 'success'
            ? 'bg-green-500'
            : config.variant === 'warning'
            ? 'bg-yellow-500'
            : config.variant === 'error'
            ? 'bg-red-500'
            : 'bg-blue-500'
        }`}
      />
      {config.label}
    </Badge>
  );
}

interface SeverityBadgeProps {
  severity: 'high' | 'medium' | 'low';
  size?: 'sm' | 'md';
}

export function SeverityBadge({ severity, size = 'md' }: SeverityBadgeProps) {
  const severityConfig = {
    high: { variant: 'error' as const, label: 'High' },
    medium: { variant: 'warning' as const, label: 'Medium' },
    low: { variant: 'info' as const, label: 'Low' },
  };

  const config = severityConfig[severity];

  return (
    <Badge variant={config.variant} size={size}>
      {config.label}
    </Badge>
  );
}
