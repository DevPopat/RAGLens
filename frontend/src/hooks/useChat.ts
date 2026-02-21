import { useState, useCallback } from 'react';
import { sendChatQuery } from '../api/chat';
import { runEvaluation } from '../api/evaluation';
import type { ChatMessage, EvaluationResult, Message, Source } from '../types';

const STORAGE_KEYS = {
  messages: 'raglens_chat_messages',
} as const;

function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : fallback;
  } catch {
    return fallback;
  }
}

function migrateMessages(raw: unknown[]): ChatMessage[] {
  if (!Array.isArray(raw)) return [];

  // Recover old global sources for migration
  const oldSources = loadFromStorage<Source[]>('raglens_chat_sources', []);

  const migrated: ChatMessage[] = raw.map((msg: any) => ({
    id: msg.id || crypto.randomUUID(),
    role: msg.role,
    content: msg.content,
    ...(msg.role === 'assistant'
      ? {
          sources: msg.sources || [],
          ...(msg.latency_ms != null ? { latency_ms: msg.latency_ms } : {}),
          ...(msg.token_usage != null ? { token_usage: msg.token_usage } : {}),
          ...(msg.cost != null ? { cost: msg.cost } : {}),
          ...(msg.query_id != null ? { query_id: msg.query_id } : {}),
          ...(msg.evaluation != null ? { evaluation: msg.evaluation } : {}),
        }
      : {}),
  }));

  // Attach old global sources to the last assistant message if it has none
  if (oldSources.length > 0) {
    const lastAssistant = [...migrated].reverse().find((m) => m.role === 'assistant');
    if (lastAssistant && (!lastAssistant.sources || lastAssistant.sources.length === 0)) {
      lastAssistant.sources = oldSources;
    }
  }

  return migrated;
}

function toConversationHistory(messages: ChatMessage[]): Message[] {
  return messages.map(({ role, content }) => ({ role, content }));
}

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (query: string, llmProvider?: 'anthropic' | 'openai') => Promise<void>;
  regenerateMessage: (messageId: string, llmProvider?: 'anthropic' | 'openai') => Promise<void>;
  evaluateMessage: (messageId: string, evaluatorProvider?: 'anthropic' | 'openai') => Promise<EvaluationResult | null>;
  clearChat: () => void;
}

export default function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    migrateMessages(loadFromStorage(STORAGE_KEYS.messages, []))
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const persistMessages = useCallback((msgs: ChatMessage[]) => {
    setMessages(msgs);
    localStorage.setItem(STORAGE_KEYS.messages, JSON.stringify(msgs));
  }, []);

  const sendMessage = useCallback(
    async (query: string, llmProvider: 'anthropic' | 'openai' = 'anthropic') => {
      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: query,
      };
      const updatedMessages = [...messages, userMessage];
      persistMessages(updatedMessages);

      try {
        const response = await sendChatQuery({
          query,
          llm_provider: llmProvider,
          conversation_history: toConversationHistory(messages),
        });

        // Add assistant response with its sources and metrics
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.response,
          sources: response.sources,
          latency_ms: response.latency_ms,
          token_usage: response.token_usage,
          cost: response.cost,
          query_id: response.query_id,
        };
        persistMessages([...updatedMessages, assistantMessage]);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);
        // Remove the user message on error
        persistMessages(messages);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, persistMessages]
  );

  const regenerateMessage = useCallback(
    async (messageId: string, llmProvider: 'anthropic' | 'openai' = 'anthropic') => {
      const msgIndex = messages.findIndex((m) => m.id === messageId);
      if (msgIndex === -1 || messages[msgIndex].role !== 'assistant') return;

      // Find the preceding user message to get the original query
      const userMsg = messages
        .slice(0, msgIndex)
        .reverse()
        .find((m) => m.role === 'user');
      if (!userMsg) return;

      setIsLoading(true);
      setError(null);

      // Conversation history is everything before the user message
      const userMsgIndex = messages.indexOf(userMsg);
      const historyBefore = messages.slice(0, userMsgIndex);

      try {
        const response = await sendChatQuery({
          query: userMsg.content,
          llm_provider: llmProvider,
          conversation_history: toConversationHistory(historyBefore),
        });

        // Replace the assistant message in-place
        const updated = [...messages];
        updated[msgIndex] = {
          ...updated[msgIndex],
          content: response.response,
          sources: response.sources,
          latency_ms: response.latency_ms,
          token_usage: response.token_usage,
          cost: response.cost,
          query_id: response.query_id,
          evaluation: undefined,
        };
        persistMessages(updated);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to regenerate message';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, persistMessages]
  );

  const evaluateMessage = useCallback(
    async (
      messageId: string,
      evaluatorProvider: 'anthropic' | 'openai' = 'anthropic'
    ): Promise<EvaluationResult | null> => {
      const msgIndex = messages.findIndex((m) => m.id === messageId);
      if (msgIndex === -1 || messages[msgIndex].role !== 'assistant') return null;

      const assistantMsg = messages[msgIndex];
      if (!assistantMsg.query_id) return null;

      // Find the preceding user message
      const userMsg = messages
        .slice(0, msgIndex)
        .reverse()
        .find((m) => m.role === 'user');
      if (!userMsg) return null;

      // Build conversation history from all messages before the user message
      const userMsgIndex = messages.indexOf(userMsg);
      const historyBefore = messages.slice(0, userMsgIndex);
      const conversationHistory = historyBefore.length > 0
        ? toConversationHistory(historyBefore)
        : undefined;

      const response = await runEvaluation({
        query_id: assistantMsg.query_id,
        evaluator_provider: evaluatorProvider,
        conversation_history: conversationHistory,
      });

      // Map backend response to EvaluationResult
      const result: EvaluationResult = {
        evaluation_type: response.evaluation_type,
        scores: response.scores,
        evaluator: response.evaluator,
        metadata: response.metadata,
        timestamp: response.timestamp,
        latency_ms: response.latency_ms,
      };

      // Attach result to the message and persist
      const updated = [...messages];
      updated[msgIndex] = { ...updated[msgIndex], evaluation: result };
      persistMessages(updated);

      return result;
    },
    [messages, persistMessages]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    localStorage.removeItem(STORAGE_KEYS.messages);
    localStorage.removeItem('raglens_chat_lastResponse'); // Clean up deprecated key
    localStorage.removeItem('raglens_chat_sources'); // Clean up deprecated key
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    regenerateMessage,
    evaluateMessage,
    clearChat,
  };
}
