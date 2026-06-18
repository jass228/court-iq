from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough
from .llm import get_llm
from .prompt import GROUNDED_PROMPT, format_docs
from src.retrieve.retriever import get_retriever


def build_chain(top_k: int = 5) -> Runnable:
    """Wire the RAG query pipeline"""
    retriever = get_retriever(top_k=top_k)
    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | GROUNDED_PROMPT
        | get_llm()
        | StrOutputParser()
    )
