import { useState } from 'react';
import { RefreshCw} from 'lucide-react';
import Card, { CardHeader } from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import { LoadingState } from '../components/common/Spinner';
import EvaluationList from '../components/evaluation/EvaluationList';
import { EvaluationDetailCard } from '../components/evaluation/EvaluationCard';
import { ScoreBreakdown } from '../components/evaluation/ScoreDisplay';
import useEvaluations from '../hooks/useEvaluations';
import type { EvaluationResponse } from '../types';

export default function EvaluationsPage() {
  const {
    evaluations,
    total,
    isLoading,
    error,
    selectedEvaluation,
    fetchEvaluations,
    fetchEvaluation,
    clearSelection,
  } = useEvaluations();

  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 20;

  const handleSelect = (evaluation: EvaluationResponse) => {
    fetchEvaluation(evaluation.id);
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    fetchEvaluations(newPage * pageSize, pageSize);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Evaluations</h1>
          <p className="text-gray-500 mt-1">
            View and analyze RAGAS evaluation results for your queries
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => fetchEvaluations(currentPage * pageSize, pageSize)}
          leftIcon={<RefreshCw className="w-4 h-4" />}
          isLoading={isLoading}
        >
          Refresh
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
          {error}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900">{total}</p>
            <p className="text-sm text-gray-500">Total Evaluations</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-green-600">
              {evaluations.filter((e) => e.scores.overall_score >= 0.8).length}
            </p>
            <p className="text-sm text-gray-500">High Scores (≥80%)</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-red-600">
              {evaluations.filter((e) => e.scores.overall_score < 0.6).length}
            </p>
            <p className="text-sm text-gray-500">Low Scores (&lt;60%)</p>
          </div>
        </Card>
      </div>

      {/* Evaluations List */}
      <Card>
        <CardHeader
          title="Recent Evaluations"
          subtitle={`Showing ${evaluations.length} of ${total} evaluations`}
        />
        {isLoading && evaluations.length === 0 ? (
          <LoadingState message="Loading evaluations..." />
        ) : (
          <>
            <EvaluationList evaluations={evaluations} onSelect={handleSelect} />

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  Page {currentPage + 1} of {totalPages}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage >= totalPages - 1}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Detail Modal */}
      <Modal
        isOpen={!!selectedEvaluation}
        onClose={clearSelection}
        title="Evaluation Details"
        size="lg"
        footer={
          <Button variant="secondary" onClick={clearSelection}>
            Close
          </Button>
        }
      >
        {selectedEvaluation && (
          <div className="space-y-6">
            <EvaluationDetailCard evaluation={selectedEvaluation} />
            <div className="border-t pt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-4">Score Breakdown</h4>
              <ScoreBreakdown scores={selectedEvaluation.scores} />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
