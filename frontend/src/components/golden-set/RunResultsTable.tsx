import { CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, AlertTriangle, Minus, Loader2, RefreshCw, FileText } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { EvaluationRun, TestCaseResult, Claim } from '../../types';
import { compareClaims } from '../../api/evaluation';
import Card, { CardHeader } from '../common/Card';
import SourceHighlightedText from '../common/SourceHighlightedText';
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

  if (!run.results_json || !run.results_json.results || !run.results_json.summary) {
    const errorMessage = run.results_json && 'error' in run.results_json
      ? String((run.results_json as Record<string, unknown>).error)
      : null;

    return (
      <Card>
        <div className="text-center py-8">
          <Clock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">
            {errorMessage
              ? `Run failed: ${errorMessage}`
              : 'Results not yet available'}
          </p>
          <StatusBadge status={run.status} />
        </div>
      </Card>
    );
  }

  const { results, summary } = run.results_json;

  const sortedResults = useMemo(() => {
    return [...results].sort((a, b) => {
      // Errors first
      if (a.status === 'error' && b.status !== 'error') return -1;
      if (a.status !== 'error' && b.status === 'error') return 1;
      // Then by score ascending (lowest first)
      return (a.overall_score ?? 0) - (b.overall_score ?? 0);
    });
  }, [results]);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader title="Run Summary" subtitle={run.config_snapshot.run_name || 'Evaluation Run'} />
        <div className="flex flex-wrap gap-3 mb-4">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-medium">
            Generator: {run.config_snapshot.llm_provider}
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-purple-50 text-purple-700 rounded-md text-xs font-medium">
            Evaluator: {run.config_snapshot.evaluator_provider}
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-600 rounded-md text-xs font-medium">
            Top K: {run.config_snapshot.top_k}
          </span>
        </div>
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
              {sortedResults.map((result, index) => (
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

const METRIC_EXPLANATIONS: Record<string, string> = {
  context_precision: 'Are the retrieved documents relevant to the query?',
  faithfulness: 'Is the response grounded in the retrieved context, without hallucination?',
  answer_relevancy: 'Does the response actually address what was asked?',
  answer_correctness: 'Does the generated answer match the expected answer?',
  context_recall: 'Does the retrieved context cover what\'s needed to answer?',
};

interface ResultRowProps {
  result: TestCaseResult;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function HighlightedText({ text, claims }: { text: string; claims: Claim[] }) {
  const quotes = claims
    .filter((c) => c.generated_quote && text.includes(c.generated_quote))
    .map((c) => ({ quote: c.generated_quote!, status: c.status }));

  if (quotes.length === 0) return <>{text}</>;

  // Build segments: find all quote positions, sort by position, fill gaps with plain text
  const positions: { start: number; end: number; status: string }[] = [];
  for (const q of quotes) {
    const idx = text.indexOf(q.quote);
    if (idx !== -1) {
      positions.push({ start: idx, end: idx + q.quote.length, status: q.status });
    }
  }
  positions.sort((a, b) => a.start - b.start);

  // Remove overlaps (keep first match)
  const merged: typeof positions = [];
  for (const pos of positions) {
    if (merged.length === 0 || pos.start >= merged[merged.length - 1].end) {
      merged.push(pos);
    }
  }

  const segments: React.ReactNode[] = [];
  let cursor = 0;
  for (const pos of merged) {
    if (cursor < pos.start) {
      segments.push(<span key={`t-${cursor}`}>{text.slice(cursor, pos.start)}</span>);
    }
    const bgColor = pos.status === 'covered'
      ? 'bg-green-100 border-b-2 border-green-400'
      : 'bg-red-100 border-b-2 border-red-400';
    segments.push(
      <mark key={`h-${pos.start}`} className={`${bgColor} rounded px-0.5`} title={pos.status}>
        {text.slice(pos.start, pos.end)}
      </mark>
    );
    cursor = pos.end;
  }
  if (cursor < text.length) {
    segments.push(<span key={`t-${cursor}`}>{text.slice(cursor)}</span>);
  }

  return <>{segments}</>;
}

const CLAIM_STATUS_CONFIG = {
  covered: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', label: 'Covered' },
  missing: { icon: Minus, color: 'text-gray-500', bg: 'bg-gray-50', label: 'Missing' },
  contradicted: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50', label: 'Contradicted' },
} as const;

function ResultRow({ result, index, isExpanded, onToggle }: ResultRowProps) {
  const [claims, setClaims] = useState<Claim[] | null>(null);
  const [showClaims, setShowClaims] = useState(false);
  const [claimsLoading, setClaimsLoading] = useState(false);
  const [claimsError, setClaimsError] = useState<string | null>(null);
  const [showSources, setShowSources] = useState(false);
  const [selectedSources, setSelectedSources] = useState<Set<number>>(new Set());

  const toggleSource = (idx: number) => {
    setSelectedSources((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const toggleAllSources = () => {
    if (!result.sources) return;
    setSelectedSources((prev) =>
      prev.size === result.sources!.length
        ? new Set()
        : new Set(result.sources!.map((_, i) => i))
    );
  };

  const fetchClaims = async () => {
    setClaimsLoading(true);
    setClaimsError(null);
    try {
      const response = await compareClaims(result.expected_answer, result.generated_answer);
      setClaims(response.claims);
      setShowClaims(true);
    } catch (err) {
      setClaimsError(err instanceof Error ? err.message : 'Failed to compare claims');
    } finally {
      setClaimsLoading(false);
    }
  };

  const handleCompareClaims = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (claims) {
      setShowClaims((prev) => !prev);
      return;
    }
    await fetchClaims();
  };

  const handleReanalyze = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setClaims(null);
    await fetchClaims();
  };

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
                    {showClaims && claims
                      ? <HighlightedText text={result.generated_answer} claims={claims} />
                      : selectedSources.size > 0 && result.sources?.length
                        ? <SourceHighlightedText text={result.generated_answer} sources={result.sources} selectedIndices={selectedSources} />
                        : result.generated_answer
                    }
                  </p>
                </div>
              </div>

              {/* Action Buttons Row */}
              <div className="flex items-center gap-3 flex-wrap">
                {result.expected_answer && result.generated_answer && (
                  <>
                    <button
                      onClick={handleCompareClaims}
                      disabled={claimsLoading}
                      className="text-xs font-medium text-primary-600 hover:text-primary-700 disabled:text-gray-400 flex items-center gap-1"
                    >
                      {claimsLoading && <Loader2 className="w-3 h-3 animate-spin" />}
                      {showClaims ? 'Hide Claim Analysis' : 'Compare Claims'}
                    </button>
                    {showClaims && claims && (
                      <button
                        onClick={handleReanalyze}
                        disabled={claimsLoading}
                        className="text-xs font-medium text-gray-500 hover:text-gray-700 disabled:text-gray-400 flex items-center gap-1"
                      >
                        <RefreshCw className="w-3 h-3" />
                        Re-analyze
                      </button>
                    )}
                  </>
                )}
                {result.sources && result.sources.length > 0 && (
                  <>
                    {result.expected_answer && result.generated_answer && (
                      <span className="text-gray-300">|</span>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowSources((prev) => {
                          if (!prev) return true;
                          setSelectedSources(new Set());
                          return false;
                        });
                      }}
                      className="text-xs font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1"
                    >
                      <FileText className="w-3 h-3" />
                      {showSources
                        ? 'Hide Retrieved Sources'
                        : `Show Retrieved Sources (${result.sources.length})`
                      }
                    </button>
                    {showSources && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleAllSources();
                        }}
                        className={`text-xs font-medium flex items-center gap-1 ${
                          selectedSources.size === result.sources.length
                            ? 'text-amber-600 hover:text-amber-700'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {selectedSources.size === result.sources.length ? 'Deselect All' : 'Highlight All'}
                      </button>
                    )}
                  </>
                )}
              </div>

              {/* Claims Expanded Content */}
              {result.expected_answer && result.generated_answer && (
                <>
                  {claimsError && (
                    <p className="text-xs text-red-500">{claimsError}</p>
                  )}
                  {showClaims && claims && (
                    <div className="space-y-1.5">
                      {claims.map((claim, i) => {
                        const config = CLAIM_STATUS_CONFIG[claim.status as keyof typeof CLAIM_STATUS_CONFIG]
                          ?? CLAIM_STATUS_CONFIG.missing;
                        const Icon = config.icon;
                        return (
                          <div key={i} className={`flex items-start gap-2 p-2 rounded ${config.bg}`}>
                            <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.color}`} />
                            <div className="min-w-0">
                              <p className="text-sm text-gray-800">{claim.claim}</p>
                              <p className="text-xs text-gray-500">{claim.detail}</p>
                            </div>
                            <span className={`text-xs font-medium ml-auto flex-shrink-0 ${config.color}`}>
                              {config.label}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
              )}

              {/* Sources Expanded Content */}
              {showSources && result.sources && result.sources.length > 0 && (
                <div className="space-y-2">
                  {result.sources.map((source, i) => {
                    const isSelected = selectedSources.has(i);
                    return (
                      <div
                        key={source.id || `src-${i}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSource(i);
                        }}
                        className={`rounded border p-3 cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-amber-50 border-amber-400'
                            : 'bg-white border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-xs font-medium ${isSelected ? 'text-amber-700' : 'text-gray-700'}`}>
                            Source {i + 1}
                          </span>
                          <ScoreBar score={source.score} size="sm" className="w-20" />
                        </div>
                        <p className="text-xs text-gray-600 whitespace-pre-wrap">
                          {source.text}
                        </p>
                        {source.metadata && (
                          <div className="flex flex-wrap gap-1 mt-2">
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
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Score Breakdown</p>
                <div className="grid grid-cols-3 gap-4">
                  {result.scores.context_precision != null && (
                    <div>
                      <ScoreBar
                        score={result.scores.context_precision}
                        label="Context Precision"
                        size="sm"
                      />
                      <p className="text-xs text-gray-400 mt-1">{METRIC_EXPLANATIONS.context_precision}</p>
                    </div>
                  )}
                  {result.scores.faithfulness != null && (
                    <div>
                      <ScoreBar
                        score={result.scores.faithfulness}
                        label="Faithfulness"
                        size="sm"
                      />
                      <p className="text-xs text-gray-400 mt-1">{METRIC_EXPLANATIONS.faithfulness}</p>
                    </div>
                  )}
                  {result.scores.answer_relevancy != null && (
                    <div>
                      <ScoreBar
                        score={result.scores.answer_relevancy}
                        label="Answer Relevancy"
                        size="sm"
                      />
                      <p className="text-xs text-gray-400 mt-1">{METRIC_EXPLANATIONS.answer_relevancy}</p>
                    </div>
                  )}
                  {result.scores.context_recall != null && (
                    <div>
                      <ScoreBar
                        score={result.scores.context_recall}
                        label="Context Recall"
                        size="sm"
                      />
                      <p className="text-xs text-gray-400 mt-1">{METRIC_EXPLANATIONS.context_recall}</p>
                    </div>
                  )}
                  {result.scores.answer_correctness != null && (
                    <div>
                      <ScoreBar
                        score={result.scores.answer_correctness}
                        label="Answer Correctness"
                        size="sm"
                      />
                      <p className="text-xs text-gray-400 mt-1">{METRIC_EXPLANATIONS.answer_correctness}</p>
                    </div>
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
