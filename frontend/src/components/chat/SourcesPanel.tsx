import { FileText, ChevronRight } from 'lucide-react';
import type { Source } from '../../types';
import ScoreBar from '../common/ScoreBar';

interface SourcesPanelProps {
  sources: Source[];
  isExpanded: boolean;
  onToggle: () => void;
}

export default function SourcesPanel({ sources, isExpanded, onToggle }: SourcesPanelProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div
      className={`border-l border-gray-200 bg-gray-50 transition-all duration-300 ${
        isExpanded ? 'w-80' : 'w-12'
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-center text-gray-500 hover:bg-gray-100 border-b border-gray-200"
      >
        <ChevronRight
          className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {isExpanded && (
        <div className="p-4 overflow-y-auto h-[calc(100%-48px)]">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Retrieved Sources ({sources.length})
          </h3>
          <div className="space-y-3">
            {sources.map((source, index) => (
              <SourceCard key={source.id || `source-${index}`} source={source} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface SourceCardProps {
  source: Source;
  index: number;
}

function SourceCard({ source, index }: SourceCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3 text-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-700">Source {index + 1}</span>
        <ScoreBar score={source.score} size="sm" showPercentage={true} className="w-20" />
      </div>
      <p className="text-gray-600 text-xs line-clamp-4">{source.text}</p>
      {source.metadata && Object.keys(source.metadata).length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <div className="flex flex-wrap gap-1">
            {source.metadata.category != null && (
              <span className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">
                {String(source.metadata.category)}
              </span>
            )}
            {source.metadata.intent != null && (
              <span className="px-2 py-0.5 bg-purple-50 text-purple-600 rounded text-xs">
                {String(source.metadata.intent)}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
