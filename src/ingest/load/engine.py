from collections.abc import Callable
from dataclasses import dataclass, field
from langchain_core.documents import Document
from ..extract import extract_pages
from ..clean import clean_lines, normalize_text, join_lines


# --------------------------------------------------------------------------- #
# Shared parser state — superset of every league's fields. A given dialect only
# fills the levels it has (NBA leaves article_* as None, FIBA section_title).
# --------------------------------------------------------------------------- #
@dataclass
class ParserState:
    """The section currently being assembled, plus its metadata."""

    rule_no: str | None = None
    rule_title: str | None = None
    article_no: str | None = None
    article_title: str | None = None
    section_no: str | None = None
    section_title: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    buffer: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# A Dialect = everything that varies between leagues, expressed as data.
# The engine below is identical for all of them.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Dialect:
    doc_title: str
    valid_from: str
    source: str
    detectors: tuple[tuple, ...]                  # (regex, handler(eng, match))
    is_start: Callable[[str], bool]              # first line that opens the body
    is_stop: Callable[[str], bool]               # line that ends parsing
    is_valid: Callable[[ParserState], bool]      # is the buffered section real?
    is_noise: Callable[[str], bool] = lambda line: False  # footers, etc.


@dataclass
class _Engine:
    """Mutable run context threaded through the handlers."""

    state: ParserState
    sections: list[Document]
    dialect: Dialect
    league: str
    language: str
    page_no: int = 0
    consume_next: Callable[["_Engine", str], None] | None = None  # one-shot lookahead


def _emit(eng: "_Engine") -> None:
    """Build one Document from the buffered text, then reset the buffer."""
    s = eng.state
    content = normalize_text(join_lines(s.buffer))
    s.buffer.clear()

    if not content or not eng.dialect.is_valid(s):
        return

    eng.sections.append(
        Document(
            page_content=content,
            metadata={
                "league": eng.league,
                "language": eng.language,
                "doc_title": eng.dialect.doc_title,
                "valid_from": eng.dialect.valid_from,
                "rule_no": s.rule_no,
                "rule_title": s.rule_title,
                "article_no": s.article_no,
                "article_title": s.article_title,
                "section_no": s.section_no,
                "section_title": s.section_title,
                "page_start": s.page_start,
                "page_end": s.page_end,
                "source": eng.dialect.source,
            },
        )
    )


def run(pdf_path: str, dialect: Dialect, league: str, language: str) -> list[Document]:
    """Drive any dialect over a PDF, emitting one Document per section."""
    eng = _Engine(ParserState(), [], dialect, league, language)
    started = False

    for page_no, text in extract_pages(pdf_path):
        eng.page_no = page_no
        for line in clean_lines(text):
            if dialect.is_noise(line):
                continue

            if not started:
                if dialect.is_start(line):
                    started = True
                else:
                    continue

            if dialect.is_stop(line):
                _emit(eng)
                return eng.sections

            # One-shot lookahead (article title, diagram caption) claims this line.
            if eng.consume_next is not None:
                handler, eng.consume_next = eng.consume_next, None
                handler(eng, line)
                continue

            for pattern, handler in dialect.detectors:
                m = pattern.match(line)
                if m:
                    handler(eng, m)
                    break
            else:
                eng.state.buffer.append(line)
                eng.state.page_end = page_no

    _emit(eng)  # don't forget the last section
    return eng.sections
