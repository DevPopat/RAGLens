import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  Play,
  Download,
  History,
} from 'lucide-react';
import Card, { CardHeader } from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import { LoadingState } from '../components/common/Spinner';
import { StatusBadge } from '../components/common/Badge';
import TestCaseList from '../components/golden-set/TestCaseList';
import TestCaseForm from '../components/golden-set/TestCaseForm';
import RunResultsTable from '../components/golden-set/RunResultsTable';
import { useApp } from '../contexts/AppContext';
import {
  getGoldenSet,
  addTestCase,
  updateTestCase,
  deleteTestCase,
  importFromHoldout,
  runTestSet,
  listRuns,
  getRun,
} from '../api/goldenSet';
import type {
  GoldenSetDetail,
  TestCase,
  TestCaseCreate,
  EvaluationRun,
  RunTestSetRequest,
} from '../types';

export default function GoldenSetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addNotification } = useApp();

  const [goldenSet, setGoldenSet] = useState<GoldenSetDetail | null>(null);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [isAddCaseModalOpen, setIsAddCaseModalOpen] = useState(false);
  const [isEditCaseModalOpen, setIsEditCaseModalOpen] = useState(false);
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [isRunsModalOpen, setIsRunsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Run config
  const [runConfig, setRunConfig] = useState<RunTestSetRequest>({
    llm_provider: 'anthropic',
    evaluator_provider: 'anthropic',
    top_k: 5,
    run_name: '',
  });

  // Import config
  const [importMaxCases, setImportMaxCases] = useState<number | undefined>(undefined);

  const fetchGoldenSet = useCallback(async () => {
    if (!id) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await getGoldenSet(id);
      setGoldenSet(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch golden set');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  const fetchRuns = useCallback(async () => {
    if (!id) return;

    try {
      const response = await listRuns(id);
      setRuns(response.runs);
    } catch (err) {
      console.error('Failed to fetch runs:', err);
    }
  }, [id]);

  useEffect(() => {
    fetchGoldenSet();
    fetchRuns();
  }, [fetchGoldenSet, fetchRuns]);

  const handleAddCase = async (testCase: TestCaseCreate) => {
    if (!id) return;

    setIsSubmitting(true);
    try {
      await addTestCase(id, testCase);
      addNotification('success', 'Test case added successfully');
      setIsAddCaseModalOpen(false);
      fetchGoldenSet();
    } catch (err) {
      addNotification('error', err instanceof Error ? err.message : 'Failed to add test case');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditCase = async (testCase: TestCaseCreate) => {
    if (!id || !editingCase) return;

    setIsSubmitting(true);
    try {
      await updateTestCase(id, editingCase.id, testCase);
      addNotification('success', 'Test case updated successfully');
      setIsEditCaseModalOpen(false);
      setEditingCase(null);
      fetchGoldenSet();
    } catch (err) {
      addNotification('error', err instanceof Error ? err.message : 'Failed to update test case');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCase = async (testCase: TestCase) => {
    if (!id) return;

    if (!confirm('Are you sure you want to delete this test case?')) return;

    try {
      await deleteTestCase(id, testCase.id);
      addNotification('success', 'Test case deleted');
      fetchGoldenSet();
    } catch (err) {
      addNotification('error', err instanceof Error ? err.message : 'Failed to delete test case');
    }
  };

  const handleImport = async () => {
    if (!id) return;

    setIsSubmitting(true);
    try {
      const result = await importFromHoldout(id, importMaxCases);
      addNotification(
        'success',
        `Imported ${result.imported_count} test cases (${result.skipped_count} skipped)`
      );
      setIsImportModalOpen(false);
      fetchGoldenSet();
    } catch (err) {
      addNotification('error', err instanceof Error ? err.message : 'Failed to import');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunEvaluation = async () => {
    if (!id) return;

    setIsSubmitting(true);
    try {
      await runTestSet(id, runConfig);
      addNotification('success', 'Evaluation started. Check the runs tab for results.');
      setIsRunModalOpen(false);
      fetchRuns();
    } catch (err) {
      addNotification('error', err instanceof Error ? err.message : 'Failed to start evaluation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewRun = async (run: EvaluationRun) => {
    if (!id) return;

    try {
      const fullRun = await getRun(id, run.id);
      setSelectedRun(fullRun);
      setIsRunsModalOpen(false);
    } catch (err) {
      addNotification('error', 'Failed to load run details');
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading golden set..." />;
  }

  if (error || !goldenSet) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || 'Golden set not found'}
        </div>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/golden-sets')}>
          Back to Golden Sets
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/golden-sets')}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
        >
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{goldenSet.name}</h1>
          {goldenSet.description && (
            <p className="text-gray-500 mt-1">{goldenSet.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setIsRunsModalOpen(true)}
            leftIcon={<History className="w-4 h-4" />}
          >
            View Runs ({runs.length})
          </Button>
          <Button
            variant="primary"
            onClick={() => setIsRunModalOpen(true)}
            leftIcon={<Play className="w-4 h-4" />}
            disabled={goldenSet.test_cases.length === 0}
          >
            Run Evaluation
          </Button>
        </div>
      </div>

      {/* Selected Run Results */}
      {selectedRun && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Evaluation Run: {selectedRun.config_snapshot?.run_name || 'Unnamed Run'}
            </h2>
            <Button variant="ghost" size="sm" onClick={() => setSelectedRun(null)}>
              Close
            </Button>
          </div>
          <RunResultsTable run={selectedRun} />
        </div>
      )}

      {/* Test Cases */}
      <Card>
        <CardHeader
          title="Test Cases"
          subtitle={`${goldenSet.test_cases.length} test case${goldenSet.test_cases.length !== 1 ? 's' : ''}`}
          action={
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsImportModalOpen(true)}
                leftIcon={<Download className="w-4 h-4" />}
              >
                Import from Holdout
              </Button>
              <Button
                size="sm"
                onClick={() => setIsAddCaseModalOpen(true)}
                leftIcon={<Plus className="w-4 h-4" />}
              >
                Add Test Case
              </Button>
            </div>
          }
        />
        <TestCaseList
          testCases={goldenSet.test_cases}
          onEdit={(tc) => {
            setEditingCase(tc);
            setIsEditCaseModalOpen(true);
          }}
          onDelete={handleDeleteCase}
        />
      </Card>

      {/* Add Test Case Modal */}
      <Modal
        isOpen={isAddCaseModalOpen}
        onClose={() => setIsAddCaseModalOpen(false)}
        title="Add Test Case"
        size="lg"
      >
        <TestCaseForm
          onSubmit={handleAddCase}
          onCancel={() => setIsAddCaseModalOpen(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* Edit Test Case Modal */}
      <Modal
        isOpen={isEditCaseModalOpen}
        onClose={() => {
          setIsEditCaseModalOpen(false);
          setEditingCase(null);
        }}
        title="Edit Test Case"
        size="lg"
      >
        {editingCase && (
          <TestCaseForm
            onSubmit={handleEditCase}
            onCancel={() => {
              setIsEditCaseModalOpen(false);
              setEditingCase(null);
            }}
            isLoading={isSubmitting}
            initialData={editingCase}
          />
        )}
      </Modal>

      {/* Run Evaluation Modal */}
      <Modal
        isOpen={isRunModalOpen}
        onClose={() => setIsRunModalOpen(false)}
        title="Run Evaluation"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsRunModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRunEvaluation} isLoading={isSubmitting}>
              Start Evaluation
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Run Name (optional)
            </label>
            <input
              type="text"
              value={runConfig.run_name || ''}
              onChange={(e) => setRunConfig({ ...runConfig, run_name: e.target.value })}
              placeholder="e.g., Baseline v1"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                LLM Provider
              </label>
              <select
                value={runConfig.llm_provider}
                onChange={(e) =>
                  setRunConfig({
                    ...runConfig,
                    llm_provider: e.target.value as 'anthropic' | 'openai',
                  })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
              >
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Evaluator Provider
              </label>
              <select
                value={runConfig.evaluator_provider}
                onChange={(e) =>
                  setRunConfig({
                    ...runConfig,
                    evaluator_provider: e.target.value as 'anthropic' | 'openai',
                  })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
              >
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Top K (retrieval)
            </label>
            <input
              type="number"
              value={runConfig.top_k}
              onChange={(e) =>
                setRunConfig({ ...runConfig, top_k: parseInt(e.target.value) || 5 })
              }
              min={1}
              max={20}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
            />
          </div>
          <p className="text-sm text-gray-500">
            This will run evaluation on all {goldenSet.test_cases.length} test cases. The
            evaluation runs in the background.
          </p>
        </div>
      </Modal>

      {/* Runs History Modal */}
      <Modal
        isOpen={isRunsModalOpen}
        onClose={() => setIsRunsModalOpen(false)}
        title="Evaluation Runs"
        size="lg"
      >
        {runs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No evaluation runs yet. Run an evaluation to see results here.
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {runs.map((run) => (
              <div
                key={run.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                onClick={() => handleViewRun(run)}
              >
                <div>
                  <p className="font-medium text-gray-900">
                    {run.config_snapshot?.run_name || 'Unnamed Run'}
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date(run.started_at).toLocaleString()}
                  </p>
                  <div className="flex gap-2 mt-1">
                    <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                      {run.config_snapshot?.llm_provider}
                    </span>
                    <span className="text-xs text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded">
                      eval: {run.config_snapshot?.evaluator_provider}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <StatusBadge status={run.status} />
                  {run.results_json?.summary?.avg_score != null && (
                    <span className="text-sm font-medium text-gray-700">
                      {Math.round(run.results_json.summary.avg_score * 100)}% avg
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>

      {/* Import Modal */}
      <Modal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        title="Import from Holdout Set"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsImportModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleImport} isLoading={isSubmitting}>
              Import
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Import test cases from the stratified holdout set created during data ingestion.
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Cases (optional)
            </label>
            <input
              type="number"
              value={importMaxCases || ''}
              onChange={(e) =>
                setImportMaxCases(e.target.value ? parseInt(e.target.value) : undefined)
              }
              placeholder="Leave empty for all"
              min={1}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
