"""Document chunking logic for Bitext Q&A pairs."""
import tiktoken
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BitetChunker:
    """Chunker for Bitext customer support Q&A pairs.

    Uses Option A (simple approach):
    - Treat each Q&A pair as a single chunk
    - Preserve metadata (category, intent, flags)
    - Split longer answers if needed with overlap
    """

    def __init__(self, max_tokens: int = 500, overlap: int = 50, encoding_name: str = "cl100k_base"):
        """Initialize chunker.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Token overlap for split chunks
            encoding_name: Tiktoken encoding (matches OpenAI models)
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def chunk_qa_pair(self, qa_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk a single Q&A pair from Bitext dataset.

        Args:
            qa_item: Dictionary with keys: instruction, response, category, intent, flags

        Returns:
            List of chunk dictionaries with 'text' and 'metadata'
        """
        question = qa_item.get("instruction", "")
        answer = qa_item.get("response", "")
        category = qa_item.get("category", "unknown")
        intent = qa_item.get("intent", "unknown")
        flags = qa_item.get("flags", "")

        # Create full Q&A text
        qa_text = f"Q: {question}\nA: {answer}"

        # Check if it fits in single chunk
        token_count = self.count_tokens(qa_text)

        if token_count <= self.max_tokens:
            # Single chunk - most common case
            return [{
                "text": qa_text,
                "metadata": {
                    "category": category,
                    "intent": intent,
                    "flags": flags,
                    "question": question,
                    "token_count": token_count,
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            }]
        else:
            # Split long answer into multiple chunks
            logger.info(f"Splitting long answer ({token_count} tokens) for intent: {intent}")
            return self._split_long_answer(question, answer, category, intent, flags)

    def _split_long_answer(
        self,
        question: str,
        answer: str,
        category: str,
        intent: str,
        flags: str
    ) -> List[Dict[str, Any]]:
        """Split a long answer into multiple chunks with question context.

        Strategy:
        - Split answer by sentences
        - Include question in each chunk
        - Add overlap between chunks
        """
        # Split answer into sentences (simple approach)
        sentences = self._split_into_sentences(answer)

        chunks = []
        current_chunk_sentences = []
        current_tokens = self.count_tokens(f"Q: {question}\nA: ")

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # Check if adding this sentence would exceed max_tokens
            if current_tokens + sentence_tokens > self.max_tokens and current_chunk_sentences:
                # Save current chunk
                chunk_text = f"Q: {question}\nA: " + " ".join(current_chunk_sentences)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "category": category,
                        "intent": intent,
                        "flags": flags,
                        "question": question,
                        "token_count": self.count_tokens(chunk_text),
                        "chunk_index": len(chunks),
                        "total_chunks": -1  # Will update later
                    }
                })

                # Start new chunk with overlap
                # Keep last sentence for overlap
                if self.overlap > 0 and current_chunk_sentences:
                    current_chunk_sentences = [current_chunk_sentences[-1]]
                    current_tokens = self.count_tokens(f"Q: {question}\nA: " + current_chunk_sentences[0])
                else:
                    current_chunk_sentences = []
                    current_tokens = self.count_tokens(f"Q: {question}\nA: ")

            current_chunk_sentences.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk_sentences:
            chunk_text = f"Q: {question}\nA: " + " ".join(current_chunk_sentences)
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "category": category,
                    "intent": intent,
                    "flags": flags,
                    "question": question,
                    "token_count": self.count_tokens(chunk_text),
                    "chunk_index": len(chunks),
                    "total_chunks": -1
                }
            })

        # Update total_chunks count
        total = len(chunks)
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = total

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitter.

        Uses basic punctuation splitting. Could be enhanced with spaCy/NLTK.
        """
        import re

        # Split on sentence-ending punctuation followed by space
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_batch(self, qa_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk a batch of Q&A pairs.

        Args:
            qa_items: List of Q&A dictionaries

        Returns:
            Flat list of all chunks
        """
        all_chunks = []

        for idx, qa_item in enumerate(qa_items):
            chunks = self.chunk_qa_pair(qa_item)

            # Add source document ID to metadata
            for chunk in chunks:
                chunk["metadata"]["source_doc_id"] = idx

            all_chunks.extend(chunks)

        logger.info(f"Chunked {len(qa_items)} Q&A pairs into {len(all_chunks)} chunks")
        return all_chunks
