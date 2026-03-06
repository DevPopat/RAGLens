"""Enhanced prompt templates for RAG generation with metadata awareness."""

CUSTOMER_SUPPORT_SYSTEM_PROMPT = """You are a helpful customer support assistant. Your role is to provide accurate, friendly, and concise answers to customer questions.

Use the provided context from our knowledge base to answer the question. The context includes metadata about the category and intent to help you understand the context better.

Guidelines:
- Be professional and friendly
- Keep answers concise but complete
- Use information from the provided context
- If the context doesn't contain relevant information, politely say you don't have that information and suggest contacting support
- Provide step-by-step instructions when appropriate
- Adapt your tone based on the customer's question style (formal, casual, etc.)
- Do not use markdown formatting such as **bold**, *italic*, or bullet points. Write in plain text only."""


# Flag explanations for LLM understanding
FLAG_EXPLANATIONS = {
    # Lexical
    "M": "Morphological variation (inflections)",
    "L": "Semantic variation (synonyms, paraphrasing)",
    # Syntactic
    "B": "Basic syntactic structure",
    "I": "Interrogative structure (question form)",
    "C": "Coordinated structure (multiple clauses)",
    "N": "Negation present",
    # Register
    "P": "Polite/formal tone",
    "Q": "Colloquial/informal language",
    "W": "Offensive or frustrated language",
    # Stylistic
    "K": "Keyword mode (telegraphic)",
    "E": "Abbreviations used",
    "Z": "Contains errors or typos"
}


def parse_flags_for_prompt(flags: str) -> str:
    """Convert flag codes to human-readable description.

    Args:
        flags: Flag string like "BQZ"

    Returns:
        Human-readable description
    """
    if not flags:
        return "Standard query"

    descriptions = []
    for flag in flags:
        if flag in FLAG_EXPLANATIONS:
            descriptions.append(FLAG_EXPLANATIONS[flag])

    if descriptions:
        return "Query style: " + ", ".join(descriptions)
    return "Standard query"


def create_rag_prompt(query: str, contexts: list[dict]) -> str:
    """Create enhanced RAG prompt with query and retrieved contexts including metadata.

    Args:
        query: User's question
        contexts: List of retrieved context dicts with 'text', 'metadata', 'score'

    Returns:
        Formatted prompt string with metadata
    """
    # Format contexts with rich metadata
    context_blocks = []

    for i, ctx in enumerate(contexts):
        metadata = ctx.get('metadata', {})
        category = metadata.get('category', 'N/A')
        intent = metadata.get('intent', 'N/A')
        flags = metadata.get('flags', '')
        relevance = ctx.get('score', 0.0)

        # Parse flags for context
        flag_desc = parse_flags_for_prompt(flags)

        context_block = f"""[Context {i+1}]
Category: {category}
Intent: {intent}
{flag_desc}
Relevance Score: {relevance:.2f}

{ctx['text']}"""

        context_blocks.append(context_block)

    context_str = "\n\n" + "="*60 + "\n\n".join(context_blocks)

    prompt = f"""Context from knowledge base:
{context_str}

{"="*60}

Customer Question: {query}

Please provide a helpful answer based on the context above. Consider the category and intent of the retrieved contexts to ensure your response is relevant and appropriate."""

    return prompt


# For LLM-as-judge evaluation
EVALUATION_SYSTEM_PROMPT = """You are an expert evaluator assessing the quality of customer support chatbot responses.

Your task is to evaluate responses across multiple dimensions considering:
1. The customer's original query
2. The retrieved context that was provided to the chatbot
3. The chatbot's generated response
4. The expected category and intent from the knowledge base

Be objective and thorough in your evaluation."""


