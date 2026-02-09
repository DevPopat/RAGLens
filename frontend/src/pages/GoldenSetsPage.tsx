import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FolderOpen } from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import { LoadingState } from '../components/common/Spinner';
import GoldenSetCard from '../components/golden-set/GoldenSetCard';
import useGoldenSets from '../hooks/useGoldenSets';
import { useApp } from '../contexts/AppContext';

export default function GoldenSetsPage() {
  const navigate = useNavigate();
  const { addNotification } = useApp();
  const {
    goldenSets,
    total,
    isLoading,
    error,
    createNewGoldenSet,
    removeGoldenSet,
  } = useGoldenSets();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedSetId, setSelectedSetId] = useState<string | null>(null);
  const [newSetName, setNewSetName] = useState('');
  const [newSetDescription, setNewSetDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreate = async () => {
    if (!newSetName.trim()) return;

    setIsSubmitting(true);
    const result = await createNewGoldenSet({
      name: newSetName.trim(),
      description: newSetDescription.trim() || undefined,
    });
    setIsSubmitting(false);

    if (result) {
      addNotification('success', `Golden set "${result.name}" created successfully`);
      setIsCreateModalOpen(false);
      setNewSetName('');
      setNewSetDescription('');
      navigate(`/golden-sets/${result.id}`);
    } else {
      addNotification('error', 'Failed to create golden set');
    }
  };

  const handleDelete = async () => {
    if (!selectedSetId) return;

    setIsSubmitting(true);
    const success = await removeGoldenSet(selectedSetId);
    setIsSubmitting(false);

    if (success) {
      addNotification('success', 'Golden set deleted successfully');
      setIsDeleteModalOpen(false);
      setSelectedSetId(null);
    } else {
      addNotification('error', 'Failed to delete golden set');
    }
  };

  const openDeleteModal = (id: string) => {
    setSelectedSetId(id);
    setIsDeleteModalOpen(true);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Golden Test Sets</h1>
          <p className="text-gray-500 mt-1">
            Manage your golden test sets for systematic RAG evaluation
          </p>
        </div>
        <Button
          onClick={() => setIsCreateModalOpen(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Create Golden Set
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
          {error}
        </div>
      )}

      {/* Golden Sets List */}
      {isLoading && goldenSets.length === 0 ? (
        <LoadingState message="Loading golden sets..." />
      ) : goldenSets.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No golden sets yet</h3>
            <p className="text-gray-500 mb-4">
              Create your first golden test set to start systematic evaluation.
            </p>
            <Button onClick={() => setIsCreateModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
              Create Golden Set
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">{total} golden set{total !== 1 ? 's' : ''}</p>
          {goldenSets.map((goldenSet) => (
            <GoldenSetCard
              key={goldenSet.id}
              goldenSet={goldenSet}
              onClick={() => navigate(`/golden-sets/${goldenSet.id}`)}
              onDelete={() => openDeleteModal(goldenSet.id)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Golden Test Set"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              isLoading={isSubmitting}
              disabled={!newSetName.trim()}
            >
              Create
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={newSetName}
              onChange={(e) => setNewSetName(e.target.value)}
              placeholder="e.g., Customer Support v1"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={newSetDescription}
              onChange={(e) => setNewSetDescription(e.target.value)}
              placeholder="Optional description of this test set..."
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
            />
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Delete Golden Set"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete} isLoading={isSubmitting}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-gray-600">
          Are you sure you want to delete this golden set? This will also delete all test
          cases and evaluation runs. This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}
