import re
from config.settings import DOC_TITLE_FIBA, VALID_FROM_FIBA, SOURCE_FIBA
from ..engine import Dialect, _Engine, _emit

RE_RULE_FIBA = re.compile(r"^RULE\s+([A-Z]+)\s+–\s+(.+)$")
RE_ARTICLE_FIBA = re.compile(r"^Article\s+(\d+)$")
RE_SECTION_FIBA = re.compile(r"^(\d+(?:\.\d+)+)$")
RE_DIAGRAM_FIBA = re.compile(r"^Diagram\s+\d+\b")


def _capture_article_title(eng: _Engine, line: str) -> None:
    eng.state.article_title = line


def _skip_line(eng: _Engine, line: str) -> None:
    pass  # drop the diagram caption: it must not pollute text nor bump page_end


def _on_rule_fiba(eng: _Engine, m: re.Match) -> None:
    _emit(eng)
    s = eng.state
    s.rule_no, s.rule_title = m.group(1), m.group(2)
    s.article_no = s.article_title = s.section_no = None


def _on_article_fiba(eng: _Engine, m: re.Match) -> None:
    _emit(eng)
    s = eng.state
    s.article_no, s.article_title, s.section_no = m.group(1), None, None
    s.page_start = s.page_end = eng.page_no
    eng.consume_next = _capture_article_title  # next line is the article title


def _on_section_fiba(eng: _Engine, m: re.Match) -> None:
    _emit(eng)
    s = eng.state
    s.section_no = m.group(1)
    s.page_start = s.page_end = eng.page_no


def _on_diagram_fiba(eng: _Engine, m: re.Match) -> None:
    eng.consume_next = _skip_line  # drop marker + its caption (the next line)


FIBA = Dialect(
    doc_title=DOC_TITLE_FIBA,
    valid_from=VALID_FROM_FIBA,
    source=SOURCE_FIBA,
    detectors=(
        (RE_RULE_FIBA, _on_rule_fiba),
        (RE_ARTICLE_FIBA, _on_article_fiba),
        (RE_SECTION_FIBA, _on_section_fiba),
        (RE_DIAGRAM_FIBA, _on_diagram_fiba),
    ),
    is_start=lambda line: line.startswith("RULE ONE"),
    is_stop=lambda line: line.startswith("APPENDIX"),
    is_valid=lambda s: s.article_no is not None,
)
