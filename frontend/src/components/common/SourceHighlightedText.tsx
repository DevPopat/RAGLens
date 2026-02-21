import { useMemo } from 'react';
import type { Source } from '../../types';
import { findSourceHighlights } from '../../utils/textHighlight';

interface SourceHighlightedTextProps {
  text: string;
  sources: Source[];
  selectedIndices: Set<number>;
}

export default function SourceHighlightedText({
  text,
  sources,
  selectedIndices,
}: SourceHighlightedTextProps) {
  const filteredSources = sources.filter((_, i) => selectedIndices.has(i));
  const highlights = useMemo(
    () => findSourceHighlights(text, filteredSources.map((s) => s.text)),
    [text, filteredSources]
  );

  if (highlights.length === 0) return <>{text}</>;

  const segments: React.ReactNode[] = [];
  let cursor = 0;
  for (const span of highlights) {
    if (cursor < span.start) {
      segments.push(<span key={`t-${cursor}`}>{text.slice(cursor, span.start)}</span>);
    }
    segments.push(
      <mark
        key={`h-${span.start}`}
        className="bg-amber-100 border-b-2 border-amber-400 rounded px-0.5"
        title={`From Source ${span.sourceIndex + 1}`}
      >
        {text.slice(span.start, span.end)}
      </mark>
    );
    cursor = span.end;
  }
  if (cursor < text.length) {
    segments.push(<span key={`t-${cursor}`}>{text.slice(cursor)}</span>);
  }

  return <>{segments}</>;
}
