# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CourtIQ is a bilingual (FR/EN) RAG assistant for basketball **rules and tactics**. PDF rulebooks are ingested into context-enriched, embedded chunks stored in Chroma, then queried via a classification-routed, grounded LLM pipeline. The FIBA and NBA rulebooks are fully wired end-to-end: ingestion → league-filtered retrieval → routed answering (single-league lookups and cross-league comparison). Query classification is the routing differentiator and is connected. EuroLeague, TheBAL, and a tactics corpus are not yet built.

## Commands

```bash
uv sync                                              # install deps + the court-iq CLI
uv run court-iq index --pdf-path data/fiba_rules_en.pdf   # PDF -> Chroma (dialect auto-selected)
uv run court-iq index --pdf-path data/nba_rules_en.pdf    # same collection, tagged by league
uv run court-iq ask                                  # interactive routed Q&A
uv run pytest                                         # all tests
uv run pytest tests/ingest/test_load.py::test_section_metadata   # single test
```

- The query path needs **Ollama running locally** (`ollama serve`) with `llama3.1` pulled.
- Set `HF_HUB_OFFLINE=1` to skip the Hugging Face Hub round-trip (the bge-m3 model is cached locally).
- Embeddings default to Apple Silicon (`device="mps"` in `src/ingest/embed.py`); change it for CPU/CUDA.

## Architecture

Three stages under `src/`, orchestrated by a Typer CLI in `apps/cli/`. The **`langchain_core.documents.Document` is the pivot type** throughout — there is no intermediate JSONL/serialization format.

**Ingest** (`src/ingest/`) — PDF → vectors, one stage per file:
`extract` (pymupdf → `(page_no, text)`) → `clean` (strip footers/TOC/noise, normalize) → `load/` → `chunk` → `store`.
- `load/` is the heart: a **dialect-driven, stateful line-by-line parser**. `engine.py` holds the league-agnostic engine (`ParserState`, `Dialect`, `_Engine`, `_emit`, `run`); each league's grammar lives in `dialects/` (`fiba.py`, `nba.py`) as **anchored** regexes + small handler functions + a `Dialect` instance; `load/__init__.py` exposes `load_pdf(pdf_path)`, which picks the dialect from the filename. Anchoring means inline cross-references never trigger a section break (e.g. NBA stops only on the standalone `COMMENTS ON THE RULES` header, not inline mentions). FIBA parses Rule → Article → Section (`RULE ONE` … `APPENDIX`); NBA parses Rule → Section with roman-numeral sections. It emits one `Document` per section with rich metadata (`rule_no`, `article_no`, `section_no`, `section_title`, `page_start`/`page_end`, `league`, `language`, …). Adding a league = adding a `Dialect`, never touching the engine. `tests/ingest/test_load.py` pins exact FIBA section numbers, page spans, and content — the contract for the **FIBA** dialect; **NBA has no test yet**. Changing a league's PDF or its formatting will likely break that dialect.
- **Contextual retrieval** (`context.py`): before embedding, each chunk's text is prefixed with its hierarchical header (`FIBA rules | Rule Two: The Court | Article 2 | §2.5.7`) so isolated chunks keep their meaning. `store.py` rebuilds `page_content` with this prefix at indexing time (`to_contextual_docs`).
- `source.py` derives `(corpus, language)` from the filename convention `<corpus>_..._<language>.pdf` (e.g. `fiba_rules_en.pdf` → `fiba`, `en`).
- Embeddings: `BAAI/bge-m3` (multilingual, for the FR/EN goal). Chroma persists to `storage/chroma/`.

**Retrieve** (`src/retrieve/`):
- `retriever.py` reconnects to the persisted Chroma collection and exposes a top-k similarity retriever, optionally filtered by `league` metadata (`{"league": {"$in": [...]}}`).
- `classify.py` is the **routing differentiator, now wired** — a Pydantic structured-output classifier returning `intent` + `leagues`. `leagues` is free-form (`list[str]`, normalized to lowercase) so a mentioned-but-unindexed league is **surfaced**, not coerced into a supported one.

**Generate** (`src/generate/`):
- `answer.py` is the **router**: `answer(question)` classifies once, then routes — `out_of_scope` → message; an explicitly named unsupported league → message; `comparison` with ≥2 supported leagues → `answer_comparison` (per-league retrieval labelled `=== LEAGUE ===`, `COMPARE_PROMPT`); otherwise → `answer_grounded` (league-filtered retrieval → `GROUNDED_PROMPT`). **Route on the concrete league data, never on the noisy intent label alone.** `AVAILABLE_LEAGUES` gates support. Cost: 2 LLM calls per question (classify + answer).
- `prompt.py`: `GROUNDED_PROMPT` (answer strictly from context, cite the exact rule, refuse when unknown, reply in the question's language), `COMPARE_PROMPT`, and `format_docs`.
- `llm.py`: `ChatOllama` `llama3.1`, `temperature=0`.

**Config**: `config/settings.py` holds per-corpus document-level constants (`DOC_TITLE_FIBA`/`_NBA`, `VALID_FROM_*`, `SOURCE_*`) injected as metadata at parse time.

## Conventions

- Code, comments, docstrings, and identifiers in **English** (chat may be in French).
- **Functions, not classes** — dataclasses for state (e.g. `ParserState`) are fine, but avoid wrapping logic in classes. "Factoriser"/refactor here means relocating a function that doesn't belong, not restructuring a function's internals.
- Default collection name is `rules` (shared by every corpus, isolated at query time by the `league` metadata filter), default persist dir `storage/chroma` — kept consistent across `store.py` and `retriever.py`.
