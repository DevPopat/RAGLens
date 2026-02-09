interface ScoreBarProps {
  score: number;
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function ScoreBar({
  score,
  label,
  showPercentage = true,
  size = 'md',
  className = '',
}: ScoreBarProps) {
  const percentage = Math.round(score * 100);

  const getColorClass = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    if (score >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const sizes = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className={className}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between mb-1">
          {label && <span className="text-sm text-gray-600">{label}</span>}
          {showPercentage && (
            <span className="text-sm font-medium text-gray-900">{percentage}%</span>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full ${sizes[size]}`}>
        <div
          className={`${sizes[size]} rounded-full transition-all duration-300 ${getColorClass(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

interface ScoreDisplayProps {
  score: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showLabel?: boolean;
}

export function ScoreCircle({ score, size = 'md', showLabel = true }: ScoreDisplayProps) {
  const percentage = Math.round(score * 100);

  const getColorClass = (score: number) => {
    if (score >= 0.8) return 'text-green-500';
    if (score >= 0.6) return 'text-yellow-500';
    if (score >= 0.4) return 'text-orange-500';
    return 'text-red-500';
  };

  const sizes = {
    sm: 'w-12 h-12 text-sm',
    md: 'w-16 h-16 text-lg',
    lg: 'w-20 h-20 text-xl',
    xl: 'w-24 h-24 text-2xl',
  };

  return (
    <div className="flex flex-col items-center">
      <div
        className={`${sizes[size]} rounded-full border-4 flex items-center justify-center font-bold ${getColorClass(score)}`}
        style={{ borderColor: 'currentColor' }}
      >
        {percentage}
      </div>
      {showLabel && <span className="text-xs text-gray-500 mt-1">Score</span>}
    </div>
  );
}
