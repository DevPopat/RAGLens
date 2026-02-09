import { useState } from 'react';
import { RefreshCw, FileText, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Card, { CardHeader } from '../components/common/Card';
import Button from '../components/common/Button';
import { LoadingState } from '../components/common/Spinner';
import SummaryStats from '../components/diagnosis/SummaryStats';
import { AlertList } from '../components/diagnosis/AlertCard';
import DiagnosisReportView from '../components/diagnosis/DiagnosisReport';
import useDiagnosis from '../hooks/useDiagnosis';

export default function DashboardPage() {
  const navigate = useNavigate();
  const {
    summary,
    report,
    isLoading,
    isLoadingReport,
    error,
    fetchSummary,
    fetchReport,
  } = useDiagnosis();
  const [showReport, setShowReport] = useState(false);
  const [periodDays, setPeriodDays] = useState(7);

  const handleRefresh = () => {
    fetchSummary(periodDays);
    if (showReport) {
      fetchReport(periodDays);
    }
  };

  const handleGenerateReport = () => {
    setShowReport(true);
    fetchReport(periodDays);
  };

  if (isLoading && !summary) {
    return <LoadingState message="Loading dashboard..." />;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Monitor your RAG system's health and performance</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            leftIcon={<RefreshCw className="w-4 h-4" />}
            isLoading={isLoading}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
          {error}
        </div>
      )}

      {/* Summary Stats */}
      {summary && (
        <>
          <SummaryStats summary={summary} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Alerts */}
            <Card className="lg:col-span-2">
              <CardHeader
                title="Active Alerts"
                subtitle={`${summary.alerts.length} alert${summary.alerts.length !== 1 ? 's' : ''} requiring attention`}
              />
              <AlertList alerts={summary.alerts} maxItems={5} />
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader title="Quick Actions" />
              <div className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate('/chat')}
                  leftIcon={<TrendingUp className="w-4 h-4" />}
                >
                  Start New Chat
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate('/evaluations')}
                  leftIcon={<TrendingUp className="w-4 h-4" />}
                >
                  View Evaluations
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate('/golden-sets')}
                  leftIcon={<TrendingUp className="w-4 h-4" />}
                >
                  Manage Golden Sets
                </Button>
                <Button
                  variant="primary"
                  className="w-full justify-start"
                  onClick={handleGenerateReport}
                  leftIcon={<FileText className="w-4 h-4" />}
                  isLoading={isLoadingReport}
                  disabled={showReport && !!report}
                >
                  {showReport && report ? 'Report Generated' : 'Generate Full Report'}
                </Button>
              </div>
            </Card>
          </div>

          {/* Top Issues & Suggestions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {summary.top_issues.length > 0 && (
              <Card>
                <CardHeader title="Top Issues" subtitle="Most common problems identified" />
                <ul className="space-y-2">
                  {summary.top_issues.map((issue, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm text-gray-700"
                    >
                      <span className="text-red-500 font-medium">{index + 1}.</span>
                      {issue}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {summary.improvement_suggestions.length > 0 && (
              <Card>
                <CardHeader
                  title="Improvement Suggestions"
                  subtitle="Recommendations for better performance"
                />
                <ul className="space-y-2">
                  {summary.improvement_suggestions.map((suggestion, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm text-gray-700"
                    >
                      <span className="text-green-500 font-medium">{index + 1}.</span>
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        </>
      )}

      {/* Full Report */}
      {showReport && (
        <div className="mt-6">
          {isLoadingReport ? (
            <Card>
              <LoadingState message="Generating comprehensive report... This may take a moment." />
            </Card>
          ) : report ? (
            <DiagnosisReportView report={report} />
          ) : null}
        </div>
      )}
    </div>
  );
}
