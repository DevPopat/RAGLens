import { useState } from 'react';
import { Edit2, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import type { TestCase } from '../../types';
import Badge from '../common/Badge';

interface TestCaseListProps {
  testCases: TestCase[];
  onEdit?: (testCase: TestCase) => void;
  onDelete?: (testCase: TestCase) => void;
}

export default function TestCaseList({ testCases, onEdit, onDelete }: TestCaseListProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  if (testCases.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No test cases yet. Add your first test case to get started.</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {testCases.map((testCase, index) => {
        const isExpanded = expandedIds.has(testCase.id);

        return (
          <div key={testCase.id} className="py-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                  {testCase.category && (
                    <Badge variant="info" size="sm">
                      {testCase.category}
                    </Badge>
                  )}
                  {testCase.intent && (
                    <Badge variant="default" size="sm">
                      {testCase.intent}
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-900 font-medium">{testCase.query}</p>

                {isExpanded && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Expected Answer:</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {testCase.expected_answer}
                    </p>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleExpand(testCase.id)}
                  className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                >
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
                {onEdit && (
                  <button
                    onClick={() => onEdit(testCase)}
                    className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => onDelete(testCase)}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
