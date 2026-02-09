import { CheckCircle, XCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { EvaluationRun, TestCaseResult } from '../../types';
import Card, { CardHeader } from '../common/Card';
import { StatusBadge } from '../common/Badge';
import ScoreBar, { ScoreCircle } from '../common/ScoreBar';

interface RunResultsTableProps {
  run: EvaluationRun;
}

export default function RunResultsTable({ run }: RunResultsTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  if (!run.results_json) {
    return (
      <Card>
        <div className="text-center py-8">
          <Clock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">Results not yet available</p>
          <StatusBadge status={run.status} />
        </div>
      </Card>
    );
  }

  const { results, summary } = run.results_json;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader title="Run Summary" subtitle={run.config_snapshot.run_name || 'Evaluation Run'} />
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center">
            <ScoreCircle score={summary.avg_score} size="md" />
            <p className="text-xs text-gray-500 mt-1">Avg Score</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{summary.total_cases}</p>
            <p className="text-xs text-gray-500">Total Cases</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{summary.completed}</p>
            <p className="text-xs text-gray-500">Completed</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600">{summary.failed}</p>
            <p className="text-xs text-gray-500">Failed</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-primary-600">
              {Math.round(summary.pass_rate * 100)}%
            </p>
            <p className="text-xs text-gray-500">Pass Rate</p>
          </div>
        </div>
      </Card>

      {/* Results Table */}
      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  #
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Query
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Score
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase w-10">
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {results.map((result, index) => (
                <ResultRow
                  key={result.test_case_id}
                  result={result}
                  index={index}
                  isExpanded={expandedRows.has(result.test_case_id)}
                  onToggle={() => toggleRow(result.test_case_id)}
                />
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

interface ResultRowProps {
  result: TestCaseResult;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function ResultRow({ result, index, isExpanded, onToggle }: ResultRowProps) {
  return (
    <>
      <tr className="hover:bg-gray-50 cursor-pointer" onClick={onToggle}>
        <td className="px-4 py-3 text-sm text-gray-500">{index + 1}</td>
        <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
          {result.query}
        </td>
        <td className="px-4 py-3">
          {result.status === 'success' ? (
            <span className="flex items-center gap-1 text-green-600 text-sm">
              <CheckCircle className="w-4 h-4" />
              Success
            </span>
          ) : (
            <span className="flex items-center gap-1 text-red-600 text-sm">
              <XCircle className="w-4 h-4" />
              Error
            </span>
          )}
        </td>
        <td className="px-4 py-3">
          <ScoreBar score={result.overall_score} size="sm" className="w-24" />
        </td>
        <td className="px-4 py-3">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={5} className="px-4 py-4 bg-gray-50">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Expected Answer</p>
                  <p className="text-sm text-gray-700 bg-white p-3 rounded border">
                    {result.expected_answer}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Generated Answer</p>
                  <p className="text-sm text-gray-700 bg-white p-3 rounded border">
                    {result.generated_answer}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Score Breakdown</p>
                <div className="grid grid-cols-3 gap-4">
                  {result.scores.context_precision !== undefined && (
                    <ScoreBar
                      score={result.scores.context_precision}
                      label="Context Precision"
                      size="sm"
                    />
                  )}
                  {result.scores.faithfulness !== undefined && (
                    <ScoreBar
                      score={result.scores.faithfulness}
                      label="Faithfulness"
                      size="sm"
                    />
                  )}
                  {result.scores.answer_relevancy !== undefined && (
                    <ScoreBar
                      score={result.scores.answer_relevancy}
                      label="Answer Relevancy"
                      size="sm"
                    />
                  )}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
