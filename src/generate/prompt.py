from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT_GROUNDED = """
    You are Court IQ, an assistant for official basketball rules (FIBA and NBA).
    Answer using ONLY the context below (official rule excerpts). Never use outside knowledge.

    Rules:
    - Answer directly and concisely — one or two sentences. Do not restate the answer or add filler ("Therefore", "The answer is", "La réponse est donc").
    - Paraphrase the rule in your own words; do not copy sentences from the context verbatim.
    - Use only the parts of the context relevant to the question; ignore unrelated sentences.
    - Each excerpt is prefixed with a citation tag in brackets, e.g. [FIBA Art. 8.1]. Give exactly ONE citation, in parentheses at the very end — never inline, never repeated. Copy the tag exactly as shown, including the league name.
    - If the answer is not in the context, say clearly that it is not in the provided rules. Do not invent.
    - Reply in the same language as the question.
"""

SYSTEM_PROMPT_COMPARISON = """
    You are Court IQ, an assistant for official basketball rules (FIBA and NBA).
    The context contains official rule excerpts from multiple leagues, grouped under '=== LEAGUE ===' headers.
    Compare the leagues on the user's question, using ONLY the context.
    
    Rules:
    - For each league, state its rule in one sentence with its bracketed citation tag.
    - Label each league's line with its name and a colon (e.g. "FIBA:", "NBA:"). Do not print a literal "LEAGUE:" line, and do not repeat the "===" headers.
    - End with a one-line summary stating WHAT differs and BY HOW MUCH (e.g. "NBA quarters are 2 minutes longer: 12 vs 10"), or state they are identical.
    - If a league's answer is not in its context, say so for that league.
    - Reply in the same language as the question.
"""

GROUNDED_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT_GROUNDED),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)

COMPARE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT_COMPARISON),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)


def _citation(meta: dict) -> str:
    """Human-readable citation from a chunk's metadata (handles FIBA and NBA)."""
    league = meta.get("league", "").upper()
    if meta.get("article_no"):  # FIBA: section_no encode rule.article.section
        ref = f"Art. {meta.get('section_no') or meta['article_no']}"
    else:  # NBA: Rule N, Section <roman>
        ref = f"Rule {meta['rule_no']}"
        if meta.get("section_no"):
            ref += f", Section {meta['section_no']}"
    return f"{league} {ref}".strip()


def format_docs(docs: list[Document]) -> str:
    """Concatenate retrieved chunks into a single context block."""
    blocks = []
    for doc in docs:
        body = doc.page_content.split("\n\n", 1)[-1]  # strip the contextual header
        blocks.append(f"[{_citation(doc.metadata)}]\n{body}")
    return "\n\n---\n\n".join(blocks)
