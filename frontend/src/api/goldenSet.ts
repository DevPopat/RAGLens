import client from './client';
import type {
  GoldenSet,
  GoldenSetDetail,
  GoldenSetCreate,
  GoldenSetUpdate,
  GoldenSetListResponse,
  TestCase,
  TestCaseCreate,
  TestCaseUpdate,
  RunTestSetRequest,
  EvaluationRun,
  EvaluationRunListResponse,
  BulkImportResponse,
} from '../types';

// Golden Set CRUD
export async function createGoldenSet(data: GoldenSetCreate): Promise<GoldenSet> {
  const response = await client.post<GoldenSet>('/golden-set/', data);
  return response.data;
}

export async function listGoldenSets(skip: number = 0, limit: number = 50): Promise<GoldenSetListResponse> {
  const response = await client.get<GoldenSetListResponse>('/golden-set/', {
    params: { skip, limit },
  });
  return response.data;
}

export async function getGoldenSet(goldenSetId: string): Promise<GoldenSetDetail> {
  const response = await client.get<GoldenSetDetail>(`/golden-set/${goldenSetId}`);
  return response.data;
}

export async function updateGoldenSet(goldenSetId: string, data: GoldenSetUpdate): Promise<GoldenSet> {
  const response = await client.patch<GoldenSet>(`/golden-set/${goldenSetId}`, data);
  return response.data;
}

export async function deleteGoldenSet(goldenSetId: string): Promise<{ message: string }> {
  const response = await client.delete<{ message: string }>(`/golden-set/${goldenSetId}`);
  return response.data;
}

// Test Case CRUD
export async function addTestCase(goldenSetId: string, data: TestCaseCreate): Promise<TestCase> {
  const response = await client.post<TestCase>(`/golden-set/${goldenSetId}/cases`, data);
  return response.data;
}

export async function addTestCasesBulk(
  goldenSetId: string,
  testCases: TestCaseCreate[]
): Promise<{ added: number; golden_set_id: string }> {
  const response = await client.post<{ added: number; golden_set_id: string }>(
    `/golden-set/${goldenSetId}/cases/bulk`,
    testCases
  );
  return response.data;
}

export async function getTestCase(goldenSetId: string, caseId: string): Promise<TestCase> {
  const response = await client.get<TestCase>(`/golden-set/${goldenSetId}/cases/${caseId}`);
  return response.data;
}

export async function updateTestCase(
  goldenSetId: string,
  caseId: string,
  data: TestCaseUpdate
): Promise<TestCase> {
  const response = await client.patch<TestCase>(`/golden-set/${goldenSetId}/cases/${caseId}`, data);
  return response.data;
}

export async function deleteTestCase(goldenSetId: string, caseId: string): Promise<{ message: string }> {
  const response = await client.delete<{ message: string }>(`/golden-set/${goldenSetId}/cases/${caseId}`);
  return response.data;
}

// Import from holdout
export async function importFromHoldout(
  goldenSetId: string,
  maxCases?: number,
  categories?: string[],
  intents?: string[]
): Promise<BulkImportResponse> {
  const params = new URLSearchParams();
  params.append('golden_set_id', goldenSetId);
  if (maxCases) params.append('max_cases', maxCases.toString());
  if (categories) categories.forEach((c) => params.append('categories', c));
  if (intents) intents.forEach((i) => params.append('intents', i));

  const response = await client.post<BulkImportResponse>(`/golden-set/import-holdout?${params.toString()}`);
  return response.data;
}

// Evaluation Runs
export async function runTestSet(goldenSetId: string, config: RunTestSetRequest): Promise<EvaluationRun> {
  const response = await client.post<EvaluationRun>(`/golden-set/${goldenSetId}/run`, config);
  return response.data;
}

export async function listRuns(goldenSetId: string): Promise<EvaluationRunListResponse> {
  const response = await client.get<EvaluationRunListResponse>(`/golden-set/${goldenSetId}/runs`);
  return response.data;
}

export async function getRun(goldenSetId: string, runId: string): Promise<EvaluationRun> {
  const response = await client.get<EvaluationRun>(`/golden-set/${goldenSetId}/runs/${runId}`);
  return response.data;
}
