from langchain_ollama import ChatOllama


def get_llm() -> ChatOllama:
    """Build the Ollama chat model."""
    return ChatOllama(
        model="llama3.1",
        temperature=0,
    )
