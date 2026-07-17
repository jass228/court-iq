# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CourtIQ is a bilingual (FR/EN) RAG assistant for basketball **rules and tactics**. A PDF rulebook is ingested into context-enriched, embedded chunks stored in Chroma, then queried via a grounded LLM chain. Today the FIBA rulebook ingestion → retrieval → answering path is fully wired; query classification, multi-corpus routing, and other corpora (NBA, EuroLeague, TheBAL) are scaffolded but not yet connected.

## Commands

```bash
uv sync                                              # install deps + the court-iq CLI
uv run court-iq index --pdf-path data/fiba_rules_en.pdf   # PDF -> Chroma
uv run court-iq fiba                                  # interactive grounded Q&A
uv run pytest                                         # all tests
uv run pytest tests/ingest/test_load.py::test_section_metadata   # single test
```

- The query path needs **Ollama running locally** (`ollama serve`) with `llama3.1` pulled.
- Set `HF_HUB_OFFLINE=1` to skip the Hugging Face Hub round-trip (the bge-m3 model is cached locally).
- Embeddings default to Apple Silicon (`device="mps"` in `src/ingest/embed.py`); change it for CPU/CUDA.

## Architecture

Three stages under `src/`, orchestrated by a Typer CLI in `apps/cli/`. The **`langchain_core.documents.Document` is the pivot type** throughout — there is no intermediate JSONL/serialization format.

**Ingest** (`src/ingest/`) — PDF → vectors, one stage per file:
`extract` (pymupdf → `(page_no, text)`) → `clean` (strip footers/TOC/noise, normalize) → `load` → `chunk` → `store`.
- `load.py` is the heart: a **stateful line-by-line parser** (`ParserState` + `flush`) hand-tuned to the FIBA rulebook grammar. Regexes (`RE_RULE`, `RE_ARTICLE`, `RE_SECTION`, `RE_DIAGRAM`) are **anchored** so inline cross-references never trigger a section break. It emits one `Document` per section (rule/article/section) with rich metadata (`rule_no`, `article_no`, `section_no`, `page_start`/`page_end`, `league`, `language`, …). Parsing starts at `RULE ONE` and stops at `APPENDIX`. Changing the FIBA PDF or its formatting will likely break this parser — `tests/ingest/test_load.py` pins exact section numbers, page spans, and content, and is the contract for it.
- **Contextual retrieval** (`context.py`): before embedding, each chunk's text is prefixed with its hierarchical header (`FIBA rules | Rule Two: The Court | Article 2 | §2.5.7`) so isolated chunks keep their meaning. `store.py` rebuilds `page_content` with this prefix at indexing time (`to_contextual_docs`).
- `source.py` derives `(corpus, language)` from the filename convention `<corpus>_..._<language>.pdf` (e.g. `fiba_rules_en.pdf` → `fiba`, `en`).
- Embeddings: `BAAI/bge-m3` (multilingual, for the FR/EN goal). Chroma persists to `storage/chroma/`.

**Retrieve** (`src/retrieve/`):
- `retriever.py` reconnects to the persisted Chroma collection and exposes a top-k similarity retriever.
- `classify.py` is a **scaffold only** — Pydantic structured-output classifier (intent + target leagues) intended to become the routing differentiator, but **not yet wired into the chain**.

**Generate** (`src/generate/`):
- `answer.py` assembles the LCEL chain: `retriever | format_docs` → `GROUNDED_PROMPT` → `get_llm()` → `StrOutputParser`.
- `prompt.py` forces the model to answer **strictly from retrieved context**, cite the exact rule, refuse when unknown, and reply in the question's language.
- `llm.py`: `ChatOllama` `llama3.1`, `temperature=0`.

**Config**: `config/settings.py` holds document-level constants (FIBA-specific: `DOC_TITLE`, `VALID_FROM`, `SOURCE`) injected as metadata at parse time.

## Conventions

- Code, comments, docstrings, and identifiers in **English** (chat may be in French).
- **Functions, not classes** — dataclasses for state (e.g. `ParserState`) are fine, but avoid wrapping logic in classes. "Factoriser"/refactor here means relocating a function that doesn't belong, not restructuring a function's internals.
- Default collection name is `fiba_rules`, default persist dir `storage/chroma` — kept consistent across `store.py` and `retriever.py`.
