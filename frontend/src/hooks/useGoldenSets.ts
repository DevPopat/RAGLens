import { useState, useCallback, useEffect } from 'react';
import {
  listGoldenSets,
  getGoldenSet,
  createGoldenSet,
  deleteGoldenSet,
  listRuns,
  getRun,
} from '../api/goldenSet';
import type { GoldenSet, GoldenSetDetail, GoldenSetCreate, EvaluationRun } from '../types';

interface UseGoldenSetsReturn {
  goldenSets: GoldenSet[];
  total: number;
  isLoading: boolean;
  error: string | null;
  selectedSet: GoldenSetDetail | null;
  runs: EvaluationRun[];
  selectedRun: EvaluationRun | null;
  fetchGoldenSets: (skip?: number, limit?: number) => Promise<void>;
  fetchGoldenSet: (id: string) => Promise<void>;
  createNewGoldenSet: (data: GoldenSetCreate) => Promise<GoldenSet | null>;
  removeGoldenSet: (id: string) => Promise<boolean>;
  fetchRuns: (goldenSetId: string) => Promise<void>;
  fetchRun: (goldenSetId: string, runId: string) => Promise<void>;
  clearSelection: () => void;
}

export default function useGoldenSets(): UseGoldenSetsReturn {
  const [goldenSets, setGoldenSets] = useState<GoldenSet[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSet, setSelectedSet] = useState<GoldenSetDetail | null>(null);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);

  const fetchGoldenSets = useCallback(async (skip: number = 0, limit: number = 50) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listGoldenSets(skip, limit);
      setGoldenSets(response.golden_sets);
      setTotal(response.total);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch golden sets';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchGoldenSet = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const goldenSet = await getGoldenSet(id);
      setSelectedSet(goldenSet);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch golden set';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createNewGoldenSet = useCallback(async (data: GoldenSetCreate): Promise<GoldenSet | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const newSet = await createGoldenSet(data);
      setGoldenSets((prev) => [newSet, ...prev]);
      setTotal((prev) => prev + 1);
      return newSet;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create golden set';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const removeGoldenSet = useCallback(async (id: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      await deleteGoldenSet(id);
      setGoldenSets((prev) => prev.filter((gs) => gs.id !== id));
      setTotal((prev) => prev - 1);
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete golden set';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchRuns = useCallback(async (goldenSetId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listRuns(goldenSetId);
      setRuns(response.runs);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch runs';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchRun = useCallback(async (goldenSetId: string, runId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const run = await getRun(goldenSetId, runId);
      setSelectedRun(run);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch run';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedSet(null);
    setSelectedRun(null);
    setRuns([]);
  }, []);

  useEffect(() => {
    fetchGoldenSets();
  }, [fetchGoldenSets]);

  return {
    goldenSets,
    total,
    isLoading,
    error,
    selectedSet,
    runs,
    selectedRun,
    fetchGoldenSets,
    fetchGoldenSet,
    createNewGoldenSet,
    removeGoldenSet,
    fetchRuns,
    fetchRun,
    clearSelection,
  };
}
