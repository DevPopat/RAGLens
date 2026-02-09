// Chat Types
export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface Source {
  id: string;
  text: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatRequest {
  query: string;
  llm_provider?: 'anthropic' | 'openai';
  top_k?: number;
  filter_category?: string;
  filter_intent?: string;
  conversation_history?: Message[];
}

export interface ChatResponse {
  query_id: string;
  query: string;
  response: string;
  sources: Source[];
  llm_provider: string;
  model: string;
  token_usage: TokenUsage;
  latency_ms: number;
  cost: number;
  message_type: 'question' | 'follow_up' | 'acknowledgment' | 'closure' | 'greeting';
}

// Evaluation Types
export interface EvaluationScores {
  context_precision?: number;
  faithfulness?: number;
  answer_relevancy?: number;
  overall_score: number;
  [key: string]: number | undefined;
}

export interface EvaluationRequest {
  query_id: string;
  evaluator_provider?: 'anthropic' | 'openai';
  expected_category?: string;
  expected_intent?: string;
}

export interface EvaluationResponse {
  id: string;
  query_id: string;
  evaluation_type: string;
  scores: EvaluationScores;
  evaluator: string;
  metadata: {
    expected_category?: string;
    expected_intent?: string;
    has_ground_truth?: boolean;
    metrics_used?: string[];
  };
  timestamp: string;
}

export interface EvaluationListResponse {
  evaluations: EvaluationResponse[];
  total: number;
  skip: number;
  limit: number;
}

export interface BatchEvaluationRequest {
  query_ids: string[];
  batch_name?: string;
  evaluator_provider?: 'anthropic' | 'openai';
}

export interface BatchEvaluationResponse {
  batch_name: string;
  total_queries: number;
  successful: number;
  failed: number;
  results: Array<{
    query_id: string;
    overall_score: number;
    status: 'success' | 'error';
  }>;
  errors: Array<{
    query_id: string;
    error: string;
  }>;
  summary: {
    total_evaluated: number;
    total_errors: number;
    avg_score: number;
    min_score: number;
    max_score: number;
  };
}

// Golden Set Types
export interface TestCase {
  id: string;
  test_set_id: string;
  query: string;
  expected_answer: string;
  category?: string;
  intent?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface TestCaseCreate {
  query: string;
  expected_answer: string;
  category?: string;
  intent?: string;
  metadata?: Record<string, unknown>;
}

export interface TestCaseUpdate {
  query?: string;
  expected_answer?: string;
  category?: string;
  intent?: string;
  metadata?: Record<string, unknown>;
}

export interface GoldenSet {
  id: string;
  name: string;
  description?: string;
  version: number;
  created_at: string;
  updated_at: string;
  test_case_count: number;
}

export interface GoldenSetDetail extends Omit<GoldenSet, 'test_case_count'> {
  test_cases: TestCase[];
}

export interface GoldenSetCreate {
  name: string;
  description?: string;
}

export interface GoldenSetUpdate {
  name?: string;
  description?: string;
}

export interface GoldenSetListResponse {
  golden_sets: GoldenSet[];
  total: number;
  skip: number;
  limit: number;
}

export interface RunTestSetRequest {
  llm_provider?: 'anthropic' | 'openai';
  evaluator_provider?: 'anthropic' | 'openai';
  top_k?: number;
  run_name?: string;
}

export interface TestCaseResult {
  test_case_id: string;
  query: string;
  expected_answer: string;
  generated_answer: string;
  overall_score: number;
  scores: EvaluationScores;
  status: 'success' | 'error';
  has_ground_truth: boolean;
}

export interface RunSummary {
  total_cases: number;
  completed: number;
  failed: number;
  avg_score: number;
  pass_rate: number;
  evaluation_type: string;
}

export interface EvaluationRun {
  id: string;
  test_set_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  config_snapshot: {
    llm_provider: string;
    evaluator_provider: string;
    top_k: number;
    run_name?: string;
  };
  results_json?: {
    results: TestCaseResult[];
    summary: RunSummary;
  };
  started_at: string;
  completed_at?: string;
}

export interface EvaluationRunListResponse {
  runs: EvaluationRun[];
  total: number;
}

export interface BulkImportResponse {
  test_set_id: string;
  imported_count: number;
  skipped_count: number;
  errors: string[];
}

// Diagnosis Types
export interface Alert {
  type: string;
  message: string;
  severity: 'high' | 'medium' | 'low';
  affected_count: number;
}

export interface DiagnosisSummary {
  period_days: number;
  total_evaluations: number;
  avg_score: number;
  low_score_count: number;
  high_score_count: number;
  alerts: Alert[];
  top_issues: string[];
  improvement_suggestions: string[];
}

export interface DiagnosisReport {
  period_days: number;
  analysis_timestamp: string;
  key_findings: string[];
  performance_issues: string[];
  categories_needing_attention: string[];
  intents_needing_attention: string[];
  suggested_actions: string[];
  detailed_analysis: string;
}

export interface AlertsResponse {
  alerts: Alert[];
  total_alerts: number;
  period_days: number;
}
