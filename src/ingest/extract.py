import pymupdf


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Extracts text from each page of a PDF file."""
    doc = pymupdf.open(pdf_path)
    pages = [(page.number + 1, page.get_text()) for page in doc]
    return pages
