import { User, Bot } from 'lucide-react';
import type { ChatMessage } from '../../types';

interface MessageBubbleProps {
  message: ChatMessage;
  isSelected?: boolean;
  onSelect?: () => void;
}

export default function MessageBubble({ message, isSelected = false, onSelect }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isClickable = !!onSelect;

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-fade-in`}
    >
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary-100' : 'bg-gray-100'
        }`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-primary-600" />
        ) : (
          <Bot className="w-5 h-5 text-gray-600" />
        )}
      </div>
      <div
        onClick={onSelect}
        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary-600 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-900 rounded-bl-md'
        } ${
          isClickable ? 'cursor-pointer hover:ring-2 hover:ring-primary-300 transition-shadow' : ''
        } ${
          isSelected ? 'ring-2 ring-primary-500' : ''
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
      </div>
    </div>
  );
}