def create_evaluation_prompt(
    query: str,
    response: str,
    contexts: list[dict],
    expected_category: str = None,
    expected_intent: str = None
) -> str:
    """Create prompt for LLM-as-judge evaluation.

    Args:
        query: Original customer query
        response: Chatbot's response
        contexts: Retrieved contexts used
        expected_category: Expected category (if known from golden set)
        expected_intent: Expected intent (if known from golden set)

    Returns:
        Evaluation prompt
    """
    # Format contexts
    context_str = "\n\n".join([
        f"[Context {i+1}] (Category: {ctx['metadata'].get('category')}, "
        f"Intent: {ctx['metadata'].get('intent')}, "
        f"Flags: {ctx['metadata'].get('flags', 'None')}, "
        f"Relevance: {ctx['score']:.2f})\n{ctx['text']}"
        for i, ctx in enumerate(contexts)
    ])

    expected_info = ""
    if expected_category or expected_intent:
        expected_info = f"""
Expected Classification:
- Category: {expected_category or 'Not specified'}
- Intent: {expected_intent or 'Not specified'}
"""

    prompt = f"""Evaluate the following customer support interaction:

CUSTOMER QUERY:
{query}

RETRIEVED CONTEXT PROVIDED TO CHATBOT:
{context_str}

CHATBOT'S RESPONSE:
{response}
{expected_info}

Please evaluate the response on the following criteria (score each 0-5):

1. **Accuracy**: Is the information factually correct based on the provided context?
   - 5: Completely accurate, all facts verified against context
   - 3: Mostly accurate with minor issues
   - 0: Contains incorrect information

2. **Completeness**: Does it fully address the customer's question?
   - 5: Fully comprehensive, covers all aspects
   - 3: Addresses main points but misses some details
   - 0: Incomplete or missing key information

3. **Faithfulness**: Is the response grounded in the provided context?
   - 5: Entirely based on context, no hallucinations
   - 3: Mostly grounded with some unsupported statements
   - 0: Makes claims not supported by context

4. **Tone**: Is the tone appropriate for customer support?
   - 5: Professional, friendly, and empathetic
   - 3: Acceptable but could be warmer/more professional
   - 0: Inappropriate tone (too casual, rude, or cold)

5. **Relevance**: Is the response relevant to the query's category and intent?
   - 5: Perfect match for category/intent
   - 3: Related but may address wrong aspect
   - 0: Completely off-topic

6. **Clarity**: Is the response clear and easy to understand?
   - 5: Crystal clear, well-structured
   - 3: Understandable but could be clearer
   - 0: Confusing or poorly structured

Provide your evaluation in the following JSON format:
{{
    "scores": {{
        "accuracy": <0-5>,
        "completeness": <0-5>,
        "faithfulness": <0-5>,
        "tone": <0-5>,
        "relevance": <0-5>,
        "clarity": <0-5>
    }},
    "overall_score": <average of above scores>,
    "explanation": "<brief explanation of your scoring>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"],
    "suggested_improvement": "<optional suggestion for improvement>"
}}"""

    return prompt


# Template for evaluation with expected answer (golden set)
def create_golden_set_evaluation_prompt(
    query: str,
    response: str,
    expected_answer: str,
    contexts: list[dict],
    category: str,
    intent: str
) -> str:
    """Create evaluation prompt when we have expected answer from golden set.

    Args:
        query: Customer query
        response: Chatbot response
        expected_answer: Expected/ideal answer
        contexts: Retrieved contexts
        category: Expected category
        intent: Expected intent

    Returns:
        Evaluation prompt with expected answer comparison
    """
    context_str = "\n\n".join([
        f"[Context {i+1}] (Relevance: {ctx['score']:.2f})\n{ctx['text']}"
        for i, ctx in enumerate(contexts)
    ])

    prompt = f"""Evaluate this customer support interaction against the expected answer:

CUSTOMER QUERY:
{query}

EXPECTED CATEGORY: {category}
EXPECTED INTENT: {intent}

RETRIEVED CONTEXT:
{context_str}

EXPECTED/IDEAL ANSWER:
{expected_answer}

ACTUAL CHATBOT RESPONSE:
{response}

Evaluate how well the actual response matches the expected answer on these criteria (0-5 scale):

1. **Semantic Similarity**: Does it convey the same meaning as the expected answer?
2. **Information Coverage**: Does it include all key information from the expected answer?
3. **Accuracy**: Is all information correct?
4. **Tone Match**: Does it match the professional tone of the expected answer?
5. **Conciseness**: Is it appropriately concise (not too verbose or too brief)?

Provide evaluation in JSON format:
{{
    "scores": {{
        "semantic_similarity": <0-5>,
        "information_coverage": <0-5>,
        "accuracy": <0-5>,
        "tone_match": <0-5>,
        "conciseness": <0-5>
    }},
    "overall_score": <average>,
    "passes_threshold": <true if overall >= 4.0>,
    "explanation": "<explanation>",
    "key_differences": ["<difference 1>", "<difference 2>"]
}}"""

    return prompt


# --- Claim Comparison Prompt (used by /evaluation/compare-claims) ---

CLAIM_COMPARE_PROMPT = """You are comparing an expected answer against a generated answer.

Extract every distinct factual claim from the expected answer. For each claim, determine whether the generated answer:
- "covered": conveys the same information (even if worded differently)
- "missing": does not mention this information at all
- "contradicted": states something that conflicts with the claim

For claims that are "covered" or "contradicted", include the exact quote from the generated answer that corresponds to the claim. The quote must be a verbatim substring of the generated answer.

Expected answer:
{expected_answer}

Generated answer:
{generated_answer}

Respond with ONLY valid JSON — no markdown fences, no extra text:
{{"claims": [
  {{"claim": "...", "status": "covered|missing|contradicted", "detail": "brief explanation", "generated_quote": "exact substring from generated answer or null"}}
]}}"""

