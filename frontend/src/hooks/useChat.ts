import { useState, useCallback } from 'react';
import { sendChatQuery } from '../api/chat';
import type { Message, ChatResponse, Source } from '../types';

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);

  const sendMessage = useCallback(
    async (query: string, llmProvider: 'anthropic' | 'openai' = 'anthropic') => {
      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const userMessage: Message = { role: 'user', content: query };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await sendChatQuery({
          query,
          llm_provider: llmProvider,
          conversation_history: messages,
        });

        // Add assistant response
        const assistantMessage: Message = { role: 'assistant', content: response.response };
        setMessages((prev) => [...prev, assistantMessage]);
        setSources(response.sources);
        setLastResponse(response);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);
        // Remove the user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [messages]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setSources([]);
    setError(null);
    setLastResponse(null);
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
