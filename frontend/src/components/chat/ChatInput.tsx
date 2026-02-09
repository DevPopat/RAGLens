import { useState, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  isLoading,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 focus:outline-none disabled:bg-gray-50 disabled:text-gray-500 text-sm"
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="flex-shrink-0 w-12 h-12 rounded-xl bg-primary-600 text-white flex items-center justify-center hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
