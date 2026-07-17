# CourtIQ

Bilingual (FR/EN) RAG assistant for basketball **rules and tactics**.

CourtIQ ingests basketball reference documents (rulebooks, tactics), turns them
into context-enriched, embedded chunks, and stores them in a vector database for
retrieval-augmented question answering.

> **Status:** the FIBA and NBA rulebooks are fully wired — ingestion → indexing →
> league-filtered retrieval → classification-routed grounded answering (single-league
> lookups and cross-league comparison). Additional corpora (EuroLeague, TheBAL), a
> tactics corpus, and an answer-quality evaluation harness are on the roadmap.

## How it works

### Ingestion — PDF → vectors

The ingestion pipeline turns a PDF into searchable, context-aware vectors:

```text
PDF ─▶ extract ─▶ clean / normalize ─▶ structural parse ─▶ chunk ─▶ contextual text ─▶ embed ─▶ Chroma
     pymupdf      strip noise/footers   one Document per     token-     prepend rule/      bge-m3
                                        section (rule/        based      article/section
                                        article/section)      512/50     header
```

- **Structural parsing** ([src/ingest/load/](src/ingest/load/)) — a dialect-driven
  engine ([engine.py](src/ingest/load/engine.py)) parses a rulebook into one
  `Document` per section, each carrying rich metadata (`rule_no`, `article_no`,
  `section_no`, `page_start`/`page_end`, `league`, `language`, …). Each league has
  its own grammar under [dialects/](src/ingest/load/dialects/): FIBA
  (Rule → Article → Section) and NBA (Rule → Section, roman-numeral sections).
  Adding a league means adding a dialect, not touching the engine.
- **Contextual retrieval** ([src/ingest/context.py](src/ingest/context.py)) — each
  chunk is prefixed with its hierarchical header
  (`FIBA rules | Rule Two: The Court | Article 2 | §2.5.7`) before embedding, so
  isolated chunks keep their meaning.
- **Embeddings** ([src/ingest/embed.py](src/ingest/embed.py)) — `BAAI/bge-m3`, a
  multilingual model that suits the FR/EN bilingual goal.
- **Vector store** ([src/ingest/store.py](src/ingest/store.py)) — Chroma, persisted
  to disk. Every corpus lives in a single collection, tagged by `league` metadata.

### Query — question → routed, grounded answer

The query pipeline classifies the question, routes it, and asks an LLM to answer
**strictly from the retrieved context**:

```text
question ─▶ classify ─▶ route ─┬─ grounded:    league-filtered retrieve ─▶ grounded prompt ─▶ LLM
          intent + leagues     ├─ comparison:  per-league retrieve ─▶ compare prompt ─▶ LLM
                               └─ out_of_scope / unsupported league ─▶ direct message
```

- **Query classification** ([src/retrieve/classify.py](src/retrieve/classify.py)) —
  structured-output classifier (intent + target leagues). This is the project's
  routing differentiator. `leagues` is free-form, so a league that is mentioned but
  not indexed (e.g. `euroleague`) is surfaced rather than silently coerced.
- **Router** ([src/generate/answer.py](src/generate/answer.py)) — classifies once,
  then routes: grounded answer for a single/unspecified league, cross-league
  comparison, or a direct message for out-of-scope questions and explicitly named
  unsupported leagues. Routing decides on the concrete league data, never on the
  noisy intent label alone.
- **Retriever** ([src/retrieve/retriever.py](src/retrieve/retriever.py)) — connects
  to the persisted Chroma index and exposes a top-k similarity retriever, optionally
  filtered by `league` metadata.
- **Prompts** ([src/generate/prompt.py](src/generate/prompt.py)) — the grounded
  prompt forces the model to cite the exact rule, reply in the question's language,
  and refuse when the answer is not in the retrieved context; the compare prompt
  contrasts leagues from separately-labelled context blocks.
- **LLM** ([src/generate/llm.py](src/generate/llm.py)) — `llama3.1` served locally
  via Ollama (`temperature=0` for deterministic answers).

