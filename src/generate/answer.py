from langchain_core.output_parsers import StrOutputParser
from .llm import get_llm
from .prompt import GROUNDED_PROMPT, COMPARE_PROMPT, format_docs
from src.retrieve.retriever import get_retriever
from src.retrieve.classify import classify_query

AVAILABLE_LEAGUES = {"fiba", "nba"}


def retrieve_context(question: str, leagues: list[str] | None, top_k: int = 5) -> str:
    """Retrieve context for a question, filtered to the given league(s)."""
    docs = get_retriever(top_k=top_k, league=leagues).invoke(question)
    return format_docs(docs)


def league_context(question: str, league: str, top_k: int = 5) -> str:
    """Retrieve one league's chunks, labelled under a === LEAGUE === header."""
    docs = get_retriever(top_k=top_k, league=[league]).invoke(question)
    return f"=== {league.upper()} ===\n\n{format_docs(docs)}"


def answer_grounded(question: str, leagues: list[str] | None, top_k: int = 5) -> str:
    """Grounded single-answer path: filtered retrieval, then generate."""
    context = retrieve_context(question, leagues, top_k)
    chain = GROUNDED_PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({"context": context, "question": question})


def answer_comparison(question: str, leagues: list[str], top_k: int = 5) -> str:
    """Comparison path: retrieve each league separately, then compare."""
    context = "\n\n".join(league_context(question, lg, top_k) for lg in leagues)
    chain = COMPARE_PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({"context": context, "question": question})


def answer(question: str) -> str:
    """Classify once, then route to the right generation path."""
    cls = classify_query(question)

    if cls.intent == "out_of_scope":
        return (
            "❌ This question is out of scope for CourtIQ. "
            "Please ask about official basketball rules (FIBA or NBA)."
        )

    available = [lg for lg in cls.leagues if lg in AVAILABLE_LEAGUES]
    missing = [lg for lg in cls.leagues if lg not in AVAILABLE_LEAGUES]

    # Reject only when the user explicitly names a league we don't index.
    # (intent from a local LLM is noisy, so never hard-reject on intent alone.)
    if missing:
        return (
            f"❌ Unsupported league(s): {', '.join(missing)}. "
            f"Available: {', '.join(sorted(AVAILABLE_LEAGUES)).upper()}."
        )

    # Genuine comparison only when 2+ supported leagues are actually in play.
    if cls.intent == "comparison" and len(available) >= 2:
        return answer_comparison(question, available)

    # Everything else (incl. mislabeled comparisons): grounded, filtered or all.
    return answer_grounded(question, available or None)
