from functools import lru_cache
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from .context import build_contextual_text


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """Return a HuggingFaceEmbeddings instance for generating embeddings."""
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "mps"},
        encode_kwargs={"normalize_embeddings": True},
    )


def embed_document(docs: list[Document], embeddings: Embeddings) -> list[list[float]]:
    """Generate embeddings for a Document's content, including its context."""
    contextual_text = [build_contextual_text(doc) for doc in docs]
    return embeddings.embed_documents(contextual_text)
