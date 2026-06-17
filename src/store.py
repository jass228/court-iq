from langchain_chroma import Chroma
from langchain_core.documents import Document

from .ingest.context import build_contextual_text
from .embed import get_embeddings

DEFAULT_PERSIST_DIRECTORY = "storage/chroma"
DEFAULT_COLLECTION_NAME = "fiba_rules"


def _clean_metadata(metadata: dict) -> dict:
    """Remove any keys with None values from the metadata dictionary."""
    return {k: v for k, v in metadata.items() if v is not None}


def to_contextual_docs(chunks: list[Document]) -> list[Document]:
    """Convert a list of chunked Documents into contextual Documents."""
    return [
        Document(
            page_content=build_contextual_text(chunk),
            metadata=_clean_metadata(chunk.metadata),
        )
        for chunk in chunks
    ]


def create_vector_store(
    chunks: list[Document],
    persist_directory: str | None = None,
    collection_name: str | None = None,
) -> Chroma:
    """Create a Chroma vector store from a list of chunked Documents."""
    return Chroma.from_documents(
        documents=to_contextual_docs(chunks),
        embedding=get_embeddings(),
        persist_directory=persist_directory or DEFAULT_PERSIST_DIRECTORY,
        collection_name=collection_name or DEFAULT_COLLECTION_NAME,
    )
