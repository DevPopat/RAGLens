import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import type { Alert } from '../../types';
import { SeverityBadge } from '../common/Badge';

interface AlertCardProps {
  alert: Alert;
}

export default function AlertCard({ alert }: AlertCardProps) {
  const icons = {
    high: AlertTriangle,
    medium: AlertCircle,
    low: Info,
  };

  const colors = {
    high: 'border-red-200 bg-red-50',
    medium: 'border-yellow-200 bg-yellow-50',
    low: 'border-blue-200 bg-blue-50',
  };

  const iconColors = {
    high: 'text-red-500',
    medium: 'text-yellow-500',
    low: 'text-blue-500',
  };

  const Icon = icons[alert.severity];

  return (
    <div className={`rounded-lg border p-4 ${colors[alert.severity]}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${iconColors[alert.severity]}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-gray-900 text-sm">{alert.type}</span>
            <SeverityBadge severity={alert.severity} size="sm" />
          </div>
          <p className="text-sm text-gray-600">{alert.message}</p>
          {alert.affected_count > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Affected: {alert.affected_count} item{alert.affected_count !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

interface AlertListProps {
  alerts: Alert[];
  maxItems?: number;
}

export function AlertList({ alerts, maxItems }: AlertListProps) {
  const displayAlerts = maxItems ? alerts.slice(0, maxItems) : alerts;

  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No active alerts</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {displayAlerts.map((alert, index) => (
        <AlertCard key={index} alert={alert} />
      ))}
      {maxItems && alerts.length > maxItems && (
        <p className="text-sm text-gray-500 text-center">
          +{alerts.length - maxItems} more alerts
        </p>
      )}
    </div>
  );
}