## Structure

```text
court-iq/
├── apps/
│   └── cli/
│       ├── main.py              # Typer app entry point
│       └── commands/
│           ├── index.py         # `index` command: PDF -> vector store
│           └── ask.py           # `ask` command: interactive routed Q&A (rich TUI)
├── config/
│   └── settings.py              # document-level metadata constants (FIBA, NBA)
├── src/
│   ├── ingest/
│   │   ├── extract.py           # PDF -> (page_no, text)
│   │   ├── clean.py             # noise stripping + text normalization
│   │   ├── load/                # structural parsing -> Documents
│   │   │   ├── engine.py        # dialect-driven parser engine + shared state
│   │   │   └── dialects/        # per-league grammars (fiba.py, nba.py)
│   │   ├── source.py            # derive (corpus, language) from the filename
│   │   ├── chunk.py             # token-based splitting
│   │   ├── context.py           # hierarchical context prefixing
│   │   ├── embed.py             # HuggingFace embeddings (bge-m3)
│   │   └── store.py             # Chroma vector store
│   ├── retrieve/
│   │   ├── retriever.py         # Chroma-backed top-k retriever (league filter)
│   │   └── classify.py          # query intent + league classification
│   └── generate/
│       ├── prompt.py            # grounded + compare prompts, context formatting
│       ├── llm.py               # Ollama chat model (llama3.1)
│       └── answer.py            # classification-routed answer pipeline
├── tests/
│   └── ingest/
│       └── test_load.py         # FIBA parser contract tests
├── data/                        # source PDFs (input)
├── storage/chroma/              # persisted vector store (generated)
└── pyproject.toml
```

## Requirements

- Python ≥ 3.13
- [uv](https://docs.astral.sh/uv/) for dependency management
- [Ollama](https://ollama.com/) running locally with the `llama3.1` model pulled
  (`ollama pull llama3.1`) — used by classification and answering.
- Apple Silicon for the default embedding device (`mps`) — change `device` in
  [src/ingest/embed.py](src/ingest/embed.py) for CPU/CUDA.

## Installation

```bash
uv sync
```

This installs the runtime dependencies, the dev tools (pytest), and the project
itself — which exposes the `court-iq` command.

## Usage

### Index rulebook PDFs into the vector store

```bash
uv run court-iq index --pdf-path data/fiba_rules_en.pdf
uv run court-iq index --pdf-path data/nba_rules_en.pdf
```

Each PDF is parsed with its league's dialect (selected from the filename) and
indexed into the shared collection, tagged by `league` metadata.

Options:

| Flag                        | Default          | Description                     |
| --------------------------- | ---------------- | ------------------------------- |
| `--pdf-path` / `-pp`        | _(required)_     | Path to the PDF to index        |
| `--vector-store` / `-vs`    | `storage/chroma` | Directory where Chroma persists |
| `--collection-name` / `-cn` | `rules`          | Chroma collection name          |

**Source filename convention:** corpus and language are derived from the file
name as `<corpus>_..._<language>.pdf` (e.g. `fiba_rules_en.pdf` →
corpus `fiba`, language `en`).

### Ask questions

Make sure Ollama is running (`ollama serve`), then:

```bash
uv run court-iq ask
```

The question is classified and routed automatically: a FIBA or NBA rule lookup is
answered from that league, a cross-league question ("FIBA vs NBA…") triggers a
comparison, and an unsupported league or off-topic question gets a direct message.
Answers cite the exact rule and reply in the question's language.

> **Tip:** set `HF_HUB_OFFLINE=1` to skip the Hugging Face Hub round-trip (and its
> auth warning) since the embedding model is already cached locally.

## Tests

```bash
uv run pytest
```

Currently covers the FIBA structural parser (the contract that pins section
numbers, page spans, and content). NBA parsing, the league filter, and routing are
verified manually — extending test coverage to them is on the roadmap.

## License

[MIT](LICENSE) © 2026 Joseph
