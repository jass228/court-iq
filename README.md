# CourtIQ

Bilingual (FR/EN) RAG assistant for basketball **rules and tactics**.

CourtIQ ingests basketball reference documents (rulebooks, tactics), turns them
into context-enriched, embedded chunks, and stores them in a vector database for
retrieval-augmented question answering.

> **Status:** ingestion → indexing and end-to-end retrieval → grounded answering
> are implemented for the FIBA rulebook. Query classification, multi-corpus
> routing, and additional corpora (NBA, EuroLeague, TheBAL) are on the roadmap.

## How it works

### Ingestion — PDF → vectors

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
- **Embeddings** ([src/ingest/embed.py](src/ingest/embed.py)) — `BAAI/bge-m3`, a
  multilingual model that suits the FR/EN bilingual goal.
- **Vector store** ([src/ingest/store.py](src/ingest/store.py)) — Chroma, persisted
  to disk.

### Query — question → grounded answer

The query pipeline retrieves the most relevant chunks and asks an LLM to answer
**strictly from that context**:

```text
question ─▶ retrieve (top-k) ─▶ format context ─▶ grounded prompt ─▶ LLM ─▶ answer
              bge-m3 similarity    join chunks       cite-or-refuse    llama3.1 (Ollama)
```

- **Retriever** ([src/retrieve/retriever.py](src/retrieve/retriever.py)) — connects
  to the persisted Chroma index and exposes a top-k similarity retriever.
- **Grounded prompt** ([src/generate/prompt.py](src/generate/prompt.py)) — forces
  the model to cite the exact rule, reply in the question's language, and refuse
  when the answer is not in the retrieved context.
- **LLM** ([src/generate/llm.py](src/generate/llm.py)) — `llama3.1` served locally
  via Ollama (`temperature=0` for deterministic answers).
- **Chain** ([src/generate/answer.py](src/generate/answer.py)) — wires retriever →
  prompt → LLM into a single LCEL runnable.
- **Query classification** ([src/retrieve/classify.py](src/retrieve/classify.py)) —
  structured-output scaffold (intent + target leagues) for future routing; not yet
  wired into the chain.

## Structure

```text
court-iq/
├── apps/
│   └── cli/
│       ├── main.py              # Typer app entry point
│       └── commands/
│           ├── index.py         # `index` command: PDF -> vector store
│           └── try_fiba.py      # `fiba` command: interactive Q&A
├── config/
│   └── settings.py              # document-level metadata constants (FIBA)
├── src/
│   ├── ingest/
│   │   ├── extract.py           # PDF -> (page_no, text)
│   │   ├── clean.py             # noise stripping + text normalization
│   │   ├── load.py              # structural parser -> Documents (FIBA grammar)
│   │   ├── source.py            # derive (corpus, language) from the filename
│   │   ├── chunk.py             # token-based splitting
│   │   ├── context.py           # hierarchical context prefixing
│   │   ├── embed.py             # HuggingFace embeddings (bge-m3)
│   │   └── store.py             # Chroma vector store
│   ├── retrieve/
│   │   ├── retriever.py         # Chroma-backed top-k retriever
│   │   └── classify.py          # query intent classification (scaffold)
│   └── generate/
│       ├── prompt.py            # grounded RAG prompt + context formatting
│       ├── llm.py               # Ollama chat model (llama3.1)
│       └── answer.py            # retriever -> prompt -> LLM chain
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
- [Ollama](https://ollama.com/) running locally with the `llama3.1` model pulled
  (`ollama pull llama3.1`) — used by the query pipeline.
- Apple Silicon for the default embedding device (`mps`) — change `device` in
  [src/ingest/embed.py](src/ingest/embed.py) for CPU/CUDA.

## Installation

```bash
uv sync
```

This installs the runtime dependencies, the dev tools (pytest), and the project
itself — which exposes the `court-iq` command.

## Usage

### Index a rulebook PDF into the vector store

```bash
uv run court-iq index --pdf-path data/fiba_rules_en.pdf
```

Options:

| Flag                        | Default          | Description                     |
| --------------------------- | ---------------- | ------------------------------- |
| `--pdf-path` / `-pp`        | _(required)_     | Path to the PDF to index        |
| `--vector-store` / `-vs`    | `storage/chroma` | Directory where Chroma persists |
| `--collection-name` / `-cn` | `fiba_rules`     | Chroma collection name          |

**Source filename convention:** corpus and language are derived from the file
name as `<corpus>_..._<language>.pdf` (e.g. `fiba_rules_en.pdf` →
corpus `fiba`, language `en`).

### Ask questions against the FIBA index

Make sure Ollama is running (`ollama serve`), then:

```bash
uv run court-iq fiba
```

> **Tip:** set `HF_HUB_OFFLINE=1` to skip the Hugging Face Hub round-trip (and its
> auth warning) since the embedding model is already cached locally.

## Tests

```bash
uv run pytest
```

## Roadmap

- [x] FIBA rulebook ingestion → indexing
- [x] Retrieval + question answering (`fiba` command)
- [ ] Query classification (the project's differentiator)
- [ ] Additional corpora: NBA, EuroLeague, TheBAL
- [ ] Tactics corpus

## License

[MIT](LICENSE) © 2026 Joseph
