import client from './client';
import type {
  EvaluationRequest,
  EvaluationResponse,
  EvaluationListResponse,
  BatchEvaluationRequest,
  BatchEvaluationResponse,
  ClaimCompareResponse,
} from '../types';

export async function runEvaluation(request: EvaluationRequest): Promise<EvaluationResponse> {
  const response = await client.post<EvaluationResponse>('/evaluation/run', request);
  return response.data;
}

export async function runBatchEvaluation(request: BatchEvaluationRequest): Promise<BatchEvaluationResponse> {
  const response = await client.post<BatchEvaluationResponse>('/evaluation/batch', request);
  return response.data;
}

export async function getEvaluation(evaluationId: string): Promise<EvaluationResponse> {
  const response = await client.get<EvaluationResponse>(`/evaluation/${evaluationId}`);
  return response.data;
}

export async function listEvaluations(
  skip: number = 0,
  limit: number = 50,
  evaluationType?: string
): Promise<EvaluationListResponse> {
  const response = await client.get<EvaluationListResponse>('/evaluation/', {
    params: { skip, limit, evaluation_type: evaluationType },
  });
  return response.data;
}

export async function getEvaluationsForQuery(queryId: string): Promise<EvaluationListResponse> {
  const response = await client.get<EvaluationListResponse>(`/evaluation/query/${queryId}`);
  return response.data;
}

export async function compareClaims(
  expectedAnswer: string,
  generatedAnswer: string
): Promise<ClaimCompareResponse> {
  const response = await client.post<ClaimCompareResponse>('/evaluation/compare-claims', {
    expected_answer: expectedAnswer,
    generated_answer: generatedAnswer,
  });
  return response.data;
}
