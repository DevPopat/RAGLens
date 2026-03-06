import { useState } from 'react';
import { Info, Search, Loader2, CheckCircle, XCircle } from 'lucide-react';
import type { EvaluationScores, DetailedAnalysisResponse } from '../../types';
import Modal from '../common/Modal';
import { getDetailedAnalysis } from '../../api/evaluation';
import {
  FaithfulnessBreakdown,
  QuestionCoverageBreakdown,
  ContextUtilizationBreakdown,
} from './DetailedAnalysis';

interface MetricDetail {
  key: string;
  label: string;
  description: string;
  getInterpretation: (score: number) => string;
}

const METRIC_DETAILS: MetricDetail[] = [
  {
    key: 'context_precision',
    label: 'Context Precision',
    description:
      'Measures whether the retrieved context chunks are relevant to the query. Evaluates if the higher-ranked context pieces are more relevant than lower-ranked ones.',
    getInterpretation: (score: number) => {
      if (score >= 0.8) return 'The retrieval system found highly relevant documents for this query.';
      if (score >= 0.6) return 'Most retrieved documents are relevant, but some less useful chunks were included.';
      if (score >= 0.4) return 'The retrieved context has mixed relevance. The retrieval query or parameters may need tuning.';
      return 'The retrieved documents are largely irrelevant to the query. Consider improving embeddings or retrieval strategy.';
    },
  },
  {
    key: 'context_recall',
    label: 'Context Recall',
    description:
      'Measures whether the retrieved context contains all the information needed to produce the expected answer. Only available when ground truth is provided.',
    getInterpretation: (score: number) => {
      if (score >= 0.8) return 'The retrieved context covers nearly all information needed for the expected answer.';
      if (score >= 0.6) return 'Most of the needed information was retrieved, but some key details are missing.';
      if (score >= 0.4) return 'Significant portions of the needed information were not retrieved.';
      return 'The retrieval system missed most of the information needed to answer correctly.';
    },
  },
  {
    key: 'faithfulness',
    label: 'Faithfulness',
    description:
      'Measures whether the generated answer is factually grounded in the retrieved context. Checks that the response does not hallucinate or add information not present in the sources.',
    getInterpretation: (score: number) => {
      if (score >= 0.8) return 'The response is well-grounded in the provided context with no hallucination.';
      if (score >= 0.6) return 'The response is mostly grounded but contains some statements not directly supported by context.';
      if (score >= 0.4) return 'The response contains notable unsupported claims. The generation prompt may need tightening.';
      return 'The response contains significant hallucinated content not present in the retrieved context.';
    },
  },
  {
    key: 'answer_relevancy',
    label: 'Answer Relevancy',
    description:
      'Pass/fail metric: an LLM judge directly evaluates whether the response answers the user\'s question. 1 = relevant, 0 = not relevant. For batch runs, the score is the fraction of cases that passed.',
    getInterpretation: (score: number) => {
      return score === 1
        ? 'The response directly and completely answers the user\'s question.'
        : 'The response does not adequately address the question that was asked.';
    },
  },
  {
    key: 'answer_correctness',
    label: 'Answer Correctness',
    description:
      'Measures how closely the generated answer matches the expected ground truth answer in terms of factual content. Only available when ground truth is provided.',
    getInterpretation: (score: number) => {
      if (score >= 0.8) return 'The generated answer closely matches the expected answer in factual content.';
      if (score >= 0.6) return 'The answer captures most key facts from the expected answer but misses some details.';
      if (score >= 0.4) return 'The answer has partial overlap with the expected answer but diverges on important points.';
      return 'The answer significantly differs from the expected ground truth.';
    },
  },
];

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.6) return 'text-yellow-600';
  if (score >= 0.4) return 'text-orange-600';
  return 'text-red-600';
}

function getScoreBg(score: number): string {
  if (score >= 0.8) return 'bg-green-50 border-green-200';
  if (score >= 0.6) return 'bg-yellow-50 border-yellow-200';
  if (score >= 0.4) return 'bg-orange-50 border-orange-200';
  return 'bg-red-50 border-red-200';
}

export interface AnalysisData {
  query: string;
  response: string;
  contexts: string[];
  message_type?: string;
}

interface ScoreDetailModalProps {
  scores: EvaluationScores;
  isOpen: boolean;
  onClose: () => void;
  analysisData?: AnalysisData;
}

