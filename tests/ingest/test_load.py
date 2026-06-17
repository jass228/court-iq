from pathlib import Path
import pytest
from langchain_core.documents import Document
from src.ingest.load import load_pdf

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PATH_FIBA = str(DATA_DIR / "fiba_rules_en.pdf")


@pytest.fixture(scope="module")
def docs() -> list[Document]:
    """Parse the FIBA PDF once and share the result across the module."""
    return load_pdf(PATH_FIBA)


@pytest.fixture(scope="module")
def blob(docs: list[Document]) -> str:
    """All section texts concatenated, for corpus-wide content checks."""
    return "\n".join(d.page_content for d in docs)


def section(docs: list[Document], section_no: str) -> Document:
    """Return the single Document for a given section number."""
    return next(d for d in docs if d.metadata["section_no"] == section_no)


def test_returns_enough_sections(docs: list[Document]) -> None:
    assert len(docs) > 150


def test_section_metadata(docs: list[Document]) -> None:
    s = section(docs, "2.5.7")
    assert s.metadata["page_start"] == 9
    assert s.metadata["page_end"] == 9
    assert s.metadata["article_no"] == "2"


def test_section_keeps_measurement(docs: list[Document]) -> None:
    assert "1.30 m" in section(docs, "2.5.7").page_content


def test_section_spans_two_pages(docs: list[Document]) -> None:
    g = section(docs, "9.4")
    assert g.metadata["page_start"] == 16
    assert g.metadata["page_end"] == 17


def test_noise_is_stripped(blob: str) -> None:
    assert "TABLE OF CONTENTS" not in blob
    assert "Page 9 of 105" not in blob


def test_appendix_sections_excluded(docs: list[Document]) -> None:
    assert all(not (d.metadata["section_no"] or "").startswith("D.") for d in docs)


def test_keeps_body_text(blob: str) -> None:
    assert "accompanying" in blob
