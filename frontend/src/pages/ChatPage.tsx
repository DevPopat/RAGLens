import { useState } from 'react';
import { Trash2, Clock, Coins, Zap } from 'lucide-react';
import ChatWindow from '../components/chat/ChatWindow';
import ChatInput from '../components/chat/ChatInput';
import SourcesPanel from '../components/chat/SourcesPanel';
import Button from '../components/common/Button';
import useChat from '../hooks/useChat';

export default function ChatPage() {
  const { messages, sources, isLoading, error, lastResponse, sendMessage, clearChat } =
    useChat();
  const [sourcesExpanded, setSourcesExpanded] = useState(true);
  const [llmProvider, setLlmProvider] = useState<'anthropic' | 'openai'>('anthropic');

  const handleSendMessage = (message: string) => {
    sendMessage(message, llmProvider);
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold text-gray-900">Chat</h1>
          <select
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.target.value as 'anthropic' | 'openai')}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
          >
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
          </select>
        </div>
        <div className="flex items-center gap-3">
          {lastResponse && (
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {Math.round(lastResponse.latency_ms)}ms
              </span>
              <span className="flex items-center gap-1">
                <Zap className="w-4 h-4" />
                {lastResponse.token_usage.total_tokens} tokens
              </span>
              <span className="flex items-center gap-1">
                <Coins className="w-4 h-4" />$
                {lastResponse.cost.toFixed(4)}
              </span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
            leftIcon={<Trash2 className="w-4 h-4" />}
            disabled={messages.length === 0}
          >
            Clear
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col">
          <ChatWindow messages={messages} isLoading={isLoading} />
          <ChatInput
            onSend={handleSendMessage}
            isLoading={isLoading}
            placeholder="Ask a question about your documents..."
          />
        </div>
        <SourcesPanel
          sources={sources}
          isExpanded={sourcesExpanded}
          onToggle={() => setSourcesExpanded(!sourcesExpanded)}
        />
      </div>
    </div>
  );
}
