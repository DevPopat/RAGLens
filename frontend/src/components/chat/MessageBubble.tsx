import { User, Bot, RefreshCw } from 'lucide-react';
import type { ChatMessage } from '../../types';
import SourceHighlightedText from '../common/SourceHighlightedText';

interface MessageBubbleProps {
  message: ChatMessage;
  isSelected?: boolean;
  onSelect?: () => void;
  onRegenerate?: () => void;
  isLoading?: boolean;
  selectedSources?: Set<number>;
}

export default function MessageBubble({ message, isSelected = false, onSelect, onRegenerate, isLoading = false, selectedSources }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isClickable = !!onSelect;
  const showHighlights = !isUser && selectedSources && selectedSources.size > 0 && message.sources && message.sources.length > 0;

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
      <div className="flex flex-col gap-1 max-w-[70%]">
        <div
          onClick={onSelect}
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-600 text-white rounded-br-md'
              : 'bg-gray-100 text-gray-900 rounded-bl-md'
          } ${
            isClickable ? 'cursor-pointer hover:ring-2 hover:ring-primary-300 transition-shadow' : ''
          } ${
            isSelected ? 'ring-2 ring-primary-500' : ''
          }`}
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {showHighlights ? (
              <SourceHighlightedText
                text={message.content}
                sources={message.sources!}
                selectedIndices={selectedSources}
              />
            ) : (
              message.content
            )}
          </p>
        </div>
        {onRegenerate && (
          <button
            onClick={onRegenerate}
            disabled={isLoading}
            className="self-start ml-1 p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 transition-colors"
            title="Regenerate response"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        )}
      </div>
    </div>
  );
}
