from langchain_core.documents import Document
from ..source import parse_source_name
from .engine import run
from .dialects import DIALECTS


def load_pdf(pdf_path: str) -> list[Document]:
    """Load a PDF and extract its sections as Documents, picking the dialect
    from the filename convention (<corpus>_..._<language>.pdf)."""
    league, language = parse_source_name(pdf_path)
    return run(pdf_path, DIALECTS[league], league, language)
