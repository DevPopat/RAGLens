import { FileText, Clock, Trash2, ChevronRight } from 'lucide-react';
import type { GoldenSet } from '../../types';
import Card from '../common/Card';
import Badge from '../common/Badge';

interface GoldenSetCardProps {
  goldenSet: GoldenSet;
  onClick?: () => void;
  onDelete?: () => void;
}

export default function GoldenSetCard({ goldenSet, onClick, onDelete }: GoldenSetCardProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.();
  };

  return (
    <Card hover={!!onClick} onClick={onClick} className="group">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 min-w-0">
          <div className="p-2 bg-primary-50 rounded-lg">
            <FileText className="w-6 h-6 text-primary-600" />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">{goldenSet.name}</h3>
            {goldenSet.description && (
              <p className="text-sm text-gray-500 truncate">{goldenSet.description}</p>
            )}
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Updated {formatDate(goldenSet.updated_at)}
              </span>
              <Badge variant="default" size="sm">
                v{goldenSet.version}
              </Badge>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-2xl font-bold text-gray-900">{goldenSet.test_case_count}</p>
            <p className="text-xs text-gray-500">test cases</p>
          </div>
          {onDelete && (
            <button
              onClick={handleDelete}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          {onClick && (
            <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-gray-600" />
          )}
        </div>
      </div>
    </Card>
  );
}
