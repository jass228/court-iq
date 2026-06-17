from langchain_core.documents import Document


def build_contextual_text(doc: Document) -> str:
    """Prefix a chunk with its hierarchical context."""
    meta = doc.metadata
    parts: list[str] = [f"{meta['league'].upper()} rules"]

    if meta.get("rule_no"):
        parts.append(f"Rule {meta['rule_no'].title()}: {meta['rule_title'].title()}")

    if meta.get("article_no"):
        parts.append(f"Article {meta['article_no'].title()}: {meta['article_title']}")

    if meta.get("section_no"):
        parts.append(f"§{meta['section_no']}")

    header = " | ".join(parts)
    return f"{header}\n\n{doc.page_content}"
