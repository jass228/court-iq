import typer
from src.ingest.load import load_pdf
from src.ingest.chunk import chunk_document
from src.ingest.store import create_vector_store


app = typer.Typer(help="CLI for indexing PDF files into a vector store.")


@app.command()
def run_index(
    pdf_path: str = typer.Option(
        ..., "--pdf-path", "-pp", help="Path to the PDF file to index"
    ),
    persist_directory: str = typer.Option(
        None, "--vector-store", "-vs", help="Directory to persist the vector store"
    ),
    collection_name: str = typer.Option(
        None,
        "--collection-name",
        "-cn",
        help="Name of the collection in the vector store",
    ),
):
    docs = load_pdf(pdf_path)
    chunks = [chunk for doc in docs for chunk in chunk_document(doc)]
    vs = create_vector_store(
        chunks=chunks,
        persist_directory=persist_directory,
        collection_name=collection_name,
    )

    print(f"Indexed {vs._collection.count()} chunks.")
