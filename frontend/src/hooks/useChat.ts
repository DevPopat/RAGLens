import { useState, useCallback } from 'react';
import { sendChatQuery } from '../api/chat';
import type { Message, ChatResponse, Source } from '../types';

const STORAGE_KEYS = {
  messages: 'raglens_chat_messages',
  sources: 'raglens_chat_sources',
  lastResponse: 'raglens_chat_lastResponse',
} as const;

function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : fallback;
  } catch {
    return fallback;
  }
}

interface UseChatReturn {
  messages: Message[];
  sources: Source[];
  isLoading: boolean;
  error: string | null;
  lastResponse: ChatResponse | null;
  sendMessage: (query: string, llmProvider?: 'anthropic' | 'openai') => Promise<void>;
  clearChat: () => void;
}

export default function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>(() => loadFromStorage(STORAGE_KEYS.messages, []));
  const [sources, setSources] = useState<Source[]>(() => loadFromStorage(STORAGE_KEYS.sources, []));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(() => loadFromStorage(STORAGE_KEYS.lastResponse, null));

  const persistMessages = useCallback((msgs: Message[]) => {
    setMessages(msgs);
    localStorage.setItem(STORAGE_KEYS.messages, JSON.stringify(msgs));
  }, []);

  const persistSources = useCallback((src: Source[]) => {
    setSources(src);
    localStorage.setItem(STORAGE_KEYS.sources, JSON.stringify(src));
  }, []);

  const persistLastResponse = useCallback((resp: ChatResponse | null) => {
    setLastResponse(resp);
    localStorage.setItem(STORAGE_KEYS.lastResponse, JSON.stringify(resp));
  }, []);

  const sendMessage = useCallback(
    async (query: string, llmProvider: 'anthropic' | 'openai' = 'anthropic') => {
      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const userMessage: Message = { role: 'user', content: query };
      const updatedMessages = [...messages, userMessage];
      persistMessages(updatedMessages);

      try {
        const response = await sendChatQuery({
          query,
          llm_provider: llmProvider,
          conversation_history: messages,
        });

        // Add assistant response
        const assistantMessage: Message = { role: 'assistant', content: response.response };
        persistMessages([...updatedMessages, assistantMessage]);
        persistSources(response.sources);
        persistLastResponse(response);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);
        // Remove the user message on error
        persistMessages(messages);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, persistMessages, persistSources, persistLastResponse]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setSources([]);
    setError(null);
    setLastResponse(null);
    localStorage.removeItem(STORAGE_KEYS.messages);
    localStorage.removeItem(STORAGE_KEYS.sources);
    localStorage.removeItem(STORAGE_KEYS.lastResponse);
  }, []);

  return {
    messages,
    sources,
    isLoading,
    error,
    lastResponse,
    sendMessage,
    clearChat,
  };
}