export default function ScoreDetailModal({ scores, isOpen, onClose, analysisData }: ScoreDetailModalProps) {
  const [analysis, setAnalysis] = useState<DetailedAnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const availableMetrics = METRIC_DETAILS.filter(
    (m) => scores[m.key] !== undefined && scores[m.key] !== null
  );

  const handleLoadAnalysis = async () => {
    if (!analysisData) return;
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const result = await getDetailedAnalysis({
        query: analysisData.query,
        response: analysisData.response,
        contexts: analysisData.contexts,
        scores: Object.fromEntries(
          Object.entries(scores).filter(
            ([k, v]) => v != null && k !== 'overall_score'
          )
        ) as Record<string, number>,
        message_type: analysisData.message_type,
      });
      setAnalysis(result);
    } catch (err) {
      setAnalysisError(
        err instanceof Error ? err.message : 'Failed to load detailed analysis'
      );
    } finally {
      setAnalysisLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Score Details" size="lg">
      <div className="space-y-6">
        {/* Overall Score */}
        <div className={`rounded-lg border p-4 ${getScoreBg(scores.overall_score)}`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">Overall Score</h3>
              <p className="text-sm text-gray-600 mt-1">
                Weighted average of all individual metrics below.
              </p>
            </div>
            <div className="text-right">
              <p className={`text-2xl font-bold ${getScoreColor(scores.overall_score)}`}>
                {Math.round(scores.overall_score * 100)}%
              </p>
              <p className="text-xs text-gray-500">raw: {scores.overall_score.toFixed(4)}</p>
            </div>
          </div>
        </div>

        {/* Individual Metrics */}
        {availableMetrics.map((metric) => {
          const raw = scores[metric.key] as number;
          const pct = Math.round(raw * 100);

          // Get the detailed breakdown for this metric (if loaded)
          const metricAnalysis = analysis
            ? metric.key === 'faithfulness' ? analysis.faithfulness
            : metric.key === 'answer_relevancy' ? analysis.answer_relevancy
            : metric.key === 'context_precision' ? analysis.context_precision
            : null
            : null;

          return (
            <div key={metric.key} className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 pr-4">
                  <h4 className="font-medium text-gray-900">{metric.label}</h4>
                  <p className="text-xs text-gray-500 mt-1">{metric.description}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  {metric.key === 'answer_relevancy' ? (
                    raw === 1 ? (
                      <span className="inline-flex items-center gap-1 text-green-600 font-semibold text-sm">
                        <CheckCircle className="w-4 h-4" /> Relevant
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-600 font-semibold text-sm">
                        <XCircle className="w-4 h-4" /> Not Relevant
                      </span>
                    )
                  ) : (
                    <>
                      <p className={`text-xl font-bold ${getScoreColor(raw)}`}>{pct}%</p>
                      <p className="text-xs text-gray-500">raw: {raw.toFixed(4)}</p>
                    </>
                  )}
                </div>
              </div>

              {/* Show LLM summary if analysis loaded, otherwise show generic interpretation */}
              <div className="mt-3 bg-gray-50 rounded-md p-3">
                <p className="text-sm text-gray-700">
                  {metricAnalysis && 'summary' in metricAnalysis
                    ? metricAnalysis.summary
                    : metric.getInterpretation(raw)}
                </p>
              </div>

              {/* Detailed breakdown sections */}
              {analysis && metric.key === 'faithfulness' && analysis.faithfulness && (
                <FaithfulnessBreakdown detail={analysis.faithfulness} />
              )}
              {analysis && metric.key === 'answer_relevancy' && analysis.answer_relevancy && (
                <QuestionCoverageBreakdown detail={analysis.answer_relevancy} />
              )}
              {analysis && metric.key === 'context_precision' && analysis.context_precision && (
                <ContextUtilizationBreakdown detail={analysis.context_precision} />
              )}
            </div>
          );
        })}

        {availableMetrics.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">
            No individual metric scores available for this evaluation.
          </p>
        )}

        {/* Load Detailed Analysis button */}
        {analysisData && !analysis && (
          <div className="flex justify-center">
            <button
              onClick={handleLoadAnalysis}
              disabled={analysisLoading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 hover:bg-primary-50 border border-primary-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analysisLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Load Detailed Analysis
                </>
              )}
            </button>
          </div>
        )}
        {analysisError && (
          <p className="text-sm text-red-500 text-center">{analysisError}</p>
        )}
      </div>
    </Modal>
  );
}

interface ScoreDetailButtonProps {
  scores: EvaluationScores;
  size?: 'sm' | 'md';
  analysisData?: AnalysisData;
}

export function ScoreDetailButton({ scores, size = 'sm', analysisData }: ScoreDetailButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const sizeClasses = {
    sm: 'text-xs px-2 py-1 gap-1',
    md: 'text-sm px-3 py-1.5 gap-1.5',
  };

  return (
    <>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(true);
        }}
        className={`inline-flex items-center ${sizeClasses[size]} text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-md transition-colors`}
      >
        <Info className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} />
        More Details
      </button>
      <ScoreDetailModal
        scores={scores}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        analysisData={analysisData}
      />
    </>
  );
}