CLAIM_COMPARE_SYSTEM_PROMPT = "You are a precise factual comparison assistant. Respond only with valid JSON."


# --- Detailed Analysis Prompts (used by /evaluation/detailed-analysis) ---

DETAILED_ANALYSIS_SYSTEM_PROMPT = (
    "You are a precise RAG evaluation analyst. Respond only with valid JSON. "
    "Be specific and cite exact text from the inputs."
)

DETAILED_ANALYSIS_PROMPT_HEADER = """You are analyzing a RAG (Retrieval-Augmented Generation) system's response. Given the user's question, the generated response, and the retrieved contexts, provide a detailed breakdown.

The RAGAS framework scored this response: {scores_summary}

## INPUT

**User Question:**
{query}

**Generated Response:**
{response}

**Retrieved Contexts:**
{contexts_formatted}

## YOUR TASK

Analyze the response across the dimensions below. Be specific and cite exact text.

### 1. Faithfulness Analysis
Extract every distinct factual claim from the generated response. For each claim, determine whether it is:
- "supported": directly backed by information in the retrieved contexts
- "unsupported": not found in any retrieved context (hallucinated or assumed)
- "contradicted": directly conflicts with information in the contexts

For supported/contradicted claims, include the relevant quote from the context and which context (by 0-based index) it comes from. For unsupported claims, set source_quote and context_index to null.
"""

DETAILED_ANALYSIS_PROMPT_COVERAGE = """
### 2. Question Coverage Analysis
Break the user's question into its component sub-questions or intent parts. For each component, determine:
- "addressed": the response directly answers this component
- "partially_addressed": the response touches on this but incompletely
- "not_addressed": the response does not address this at all

For addressed/partially_addressed components, include the exact substring from the response that addresses it. For not_addressed, set response_quote to null.
"""

DETAILED_ANALYSIS_PROMPT_CONTEXT = """
### {section_num}. Context Utilization Analysis
For each retrieved context (by 0-based index), determine whether the response actually drew information from it:
- "used": the response clearly incorporates information from this context
- "partially_used": the response tangentially draws from this context
- "not_used": the response does not use this context at all

For used/partially_used contexts, include the exact substring from the response that reflects information from this context. For not_used, set used_in_response to null.
"""

DETAILED_ANALYSIS_FORMAT_WITH_COVERAGE = """
## OUTPUT FORMAT

Respond with ONLY valid JSON (no markdown fences, no extra text):
{{
  "faithfulness": {{
    "summary": "One sentence summarizing faithfulness issues",
    "claims": [
      {{"statement": "...", "verdict": "supported|unsupported|contradicted", "reason": "...", "source_quote": "exact quote from context or null", "context_index": 0}}
    ]
  }},
  "answer_relevancy": {{
    "summary": "One sentence summarizing question coverage",
    "components": [
      {{"component": "the sub-question or intent", "verdict": "addressed|partially_addressed|not_addressed", "response_quote": "exact substring from response or null", "reason": "..."}}
    ]
  }},
  "context_precision": {{
    "summary": "One sentence summarizing context utilization",
    "contexts": [
      {{"context_index": 0, "verdict": "used|partially_used|not_used", "used_in_response": "exact substring from response or null", "reason": "..."}}
    ]
  }}
}}"""

DETAILED_ANALYSIS_FORMAT_WITHOUT_COVERAGE = """
## OUTPUT FORMAT

Respond with ONLY valid JSON (no markdown fences, no extra text):
{{
  "faithfulness": {{
    "summary": "One sentence summarizing faithfulness issues",
    "claims": [
      {{"statement": "...", "verdict": "supported|unsupported|contradicted", "reason": "...", "source_quote": "exact quote from context or null", "context_index": 0}}
    ]
  }},
  "context_precision": {{
    "summary": "One sentence summarizing context utilization",
    "contexts": [
      {{"context_index": 0, "verdict": "used|partially_used|not_used", "used_in_response": "exact substring from response or null", "reason": "..."}}
    ]
  }}
}}"""


# Expose main functions
RAG_USER_PROMPT_TEMPLATE = create_rag_prompt
EVALUATION_PROMPT_TEMPLATE = create_evaluation_prompt
GOLDEN_SET_EVALUATION_TEMPLATE = create_golden_set_evaluation_prompt
