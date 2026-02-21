export interface HighlightSpan {
  start: number;
  end: number;
  sourceIndex: number;
}

/**
 * Find spans in `answer` that appear verbatim in any of the `sourceTexts`.
 * Returns non-overlapping spans sorted by position.
 */
export function findSourceHighlights(
  answer: string,
  sourceTexts: string[],
  minLength: number = 20
): HighlightSpan[] {
  const answerLower = answer.toLowerCase();
  const spans: HighlightSpan[] = [];

  for (let si = 0; si < sourceTexts.length; si++) {
    const sourceLower = sourceTexts[si].toLowerCase();
    const step = Math.max(1, Math.floor(minLength / 4));

    for (let srcStart = 0; srcStart <= sourceLower.length - minLength; srcStart += step) {
      const candidate = sourceLower.substring(srcStart, srcStart + minLength);
      let answerIdx = answerLower.indexOf(candidate);

      while (answerIdx !== -1) {
        // Extend the match as far as possible
        let matchLen = minLength;
        while (
          srcStart + matchLen < sourceLower.length &&
          answerIdx + matchLen < answerLower.length &&
          sourceLower[srcStart + matchLen] === answerLower[answerIdx + matchLen]
        ) {
          matchLen++;
        }

        spans.push({ start: answerIdx, end: answerIdx + matchLen, sourceIndex: si });
        answerIdx = answerLower.indexOf(candidate, answerIdx + 1);
      }
    }
  }

  return mergeSpans(spans);
}

function mergeSpans(spans: HighlightSpan[]): HighlightSpan[] {
  if (spans.length === 0) return [];

  spans.sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));

  const merged: HighlightSpan[] = [spans[0]];

  for (let i = 1; i < spans.length; i++) {
    const last = merged[merged.length - 1];
    const curr = spans[i];

    if (curr.start < last.end) {
      if (curr.end > last.end) {
        last.end = curr.end;
      }
    } else {
      merged.push(curr);
    }
  }

  return merged;
}
