from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """
    You are Court IQ, an assistant for official basketball rules.
    Rules:
    - Base every statement strictly on the context; never use outside knowledge.
    - Cite the exact rule you relied on (e.g. 'FIBA Art. 8.1').
    - If the answer is not in the context, say clearly that it is not in the provided rules. Do not invent.
    - Reply in the same language as the question.
"""

GROUNDED_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)


def format_docs(docs: list[Document]) -> str:
    """Concatenate retrieved chunks into a single context block."""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)
