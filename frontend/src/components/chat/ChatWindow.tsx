import { useRef, useEffect } from 'react';
import { Bot, Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import type { Message } from '../../types';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

export default function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Bot className="w-8 h-8 text-primary-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Welcome to RAGLens Chat
          </h2>
          <p className="text-gray-500 text-sm">
            Ask questions about your indexed documents. Your queries will be answered using
            retrieval-augmented generation with automatic evaluation.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
        {isLoading && (
          <div className="flex gap-3 animate-fade-in">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
              <Bot className="w-5 h-5 text-gray-600" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
