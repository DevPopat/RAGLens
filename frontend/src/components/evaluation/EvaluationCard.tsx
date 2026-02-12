import { Clock, Cpu } from 'lucide-react';
import type { EvaluationResponse } from '../../types';
import Card from '../common/Card';
import Badge from '../common/Badge';
import ScoreDisplay from './ScoreDisplay';

interface EvaluationCardProps {
  evaluation: EvaluationResponse;
  onClick?: () => void;
}

export default function EvaluationCard({ evaluation, onClick }: EvaluationCardProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <Card hover={!!onClick} onClick={onClick} className="transition-all">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="info">{evaluation.evaluation_type}</Badge>
            {evaluation.metadata?.has_ground_truth && (
              <Badge variant="success">Has Ground Truth</Badge>
            )}
          </div>
          <p className="text-sm text-gray-500 truncate mb-3">
            Query ID: {evaluation.query_id}
          </p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDate(evaluation.timestamp)}
            </span>
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3" />
              {evaluation.evaluator}
            </span>
          </div>
        </div>
        <div className="flex-shrink-0 ml-4">
          <ScoreDisplay scores={evaluation.scores} layout="compact" />
        </div>
      </div>
    </Card>
  );
}

interface EvaluationDetailCardProps {
  evaluation: EvaluationResponse;
}

export function EvaluationDetailCard({ evaluation }: EvaluationDetailCardProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="info" size="md">
              {evaluation.evaluation_type.toUpperCase()}
            </Badge>
            {evaluation.metadata?.has_ground_truth && (
              <Badge variant="success" size="md">
                Ground Truth Available
              </Badge>
            )}
          </div>
          <p className="text-sm text-gray-500">
            Evaluation ID: {evaluation.id}
          </p>
          <p className="text-sm text-gray-500">Query ID: {evaluation.query_id}</p>
        </div>
        <div className="text-right text-sm text-gray-500">
          <p>{formatDate(evaluation.timestamp)}</p>
          <p className="mt-1">{evaluation.evaluator}</p>
        </div>
      </div>

      {/* Scores */}
      <ScoreDisplay scores={evaluation.scores} layout="horizontal" />

      {/* Metadata */}
      {(evaluation.metadata?.expected_category || evaluation.metadata?.expected_intent) && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Expected Values</h4>
          <div className="flex gap-4">
            {evaluation.metadata?.expected_category && (
              <div>
                <span className="text-xs text-gray-500">Category:</span>
                <span className="ml-2 text-sm text-gray-900">
                  {evaluation.metadata?.expected_category}
                </span>
              </div>
            )}
            {evaluation.metadata?.expected_intent && (
              <div>
                <span className="text-xs text-gray-500">Intent:</span>
                <span className="ml-2 text-sm text-gray-900">
                  {evaluation.metadata?.expected_intent}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Metrics Used */}
      {evaluation.metadata?.metrics_used && evaluation.metadata.metrics_used.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Metrics Evaluated</h4>
          <div className="flex flex-wrap gap-2">
            {evaluation.metadata.metrics_used.map((metric) => (
              <Badge key={metric} variant="default">
                {metric}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
