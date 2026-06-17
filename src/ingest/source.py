from pathlib import Path


def parse_source_name(pdf_path: str) -> tuple[str, str]:
    """Derive (corpus, language) from a '<corpus>_..._<language>.pdf' filename."""
    stem = Path(pdf_path).stem
    parts = stem.split("_")
    if len(parts) < 2:
        raise ValueError(
            f"Cannot derive corpus/language from filename {stem!r}; "
            "expected '<corpus>_..._<language>'."
        )
    return parts[0], parts[-1]
