import { FileQuestion } from 'lucide-react';
import type { EvaluationResponse } from '../../types';
import EvaluationCard from './EvaluationCard';

interface EvaluationListProps {
  evaluations: EvaluationResponse[];
  onSelect?: (evaluation: EvaluationResponse) => void;
}

export default function EvaluationList({ evaluations, onSelect }: EvaluationListProps) {
  if (evaluations.length === 0) {
    return (
      <div className="text-center py-12">
        <FileQuestion className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No evaluations yet</h3>
        <p className="text-gray-500">
          Evaluations will appear here after you run queries through the chat.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {evaluations.map((evaluation) => (
        <EvaluationCard
          key={evaluation.id}
          evaluation={evaluation}
          onClick={onSelect ? () => onSelect(evaluation) : undefined}
        />
      ))}
    </div>
  );
}
