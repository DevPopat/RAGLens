import client from './client';
import type { DiagnosisSummary, DiagnosisReport, AlertsResponse } from '../types';

export async function getDiagnosisReport(days: number = 7): Promise<DiagnosisReport> {
  const response = await client.get<DiagnosisReport>('/diagnosis/report', {
    params: { days },
  });
  return response.data;
}

export async function getDiagnosisSummary(days: number = 7): Promise<DiagnosisSummary> {
  const response = await client.get<DiagnosisSummary>('/diagnosis/summary', {
    params: { days },
  });
  return response.data;
}

export async function getAlerts(days: number = 7, severity?: 'high' | 'medium' | 'low'): Promise<AlertsResponse> {
  const response = await client.get<AlertsResponse>('/diagnosis/alerts', {
    params: { days, severity },
  });
  return response.data;
}
