import { useState } from 'react';
import { FileText, ChevronRight, ChevronDown, ChevronUp, Activity, RefreshCw, Clock } from 'lucide-react';
import type { Source, EvaluationResult } from '../../types';
import ScoreBar from '../common/ScoreBar';
import Button from '../common/Button';
import { ScoreDetailButton } from '../evaluation/ScoreDetailModal';

interface SourcesPanelProps {
  sources: Source[];
  isExpanded: boolean;
  onToggle: () => void;
  evaluation?: EvaluationResult;
  isEvaluating?: boolean;
  onRunEvaluation?: () => void;
  selectedSources: Set<number>;
  onToggleSource: (idx: number) => void;
  onToggleAllSources: () => void;
}

export default function SourcesPanel({
  sources,
  isExpanded,
  onToggle,
  evaluation,
  isEvaluating,
  onRunEvaluation,
  selectedSources,
  onToggleSource,
  onToggleAllSources,
}: SourcesPanelProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div
      className={`border-l border-gray-200 bg-gray-50 transition-all duration-300 ${
        isExpanded ? 'w-80' : 'w-12'
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-center text-gray-500 hover:bg-gray-100 border-b border-gray-200"
      >
        <ChevronRight
          className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {isExpanded && (
        <div className="p-4 overflow-y-auto h-[calc(100%-48px)]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Retrieved Sources ({sources.length})
            </h3>
            <button
              onClick={onToggleAllSources}
              className={`text-xs font-medium ${
                selectedSources.size === sources.length
                  ? 'text-amber-600 hover:text-amber-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {selectedSources.size === sources.length ? 'Deselect All' : 'Highlight All'}
            </button>
          </div>
          <div className="space-y-3">
            {sources.map((source, index) => (
              <SourceCard
                key={source.id || `source-${index}`}
                source={source}
                index={index}
                isSelected={selectedSources.has(index)}
                onToggle={() => onToggleSource(index)}
              />
            ))}
          </div>

          {/* Evaluation Section */}
          {onRunEvaluation && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                RAGAS Evaluation
              </h3>

              {evaluation ? (
                <div className="space-y-3">
                  {evaluation.scores.overall_score != null && (
                    <ScoreBar
                      score={evaluation.scores.overall_score}
                      label="Overall Score"
                      size="md"
                    />
                  )}
                  {evaluation.scores.context_precision != null && (
                    <ScoreBar
                      score={evaluation.scores.context_precision}
                      label="Context Precision"
                      size="sm"
                    />
                  )}
                  {evaluation.scores.faithfulness != null && (
                    <ScoreBar
                      score={evaluation.scores.faithfulness}
                      label="Faithfulness"
                      size="sm"
                    />
                  )}
                  {evaluation.scores.answer_relevancy != null && (
                    <ScoreBar
                      score={evaluation.scores.answer_relevancy}
                      label="Answer Relevancy"
                      size="sm"
                    />
                  )}
                  <div className="flex items-center gap-2">
                    <ScoreDetailButton scores={evaluation.scores} size="sm" />
                    {evaluation.latency_ms != null && (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <Clock className="w-3 h-3" />
                        {Math.round(evaluation.latency_ms / 1000)}s
                      </span>
                    )}
                  </div>
                  {evaluation.metadata?.has_conversation_context && (
                    <p className="text-xs text-gray-400">
                      Evaluated with conversation context
                    </p>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onRunEvaluation}
                    isLoading={isEvaluating}
                    leftIcon={<RefreshCw className="w-3 h-3" />}
                  >
                    Re-evaluate
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRunEvaluation}
                  isLoading={isEvaluating}
                  leftIcon={<Activity className="w-4 h-4" />}
                  className="w-full"
                >
                  Run Evaluation
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface SourceCardProps {
  source: Source;
  index: number;
  isSelected: boolean;
  onToggle: () => void;
}

function SourceCard({ source, index, isSelected, onToggle }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      onClick={onToggle}
      className={`rounded-lg border p-3 text-sm cursor-pointer transition-colors ${
        isSelected
          ? 'bg-amber-50 border-amber-400'
          : 'bg-white border-gray-200 hover:border-gray-300'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className={`font-medium ${isSelected ? 'text-amber-700' : 'text-gray-700'}`}>Source {index + 1}</span>
        <div className="flex items-center gap-2">
          <ScoreBar score={source.score} size="sm" showPercentage={true} className="w-20" />
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="p-0.5 text-gray-400 hover:text-gray-600"
            title={expanded ? 'Show less' : 'Show more'}
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
      <p className={`text-gray-600 text-xs ${expanded ? '' : 'line-clamp-4'}`}>{source.text}</p>
      {source.metadata && Object.keys(source.metadata).length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <div className="flex flex-wrap gap-1">
            {expanded
              ? Object.entries(source.metadata).map(([key, value]) => (
                  <span
                    key={key}
                    className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                  >
                    {key}: {String(value)}
                  </span>
                ))
              : <>
                  {source.metadata.category != null && (
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">
                      {String(source.metadata.category)}
                    </span>
                  )}
                  {source.metadata.intent != null && (
                    <span className="px-2 py-0.5 bg-purple-50 text-purple-600 rounded text-xs">
                      {String(source.metadata.intent)}
                    </span>
                  )}
                </>
            }
          </div>
        </div>
      )}
    </div>
  );
}
