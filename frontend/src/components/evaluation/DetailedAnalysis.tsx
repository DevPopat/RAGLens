import { CheckCircle, AlertTriangle, HelpCircle, MessageSquare, Database } from 'lucide-react';
import Badge from '../common/Badge';
import type {
  FaithfulnessDetail,
  QuestionCoverageDetail,
  ContextUtilizationDetail,
} from '../../types';

// --- Faithfulness Breakdown ---

const FAITHFULNESS_CONFIG = {
  supported: { icon: CheckCircle, variant: 'success' as const, label: 'Supported', color: 'text-green-600' },
  unsupported: { icon: HelpCircle, variant: 'warning' as const, label: 'Unsupported', color: 'text-orange-500' },
  contradicted: { icon: AlertTriangle, variant: 'error' as const, label: 'Contradicted', color: 'text-red-600' },
};

interface FaithfulnessBreakdownProps {
  detail: FaithfulnessDetail;
}

export function FaithfulnessBreakdown({ detail }: FaithfulnessBreakdownProps) {
  const supported = detail.claims.filter((c) => c.verdict === 'supported').length;
  const total = detail.claims.length;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-700">{detail.summary}</p>
        <span className="text-xs text-gray-400 flex-shrink-0 ml-2">
          {supported}/{total} supported
        </span>
      </div>
      {detail.claims.map((claim, i) => {
        const config = FAITHFULNESS_CONFIG[claim.verdict] ?? FAITHFULNESS_CONFIG.unsupported;
        const Icon = config.icon;
        return (
          <div key={i} className="flex items-start gap-2 p-2.5 rounded-md bg-gray-50 border border-gray-100">
            <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.color}`} />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-gray-800">{claim.statement}</p>
              <p className="text-xs text-gray-500 mt-0.5">{claim.reason}</p>
              {claim.source_quote && (
                <blockquote className="mt-1.5 pl-2 border-l-2 border-gray-300 text-xs text-gray-500 italic">
                  &ldquo;{claim.source_quote}&rdquo;
                  {claim.context_index != null && (
                    <span className="not-italic ml-1 text-gray-400">
                      &mdash; Context {claim.context_index + 1}
                    </span>
                  )}
                </blockquote>
              )}
            </div>
            <Badge variant={config.variant} size="sm" className="flex-shrink-0">
              {config.label}
            </Badge>
          </div>
        );
      })}
    </div>
  );
}

// --- Question Coverage Breakdown ---

const COVERAGE_CONFIG = {
  addressed: { variant: 'success' as const, label: 'Addressed', iconColor: 'text-green-600' },
  partially_addressed: { variant: 'warning' as const, label: 'Partial', iconColor: 'text-yellow-600' },
  not_addressed: { variant: 'error' as const, label: 'Missing', iconColor: 'text-red-600' },
};

interface QuestionCoverageBreakdownProps {
  detail: QuestionCoverageDetail;
}

export function QuestionCoverageBreakdown({ detail }: QuestionCoverageBreakdownProps) {
  const addressed = detail.components.filter((c) => c.verdict === 'addressed').length;
  const total = detail.components.length;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-700">{detail.summary}</p>
        <span className="text-xs text-gray-400 flex-shrink-0 ml-2">
          {addressed}/{total} addressed
        </span>
      </div>
      {detail.components.map((comp, i) => {
        const config = COVERAGE_CONFIG[comp.verdict] ?? COVERAGE_CONFIG.not_addressed;
        return (
          <div key={i} className="flex items-start gap-2 p-2.5 rounded-md bg-gray-50 border border-gray-100">
            <MessageSquare className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-gray-800 font-medium">{comp.component}</p>
              <p className="text-xs text-gray-500 mt-0.5">{comp.reason}</p>
              {comp.response_quote && (
                <blockquote className="mt-1.5 pl-2 border-l-2 border-green-300 text-xs text-gray-600 italic">
                  &ldquo;{comp.response_quote}&rdquo;
                </blockquote>
              )}
            </div>
            <Badge variant={config.variant} size="sm" className="flex-shrink-0">
              {config.label}
            </Badge>
          </div>
        );
      })}
    </div>
  );
}

// --- Context Utilization Breakdown ---

const UTILIZATION_CONFIG = {
  used: { variant: 'success' as const, label: 'Used', iconColor: 'text-green-600' },
  partially_used: { variant: 'warning' as const, label: 'Partial', iconColor: 'text-yellow-600' },
  not_used: { variant: 'default' as const, label: 'Not Used', iconColor: 'text-gray-400' },
};

interface ContextUtilizationBreakdownProps {
  detail: ContextUtilizationDetail;
}

export function ContextUtilizationBreakdown({ detail }: ContextUtilizationBreakdownProps) {
  const used = detail.contexts.filter((c) => c.verdict === 'used').length;
  const total = detail.contexts.length;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-700">{detail.summary}</p>
        <span className="text-xs text-gray-400 flex-shrink-0 ml-2">
          {used}/{total} used
        </span>
      </div>
      {detail.contexts.map((ctx) => {
        const config = UTILIZATION_CONFIG[ctx.verdict] ?? UTILIZATION_CONFIG.not_used;
        return (
          <div key={ctx.context_index} className="flex items-start gap-2 p-2.5 rounded-md bg-gray-50 border border-gray-100">
            <Database className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-gray-700">
                <span className="font-mono text-xs text-gray-400 mr-1">#{ctx.context_index + 1}</span>
                {ctx.reason}
              </p>
              {ctx.used_in_response && (
                <blockquote className="mt-1.5 pl-2 border-l-2 border-green-300 text-xs text-gray-600 italic">
                  &ldquo;{ctx.used_in_response}&rdquo;
                </blockquote>
              )}
            </div>
            <Badge variant={config.variant} size="sm" className="flex-shrink-0">
              {config.label}
            </Badge>
          </div>
        );
      })}
    </div>
  );
}
