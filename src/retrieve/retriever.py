from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from src.ingest.embed import get_embeddings


def get_retriever(
    top_k: int = 5,
    persist_directory: str = "storage/chroma",
    collection_name: str = "fiba_rules",
) -> VectorStoreRetriever:
    """Connect to the persisted Chroma index and expose it as a retriever."""
    vectorestore = Chroma(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_function=get_embeddings(),
    )

    return vectorestore.as_retriever(search_kwargs={"k": top_k})
