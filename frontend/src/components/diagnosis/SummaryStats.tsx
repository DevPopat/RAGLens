import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import type { DiagnosisSummary } from '../../types';
import Card from '../common/Card';
import { ScoreCircle } from '../common/ScoreBar';

interface SummaryStatsProps {
  summary: DiagnosisSummary;
}

export default function SummaryStats({ summary }: SummaryStatsProps) {
  const stats = [
    {
      label: 'Total Evaluations',
      value: summary.total_evaluations,
      icon: Activity,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'High Scores (>80%)',
      value: summary.high_score_count,
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
    },
    {
      label: 'Low Scores (<60%)',
      value: summary.low_score_count,
      icon: TrendingDown,
      color: 'text-red-500',
      bgColor: 'bg-red-50',
    },
    {
      label: 'Active Alerts',
      value: summary.alerts.length,
      icon: AlertTriangle,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* Average Score Card */}
      <Card className="flex items-center justify-center">
        <div className="text-center">
          <ScoreCircle score={summary.avg_score} size="lg" />
          <p className="text-sm text-gray-500 mt-2">Average Score</p>
        </div>
      </Card>

      {/* Stat Cards */}
      {stats.map((stat) => (
        <Card key={stat.label}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${stat.bgColor}`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

export function StatCard({ label, value, icon: Icon, trend, trendValue }: StatCardProps) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {trend && trendValue && (
            <div className="flex items-center gap-1 mt-2">
              {trend === 'up' ? (
                <TrendingUp className="w-4 h-4 text-green-500" />
              ) : trend === 'down' ? (
                <TrendingDown className="w-4 h-4 text-red-500" />
              ) : null}
              <span
                className={`text-sm ${
                  trend === 'up'
                    ? 'text-green-600'
                    : trend === 'down'
                    ? 'text-red-600'
                    : 'text-gray-500'
                }`}
              >
                {trendValue}
              </span>
            </div>
          )}
        </div>
        <div className="p-3 bg-gray-100 rounded-lg">
          <Icon className="w-6 h-6 text-gray-600" />
        </div>
      </div>
    </Card>
  );
}
