import re

# Cleaning: line-level noise you can freely extend.
FOOTER_PATTERNS = [
    re.compile(r"^Page \d+ of \d+$"),
    re.compile(r"^OFFICIAL BASKETBALL RULES 2024$"),
    re.compile(r"^April 2026$"),
]
RE_DOTS = re.compile(r"\.{4,}")  # TOC / index dot leaders
_MULTISPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Collapse runs of whitespace and trim."""
    return _MULTISPACE.sub(" ", text).strip()


def join_lines(lines: list[str]) -> str:
    """Join lines into a single string, normalizing whitespace."""
    parts: list[str] = []
    for line in lines:
        if parts and parts[-1].endswith("-"):
            parts[-1] = parts[-1][:-1] + line
        else:
            parts.append(line)
    return " ".join(parts)


def clean_lines(text: str):
    """Clean the input text by removing empty lines,
    lines with only dots, and footer lines.
    """
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if RE_DOTS.search(line):
            continue
        if any(pat.match(line) for pat in FOOTER_PATTERNS):
            continue
        yield line
