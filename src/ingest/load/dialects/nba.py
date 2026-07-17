import re
from config.settings import DOC_TITLE_NBA, VALID_FROM_NBA, SOURCE_NBA
from ..engine import Dialect, _Engine, _emit

RE_RULE_NBA = re.compile(r"^RULE NO\. (\d+[A-Z]?)—(.+)$")
RE_SECTION_NBA = re.compile(r"^Section\s+([IVXLCDM]+)\s*[—–]\s*(.+)$")
RE_FOOTER_NBA = re.compile(r"^- \d+ -$")


def _on_rule_nba(eng: _Engine, m: re.Match) -> None:
    _emit(eng)
    s = eng.state
    s.rule_no, s.rule_title = m.group(1), m.group(2).strip()
    s.section_no = s.section_title = None
    s.page_start = s.page_end = eng.page_no


def _on_section_nba(eng: _Engine, m: re.Match) -> None:
    _emit(eng)
    s = eng.state
    s.section_no, s.section_title = m.group(1), m.group(2).strip()
    s.page_start = s.page_end = eng.page_no


NBA = Dialect(
    doc_title=DOC_TITLE_NBA,
    valid_from=VALID_FROM_NBA,
    source=SOURCE_NBA,
    detectors=(
        (RE_RULE_NBA, _on_rule_nba),
        (RE_SECTION_NBA, _on_section_nba),
    ),
    is_start=lambda line: bool(RE_RULE_NBA.match(line)),
    is_stop=lambda line: line.strip() == "COMMENTS ON THE RULES",
    is_valid=lambda s: s.rule_no is not None,  # NBA has no article level
    is_noise=lambda line: bool(RE_FOOTER_NBA.match(line)),
)
