# CourtIQ

Bilingual (FR/EN) RAG assistant for basketball **rules and tactics**.

CourtIQ ingests basketball reference documents (rulebooks, tactics), turns them
into context-enriched, embedded chunks, and stores them in a vector database for
retrieval-augmented question answering.

> **Status:** ingestion → indexing is implemented for the FIBA rulebook.
> Retrieval, query classification, and additional corpora (NBA, EuroLeague,
> TheBAL) are on the roadmap.

## How it works

The ingestion pipeline turns a PDF into searchable, context-aware vectors:

```text
PDF ─▶ extract ─▶ clean / normalize ─▶ structural parse ─▶ chunk ─▶ contextual text ─▶ embed ─▶ Chroma
     pymupdf      strip noise/footers   one Document per     token-     prepend rule/      bge-m3
                                        section (rule/        based      article/section
                                        article/section)      512/50     header
```

- **Structural parsing** ([src/ingest/load.py](src/ingest/load.py)) — the rulebook
  is parsed into one `Document` per section, each carrying rich metadata
  (`rule_no`, `article_no`, `section_no`, `page_start`/`page_end`, `league`,
  `language`, …).
- **Contextual retrieval** ([src/ingest/context.py](src/ingest/context.py)) — each
  chunk is prefixed with its hierarchical header
  (`FIBA rules | Rule Two: The Court | Article 2 | §2.5.7`) before embedding, so
  isolated chunks keep their meaning.
- **Embeddings** ([src/embed.py](src/embed.py)) — `BAAI/bge-m3`, a multilingual
  model that suits the FR/EN bilingual goal.
- **Vector store** ([src/store.py](src/store.py)) — Chroma, persisted to disk.

## Structure

```text
court-iq/
├── apps/
│   └── cli/
│       ├── main.py              # Typer app entry point
│       └── commands/
│           └── index.py         # `index` command: PDF -> vector store
├── config/
│   └── settings.py              # document-level metadata constants (FIBA)
├── src/
│   ├── embed.py                 # HuggingFace embeddings (bge-m3)
│   ├── store.py                 # Chroma vector store
│   └── ingest/
│       ├── extract.py           # PDF -> (page_no, text)
│       ├── clean.py             # noise stripping + text normalization
│       ├── load.py              # structural parser -> Documents (FIBA grammar)
│       ├── source.py            # derive (corpus, language) from the filename
│       ├── chunk.py             # token-based splitting
│       └── context.py           # hierarchical context prefixing
├── tests/
│   └── ingest/
│       └── test_load.py         # parser tests
├── data/                        # source PDFs (input)
├── storage/chroma/              # persisted vector store (generated)
└── pyproject.toml
```

## Requirements

- Python ≥ 3.13
- [uv](https://docs.astral.sh/uv/) for dependency management
- Apple Silicon for the default embedding device (`mps`) — change `device` in
  [src/embed.py](src/embed.py) for CPU/CUDA.

## Installation

```bash
uv sync
```

This installs the runtime dependencies, the dev tools (pytest), and the project
itself — which exposes the `court-iq` command.

## Usage

Index a rulebook PDF into the vector store:

```bash
uv run court-iq --pdf-path data/fiba_rules_en.pdf
```

`court-iq` is a console entry point declared in `pyproject.toml`
(`[project.scripts]`), installed by `uv sync`.

Options:

| Flag                        | Default          | Description                     |
| --------------------------- | ---------------- | ------------------------------- |
| `--pdf-path` / `-pp`        | _(required)_     | Path to the PDF to index        |
| `--vector-store` / `-vs`    | `storage/chroma` | Directory where Chroma persists |
| `--collection-name` / `-cn` | `fiba_rules`     | Chroma collection name          |

**Source filename convention:** corpus and language are derived from the file
name as `<corpus>_..._<language>.pdf` (e.g. `fiba_rules_en.pdf` →
corpus `fiba`, language `en`).

## Tests

```bash
uv run pytest
```

## Roadmap

- [x] FIBA rulebook ingestion → indexing
- [ ] Retrieval + question answering (`query` command)
- [ ] Query classification (the project's differentiator)
- [ ] Additional corpora: NBA, EuroLeague, TheBAL
- [ ] Tactics corpus

## License

[MIT](LICENSE) © 2026 Joseph
