import re
from dataclasses import dataclass, field
from langchain_core.documents import Document
from .extract import extract_pages
from .clean import clean_lines, normalize_text, join_lines
from .source import parse_source_name
from config.settings import DOC_TITLE, VALID_FROM, SOURCE


# Structure detectors (anchored: inline refs never match).
RE_RULE = re.compile(r"^RULE\s+([A-Z]+)\s+–\s+(.+)$")
RE_ARTICLE = re.compile(r"^Article\s+(\d+)$")
RE_SECTION = re.compile(r"^(\d+(?:\.\d+)+)$")
RE_DIAGRAM = re.compile(r"^Diagram\s+\d+\b")


@dataclass
class ParserState:
    """The section currently being assembled, plus its metadata."""

    rule_no: str | None = None
    rule_title: str | None = None
    article_no: str | None = None
    article_title: str | None = None
    section_no: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    buffer: list[str] = field(default_factory=list)


def flush(state: ParserState, league: str, language: str) -> Document | None:
    """Build one Document from the buffered text, then reset the buffer."""
    content = normalize_text(join_lines(state.buffer))
    state.buffer.clear()

    if not content or state.article_no is None:
        return None

    return Document(
        page_content=content,
        metadata={
            "league": league,
            "language": language,
            "doc_title": DOC_TITLE,
            "valid_from": VALID_FROM,
            "rule_no": state.rule_no,
            "rule_title": state.rule_title,
            "article_no": state.article_no,
            "article_title": state.article_title,
            "section_no": state.section_no,
            "page_start": state.page_start,
            "page_end": state.page_end,
            "source": SOURCE,
        },
    )


def load_pdf(pdf_path: str) -> list[Document]:
    """Load a PDF file and extract its sections as a list of Document objects."""
    sections: list[Document] = []
    state = ParserState()

    started = False
    expecting_article_title = False
    expecting_diagram_caption = False

    league, language = parse_source_name(pdf_path)

    for page_no, text in extract_pages(pdf_path):
        for line in clean_lines(text):
            if not started:
                if line.startswith("RULE ONE"):
                    started = True
                else:
                    continue

            if line.startswith("APPENDIX"):
                doc = flush(state, league, language)
                if doc is not None:
                    sections.append(doc)
                return sections

            # The line right after "Article N" is its title.
            if expecting_article_title:
                state.article_title = line
                expecting_article_title = False
                continue

            # The line right after "Diagram N" is its caption: drop it so it
            # neither pollutes the section text nor inflates page_end.
            if expecting_diagram_caption:
                expecting_diagram_caption = False
                continue

            m = RE_RULE.match(line)
            if m:
                doc = flush(state, league, language)
                if doc is not None:
                    sections.append(doc)
                state.rule_no, state.rule_title = m.group(1), m.group(2)
                state.article_no = None
                state.article_title = None
                state.section_no = None
                continue

            m = RE_ARTICLE.match(line)
            if m:
                doc = flush(state, league, language)
                if doc is not None:
                    sections.append(doc)
                state.article_no = m.group(1)
                state.article_title = None
                state.section_no = None
                state.page_start = page_no
                state.page_end = page_no
                expecting_article_title = True
                continue

            m = RE_SECTION.match(line)
            if m:
                doc = flush(state, league, language)
                if doc is not None:
                    sections.append(doc)
                state.section_no = m.group(1)
                state.page_start = page_no
                state.page_end = page_no
                continue

            if RE_DIAGRAM.match(line):
                # Diagrams are not part of the text content; skip the marker
                # and its caption (the next line).
                expecting_diagram_caption = True
                continue

            state.buffer.append(line)
            state.page_end = page_no

    doc = flush(state, league, language)  # don't forget the last section
    if doc is not None:
        sections.append(doc)

    return sections
