import { useState, useCallback, useEffect } from 'react';
import { getDiagnosisSummary, getDiagnosisReport, getAlerts } from '../api/diagnosis';
import type { DiagnosisSummary, DiagnosisReport, Alert } from '../types';

interface UseDiagnosisReturn {
  summary: DiagnosisSummary | null;
  report: DiagnosisReport | null;
  alerts: Alert[];
  isLoading: boolean;
  isLoadingReport: boolean;
  error: string | null;
  fetchSummary: (days?: number) => Promise<void>;
  fetchReport: (days?: number) => Promise<void>;
  fetchAlerts: (days?: number, severity?: 'high' | 'medium' | 'low') => Promise<void>;
}

export default function useDiagnosis(): UseDiagnosisReturn {
  const [summary, setSummary] = useState<DiagnosisSummary | null>(null);
  const [report, setReport] = useState<DiagnosisReport | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async (days: number = 7) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getDiagnosisSummary(days);
      setSummary(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch summary';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchReport = useCallback(async (days: number = 7) => {
    setIsLoadingReport(true);
    setError(null);

    try {
      const data = await getDiagnosisReport(days);
      setReport(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch report';
      setError(errorMessage);
    } finally {
      setIsLoadingReport(false);
    }
  }, []);

  const fetchAlerts = useCallback(async (days: number = 7, severity?: 'high' | 'medium' | 'low') => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getAlerts(days, severity);
      setAlerts(data.alerts);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch alerts';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return {
    summary,
    report,
    alerts,
    isLoading,
    isLoadingReport,
    error,
    fetchSummary,
    fetchReport,
    fetchAlerts,
  };
}
