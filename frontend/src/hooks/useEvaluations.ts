import { useState, useCallback, useEffect } from 'react';
import { listEvaluations, getEvaluation } from '../api/evaluation';
import type { EvaluationResponse } from '../types';

interface UseEvaluationsReturn {
  evaluations: EvaluationResponse[];
  total: number;
  isLoading: boolean;
  error: string | null;
  selectedEvaluation: EvaluationResponse | null;
  fetchEvaluations: (skip?: number, limit?: number) => Promise<void>;
  fetchEvaluation: (id: string) => Promise<void>;
  clearSelection: () => void;
}

export default function useEvaluations(): UseEvaluationsReturn {
  const [evaluations, setEvaluations] = useState<EvaluationResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationResponse | null>(null);

  const fetchEvaluations = useCallback(async (skip: number = 0, limit: number = 50) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listEvaluations(skip, limit);
      setEvaluations(response.evaluations);
      setTotal(response.total);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch evaluations';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchEvaluation = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const evaluation = await getEvaluation(id);
      setSelectedEvaluation(evaluation);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch evaluation';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedEvaluation(null);
  }, []);

  useEffect(() => {
    fetchEvaluations();
  }, [fetchEvaluations]);

  return {
    evaluations,
    total,
    isLoading,
    error,
    selectedEvaluation,
    fetchEvaluations,
    fetchEvaluation,
    clearSelection,
  };
}
