import type { EvaluationScores } from '../../types';
import ScoreBar, { ScoreCircle } from '../common/ScoreBar';

interface ScoreDisplayProps {
  scores: EvaluationScores;
  layout?: 'horizontal' | 'vertical' | 'compact';
}

export default function ScoreDisplay({ scores, layout = 'vertical' }: ScoreDisplayProps) {
  const metricLabels: Record<string, string> = {
    context_precision: 'Context Precision',
    faithfulness: 'Faithfulness',
    answer_relevancy: 'Answer Relevancy',
    overall_score: 'Overall Score',
  };

  const displayMetrics = Object.entries(scores)
    .filter(([key, value]) => value !== undefined && key !== 'overall_score')
    .map(([key, value]) => ({
      key,
      label: metricLabels[key] || key.replace(/_/g, ' '),
      value: value as number,
    }));

  if (layout === 'compact') {
    return (
      <div className="flex items-center gap-4">
        <ScoreCircle score={scores.overall_score} size="sm" showLabel={false} />
        <div className="text-sm text-gray-600">
          Overall: {Math.round(scores.overall_score * 100)}%
        </div>
      </div>
    );
  }

  if (layout === 'horizontal') {
    return (
      <div className="flex items-center gap-6">
        <ScoreCircle score={scores.overall_score} size="md" />
        <div className="flex-1 grid grid-cols-3 gap-4">
          {displayMetrics.map((metric) => (
            <ScoreBar
              key={metric.key}
              score={metric.value}
              label={metric.label}
              size="sm"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center">
        <ScoreCircle score={scores.overall_score} size="lg" />
      </div>
      <div className="space-y-3">
        {displayMetrics.map((metric) => (
          <ScoreBar key={metric.key} score={metric.value} label={metric.label} size="md" />
        ))}
      </div>
    </div>
  );
}

interface ScoreBreakdownProps {
  scores: EvaluationScores;
}

export function ScoreBreakdown({ scores }: ScoreBreakdownProps) {
  const metrics = [
    {
      key: 'context_precision',
      label: 'Context Precision',
      description: 'How relevant are the retrieved documents?',
    },
    {
      key: 'faithfulness',
      label: 'Faithfulness',
      description: 'Is the response grounded in the context?',
    },
    {
      key: 'answer_relevancy',
      label: 'Answer Relevancy',
      description: 'Does the answer address the question?',
    },
  ];

  return (
    <div className="space-y-4">
      {metrics.map((metric) => {
        const score = scores[metric.key as keyof EvaluationScores];
        if (score === undefined) return null;

        return (
          <div key={metric.key} className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h4 className="font-medium text-gray-900">{metric.label}</h4>
                <p className="text-xs text-gray-500">{metric.description}</p>
              </div>
              <span className="text-lg font-bold text-gray-900">
                {Math.round(score * 100)}%
              </span>
            </div>
            <ScoreBar score={score} showPercentage={false} size="md" />
          </div>
        );
      })}
    </div>
  );
}
