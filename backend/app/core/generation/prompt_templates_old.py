"""Prompt templates for RAG generation."""

CUSTOMER_SUPPORT_SYSTEM_PROMPT = """You are a helpful customer support assistant. Your role is to provide accurate, friendly, and concise answers to customer questions.

Use the provided context from our knowledge base to answer the question. If the context doesn't contain relevant information, politely say you don't have that information and suggest contacting support.

Guidelines:
- Be professional and friendly
- Keep answers concise but complete
- Use information from the provided context
- If unsure, acknowledge it honestly
- Provide step-by-step instructions when appropriate"""


def create_rag_prompt(query: str, contexts: list[dict]) -> str:
    """Create RAG prompt with query and retrieved contexts.

    Args:
        query: User's question
        contexts: List of retrieved context dicts with 'text', 'metadata', 'score'

    Returns:
        Formatted prompt string
    """
    # Format contexts
    context_str = "\n\n".join([
        f"[Context {i+1}] (Category: {ctx['metadata'].get('category', 'N/A')}, "
        f"Intent: {ctx['metadata'].get('intent', 'N/A')}, "
        f"Relevance: {ctx['score']:.2f})\n{ctx['text']}"
        for i, ctx in enumerate(contexts)
    ])

    prompt = f"""Context from knowledge base:

{context_str}

Customer Question: {query}

Please provide a helpful answer based on the context above:"""

    return prompt


RAG_USER_PROMPT_TEMPLATE = create_rag_prompt
