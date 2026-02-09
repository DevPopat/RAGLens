import { FileText, AlertCircle, Lightbulb, Clock } from 'lucide-react';
import type { DiagnosisReport } from '../../types';
import Card, { CardHeader } from '../common/Card';

interface DiagnosisReportViewProps {
  report: DiagnosisReport;
}

export default function DiagnosisReportView({ report }: DiagnosisReportViewProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-primary-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Diagnosis Report</h2>
            <p className="text-sm text-gray-500">
              Analysis period: {report.period_days} days
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock className="w-4 h-4" />
          {new Date(report.analysis_timestamp).toLocaleString()}
        </div>
      </div>

      {/* Key Findings */}
      {report.key_findings.length > 0 && (
        <Card>
          <CardHeader title="Key Findings" subtitle="Main insights from the analysis" />
          <ul className="space-y-2">
            {report.key_findings.map((finding, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-primary-500 mt-1">•</span>
                {finding}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Performance Issues */}
      {report.performance_issues.length > 0 && (
        <Card>
          <CardHeader
            title="Performance Issues"
            subtitle="Areas where the system is underperforming"
          />
          <ul className="space-y-2">
            {report.performance_issues.map((issue, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                {issue}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Categories Needing Attention */}
        {report.categories_needing_attention.length > 0 && (
          <Card>
            <CardHeader
              title="Categories to Review"
              subtitle="Document categories with issues"
            />
            <div className="flex flex-wrap gap-2">
              {report.categories_needing_attention.map((category, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm"
                >
                  {category}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Intents Needing Attention */}
        {report.intents_needing_attention.length > 0 && (
          <Card>
            <CardHeader
              title="Intents to Review"
              subtitle="Query intents with issues"
            />
            <div className="flex flex-wrap gap-2">
              {report.intents_needing_attention.map((intent, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-sm"
                >
                  {intent}
                </span>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Suggested Actions */}
      {report.suggested_actions.length > 0 && (
        <Card>
          <CardHeader
            title="Suggested Actions"
            subtitle="Recommended steps to improve performance"
          />
          <ul className="space-y-2">
            {report.suggested_actions.map((action, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                <Lightbulb className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                {action}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Detailed Analysis */}
      {report.detailed_analysis && (
        <Card>
          <CardHeader
            title="Detailed Analysis"
            subtitle="In-depth examination of system performance"
          />
          <div className="prose prose-sm max-w-none text-gray-700">
            <p className="whitespace-pre-wrap">{report.detailed_analysis}</p>
          </div>
        </Card>
      )}
    </div>
  );
}
