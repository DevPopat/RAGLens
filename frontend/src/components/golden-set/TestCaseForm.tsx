import { useState } from 'react';
import Button from '../common/Button';
import type { TestCaseCreate } from '../../types';

interface TestCaseFormProps {
  onSubmit: (testCase: TestCaseCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
  initialData?: Partial<TestCaseCreate>;
}

export default function TestCaseForm({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData,
}: TestCaseFormProps) {
  const [formData, setFormData] = useState<TestCaseCreate>({
    query: initialData?.query || '',
    expected_answer: initialData?.expected_answer || '',
    category: initialData?.category || '',
    intent: initialData?.intent || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.query && formData.expected_answer) {
      onSubmit({
        ...formData,
        category: formData.category || undefined,
        intent: formData.intent || undefined,
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Query <span className="text-red-500">*</span>
        </label>
        <textarea
          value={formData.query}
          onChange={(e) => setFormData({ ...formData, query: e.target.value })}
          placeholder="Enter the test query..."
          rows={2}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Expected Answer <span className="text-red-500">*</span>
        </label>
        <textarea
          value={formData.expected_answer}
          onChange={(e) => setFormData({ ...formData, expected_answer: e.target.value })}
          placeholder="Enter the expected answer..."
          rows={4}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <input
            type="text"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            placeholder="e.g., ACCOUNT, ORDER"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Intent</label>
          <input
            type="text"
            value={formData.intent}
            onChange={(e) => setFormData({ ...formData, intent: e.target.value })}
            placeholder="e.g., password_reset"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
          />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" isLoading={isLoading}>
          Save Test Case
        </Button>
      </div>
    </form>
  );
}
