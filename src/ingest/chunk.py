from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_document(
    doc: Document, chunk_size: int = 512, chunk_overlap: int = 50
) -> list[Document]:
    """Chunk a Document into smaller Documents, preserving metadata."""
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents([doc])
    return chunks
