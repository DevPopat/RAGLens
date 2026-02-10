import { useState, useCallback } from 'react';
import { sendChatQuery } from '../api/chat';
import type { ChatMessage, Message, Source } from '../types';

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
    clearChat,
  };
}
