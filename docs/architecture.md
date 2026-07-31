# SecondSelf — System Architecture

> **Purpose:** Define *how* we build SecondSelf — a personal AI second brain that captures, organizes, links, visualizes, and answers questions over your own knowledge.

---

## 1. Executive Summary

SecondSelf is a **local-first knowledge pipeline** with a **web-facing UI**. Raw captures land in `raw/`, get classified and linked into `wiki/`, export to a graph model, and power retrieval-augmented Q&A — all surfaced through a single Streamlit app deployed to a public URL.

| Principle | Decision |
|-----------|----------|
| Storage | File-system first (Markdown + JSON); no database in v1 |
| Intelligence | Free-tier LLM (Groq/Llama 3) + local embeddings (sentence-transformers) |
| UI | Streamlit (graph + search in one app) |
| Deployment | Streamlit Cloud or Hugging Face Spaces |
| Organization model | PARA (Projects, Areas, Resources, Archives) |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION LAYER                            │
│  ┌──────────────────────┐    ┌──────────────────────┐    ┌───────────────┐  │
│  │  CLI: capture.py     │    │  Streamlit app.py    │    │  Public URL   │  │
│  │  (Week 1)              │    │  (Week 4)            │    │  (deployed)   │  │
│  └──────────┬───────────┘    └──────────┬───────────┘    └───────────────┘  │
└─────────────┼────────────────────────────┼──────────────────────────────────┘
              │                            │
              ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROCESSING PIPELINE (Python)                        │
│                                                                             │
│  capture.py ──► classify.py ──► link.py ──► build_graph.py ──► ask.py        │
│     │               │              │              │              │          │
│     │          Groq LLM        embeddings     graph.json      RAG + LLM     │
│     │          (PARA/tags)   (sentence-                        synthesis    │
│     │                         transformers)                                   │
└─────┼───────────────┼──────────────┼──────────────┼──────────────┼───────────┘
      ▼               ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENCE LAYER                                 │
│  raw/          wiki/              embeddings/         graph.json            │
│  (captures)    (organized MD)     (vectors cache)    (nodes + edges)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow (End-to-End)

```
Capture (note | link | file)
    → raw/{timestamp}_{uuid}.{ext}
    → classify (PARA + tags + summary)
    → wiki/{para_category}/{slug}.md  (with YAML frontmatter)
    → embed + compare against wiki corpus
    → auto-insert [[wiki-links]] between related notes
    → build_graph.py reads wiki → graph.json
    → app.py renders graph + ask() answers questions
```

---

## 3. Component Architecture

### 3.1 Week 1 — Capture Pipeline (`capture.py`)

**Responsibility:** Accept any input type and persist immutably to `raw/`.

| Input Type | Handling |
|------------|----------|
| Plain text note | Save as `.md` or `.txt` with content body |
| URL / link | Fetch metadata (title, description) if possible; store URL + fetched text |
| File (PDF, image, etc.) | Copy binary to `raw/`; extract text sidecar if PDF |

**Capture record schema (filename convention):**

```
raw/{ISO8601_timestamp}_{short_uuid}.{ext}
Example: raw/20260723T143022_a3f9b2.md
```

**Sidecar metadata (optional JSON alongside file):**

```json
{
  "id": "a3f9b2c1-...",
  "captured_at": "2026-07-23T14:30:22Z",
  "source_type": "note | link | file",
  "original_filename": "research.pdf",
  "content_hash": "sha256:..."
}
```

**CLI interface:**

```bash
python capture.py note "Remember to review PARA method"
python capture.py link "https://example.com/article"
python capture.py file "./documents/paper.pdf"
```

**Design decisions:**
- Raw captures are **append-only** — never modified after write.
- Unique ID is UUID v4 (or ULID for sortable IDs).
- Timestamp is UTC ISO 8601 for consistency across deployments.

---

### 3.2 Week 2 — Classification (`classify.py`)

**Responsibility:** Transform raw captures into organized wiki notes using LLM.

**LLM provider:** Groq API with Llama 3 (free tier).

**Input:** One file from `raw/` (unprocessed).

**Output:** One Markdown file in `wiki/` with YAML frontmatter:

```yaml
---
id: a3f9b2c1-...
source_raw: raw/20260723T143022_a3f9b2.md
para_category: Resources        # Projects | Areas | Resources | Archives
tags: [productivity, para, note-taking]
summary: "Overview of the PARA organizational method for digital notes."
created_at: 2026-07-23T14:35:00Z
links: []                       # populated by link.py
embedding_id: emb_a3f9b2
---
# Note Title

Full content body...
```

**PARA routing (folder structure):**

```
wiki/
├── Projects/
├── Areas/
├── Resources/
└── Archives/
```

**Classification prompt contract:**

The LLM must return structured JSON:

```json
{
  "para_category": "Resources",
  "tags": ["tag1", "tag2"],
  "summary": "One-line summary.",
  "title": "Human-readable title",
  "body": "Cleaned/normalized markdown body"
}
```

**Batch mode:** `python classify.py --all` processes every unclassified item in `raw/`.

**State tracking:** Maintain `wiki/.index.json` mapping `raw_id → wiki_path` and processing status to avoid re-processing.

---

### 3.3 Week 2 — Auto-Linking (`link.py`)

**Responsibility:** Compute embeddings and insert bidirectional wiki links between semantically related notes.

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (local, free, ~80MB).

**Architecture:**

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  wiki/*.md  │────►│  Embedder        │────►│ embeddings/     │
│  (corpus)   │     │  (local ST model)│     │ {note_id}.npy   │
└─────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Similarity      │
                    │  Matrix / ANN    │
                    │  (cosine ≥ τ)    │
                    └────────┬─────────┘
                             ▼
                    Insert [[Note Title]] links
                    in both notes' frontmatter + body
```

**Similarity threshold:** Default `τ = 0.75` (tunable via config).

**Link insertion rules:**
1. Compare new note against all existing wiki notes.
2. For pairs above threshold, add `[[linked-note-slug]]` in a `## Related` section.
3. Update `links: []` array in frontmatter for graph builder consumption.
4. Avoid self-links and duplicate links.

**Incremental mode:** Only embed and compare the new note against the corpus (not full recompute every time).

---

### 3.4 Week 3 — Graph Builder (`build_graph.py`)

**Responsibility:** Parse all wiki notes and export a portable graph JSON for visualization.

**Graph JSON schema:**

```json
{
  "meta": {
    "generated_at": "2026-07-23T18:00:00Z",
    "node_count": 42,
    "edge_count": 87
  },
  "nodes": [
    {
      "id": "note-slug",
      "label": "Note Title",
      "para_category": "Resources",
      "tags": ["productivity"],
      "summary": "One-line summary",
      "content_preview": "First 200 chars...",
      "full_content": "Complete markdown body for hover popup",
      "wiki_path": "wiki/Resources/note-slug.md"
    }
  ],
  "edges": [
    {
      "source": "note-a-slug",
      "target": "note-b-slug",
      "type": "semantic_link",
      "weight": 0.82
    }
  ]
}
```

**Link sources (edges):**
1. Explicit `[[wiki-links]]` parsed from note bodies.
2. `links` array in frontmatter (from auto-linker).
3. Optional: tag co-occurrence edges (lower weight, v2).

**CLI:** `python build_graph.py` → writes `graph.json`.

---

### 3.5 Week 3/4 — Interactive Graph (inside `app.py`)

**Responsibility:** Render `graph.json` as a force-directed, explorable brain.

**Library choice:** `vis-network` (via `streamlit-components` or embedded HTML/JS) — simpler integration with Streamlit than Cytoscape for v1.

**Graph UI features:**

| Feature | Implementation |
|---------|----------------|
| Force-directed layout | vis-network physics engine |
| Node styling by PARA | Color map: Projects=blue, Areas=green, Resources=orange, Archives=gray |
| Hover popup | Show title, summary, tags, content preview |
| Click node | Side panel with full note content |
| Drag + zoom | Built-in vis-network interactions |
| "Alive" pulse | CSS animation on recently added nodes (optional) |

**Streamlit integration pattern:**

```python
# app.py renders graph via st.components.v1.html()
# Load graph.json, inject into vis-network template
```

---

### 3.6 Week 4 — Ask Your Brain (`ask.py`)

**Responsibility:** Retrieval-augmented generation (RAG) over the wiki corpus.

**RAG pipeline:**

```
User question (plain English)
    │
    ▼
┌─────────────────┐
│ Embed question  │  (same sentence-transformers model)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Top-K retrieval │  cosine similarity vs wiki embeddings (K=5 default)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Context assembly│  concatenate retrieved note bodies + metadata
└────────┬────────┘
         ▼
┌─────────────────┐
│ LLM synthesis   │  Groq/Llama 3 with grounded prompt
└────────┬────────┘
         ▼
Answer + source citations (which notes were used)
```

**`ask()` function signature:**

```python
def ask(
    question: str,
    top_k: int = 5,
    similarity_threshold: float = 0.5,
) -> AskResult:
    """
    Returns:
        answer: str           # synthesized response
        sources: list[Source] # note paths + relevance scores
        retrieved_chunks: list[str]
    """
```

**Prompt design (grounded synthesis):**

- System: "Answer ONLY from the provided notes. If insufficient, say so."
- Include retrieved note titles, summaries, and bodies as context.
- Require citation format: `[Source: note-title]`.

**Fallback behavior:** If no notes exceed similarity threshold, return "I don't have enough in your notes to answer that" rather than hallucinating.

---

### 3.7 Week 4 — Streamlit App (`app.py`)

**Responsibility:** Unified UI combining graph visualization and Q&A.

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  SecondSelf — Your Personal AI Second Brain                │
├──────────────────────────────┬─────────────────────────────┤
│                              │  🔍 Ask your brain          │
│   INTERACTIVE GRAPH          │  [________________] [Ask]   │
│   (vis-network canvas)       │                             │
│                              │  Answer:                    │
│                              │  ...                        │
│                              │  Sources: [note1] [note2]   │
├──────────────────────────────┴─────────────────────────────┤
│  Stats: 42 notes | 87 links | Last updated: 2 min ago    │
│  [Refresh Graph]  [Re-classify New]  [Capture Status]    │
└────────────────────────────────────────────────────────────┘
```

**App initialization:**
1. Load `graph.json` (rebuild if stale or missing).
2. Load embedding index for `ask()`.
3. Cache expensive operations with `@st.cache_data`.

**Environment variables (deployment):**
- `GROQ_API_KEY` — required for classify + ask
- `DATA_DIR` — optional override for raw/wiki paths

---

## 4. Data Models

### 4.1 Raw Capture

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `captured_at` | datetime (UTC) | Capture timestamp |
| `source_type` | enum | `note`, `link`, `file` |
| `content` | string / bytes | Raw payload |
| `metadata` | dict | URL, filename, mime type, etc. |

### 4.2 Wiki Note

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Links back to raw capture |
| `para_category` | enum | PARA bucket |
| `title` | string | Display title |
| `tags` | list[str] | LLM-assigned tags |
| `summary` | string | One-line summary |
| `body` | markdown | Full content |
| `links` | list[str] | Slugs of related notes |
| `embedding` | float[] | Stored in `embeddings/` cache |

### 4.3 Graph

| Entity | Fields |
|--------|--------|
| Node | id, label, para_category, tags, summary, content |
| Edge | source, target, type, weight |

### 4.4 Ask Result

| Field | Type |
|-------|------|
| `answer` | string |
| `sources` | list[{path, title, score}] |
| `confidence` | float (optional, from retrieval scores) |

---

## 5. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.11+ | Ecosystem for ML, LLM, Streamlit |
| Capture CLI | `argparse` / `click` | Simple one-command interface |
| LLM | Groq + Llama 3 | Free tier, fast inference |
| Embeddings | sentence-transformers | Local, no API cost, good quality |
| Vector storage | `.npy` files + in-memory index | No DB dependency for v1 |
| Wiki format | Markdown + YAML frontmatter | Human-readable, git-friendly |
| Graph viz | vis-network (JS) | Force-directed, hover, drag, zoom |
| UI | Streamlit | Rapid full-stack UI, easy deploy |
| Deploy | Streamlit Cloud / HF Spaces | Free public URL |
| Config | `.env` + `python-dotenv` | API keys outside repo |

### `requirements.txt` (expected)

```
streamlit>=1.32
groq>=0.4
sentence-transformers>=2.2
numpy>=1.24
pyyaml>=6.0
python-frontmatter>=1.0
python-dotenv>=1.0
requests>=2.31
pypdf>=4.0          # PDF text extraction
```

---

## 6. Module Boundaries & Dependencies

```
capture.py      →  (no upstream deps)
classify.py     →  groq, frontmatter, raw/
link.py         →  sentence-transformers, classify output, wiki/
build_graph.py  →  wiki/, frontmatter parser
ask.py          →  embeddings/, wiki/, groq
app.py          →  build_graph, ask, graph.json, streamlit
```

**Orchestration script (optional, Week 4):**

```bash
python pipeline.py   # classify → link → build_graph (for new captures)
```

Each module is independently runnable for development and testing.

---

## 7. Configuration

**`config.py` or `.env`:**

```env
GROQ_API_KEY=gsk_...
EMBEDDING_MODEL=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.75
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.5
RAW_DIR=raw
WIKI_DIR=wiki
EMBEDDINGS_DIR=embeddings
GRAPH_PATH=graph.json
```

**`.gitignore` must exclude:**
- `.env`
- `embeddings/` (regenerable)
- `__pycache__/`
- Optional: `raw/` and `wiki/` if they contain personal data (document in README)

---

## 8. Deployment Architecture

```
┌──────────────────┐         ┌─────────────────────────┐
│  GitHub Repo     │────────►│  Streamlit Cloud        │
│  (public)        │  push   │  or HF Spaces           │
└──────────────────┘         └───────────┬─────────────┘
                                         │
                                         ▼
                             ┌─────────────────────────┐
                             │  Public URL             │
                             │  https://xxx.streamlit  │
                             │  .app                   │
                             └─────────────────────────┘
```

**Deployment considerations:**

| Concern | Approach |
|---------|----------|
| API keys | Set `GROQ_API_KEY` in Streamlit Cloud secrets |
| Personal data | Ship demo/sample wiki OR use env flag for read-only demo mode |
| Graph refresh | Rebuild `graph.json` on app startup or via "Refresh" button |
| Cold start | Cache embeddings; pre-build graph.json in repo for demo |
| Resource limits | MiniLM model ~80MB; acceptable on free tier |

**Demo vs. personal mode:**
- **Personal:** User runs capture/classify locally; deploys pre-built wiki + graph.
- **Demo:** Include `sample_wiki/` in repo for public deployment without private notes.

---

## 9. Security & Privacy

| Risk | Mitigation |
|------|------------|
| API key leakage | Never commit `.env`; use platform secrets |
| Personal notes in public repo | `.gitignore` personal dirs; document clearly |
| LLM sends note content to Groq | Disclose in README; optional local LLM in v2 |
| Arbitrary file capture | Validate file types; size limits (e.g., 10MB) |
| URL fetch SSRF | Allowlist schemes (https only); timeout on fetch |

---

## 10. Observability & Logging

- Structured logging via Python `logging` module.
- Each pipeline stage logs: input path, output path, duration, errors.
- `wiki/.index.json` serves as processing audit trail.
- Streamlit sidebar shows last pipeline run timestamp and note counts.

---

## 11. Repository Structure (Final)

```
secondself/
├── raw/                    # Week 1: immutable captures
├── wiki/                   # Week 2: organized notes
│   ├── Projects/
│   ├── Areas/
│   ├── Resources/
│   ├── Archives/
│   └── .index.json         # processing state
├── embeddings/             # cached vectors (gitignored)
├── capture.py              # Week 1
├── classify.py             # Week 2.1
├── link.py                 # Week 2.2
├── build_graph.py          # Week 3.1
├── graph.json              # Week 3 output
├── ask.py                  # Week 4.1
├── app.py                  # Week 4.2 — Streamlit UI
├── config.py               # shared configuration
├── pipeline.py             # optional orchestrator
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── architecture.md         # this document
├── PROBLEM_STATEMENT.md
└── static/
    └── graph_template.html # vis-network embed template
```

---

## 12. Weekly Milestone → Architecture Mapping

| Week | Badge | Components Built | Persistent Artifacts |
|------|-------|------------------|----------------------|
| 1 | The Archivist | `capture.py`, `raw/` | Timestamped raw files |
| 2 | The Librarian | `classify.py`, `link.py`, `wiki/` | PARA notes + links + embeddings |
| 3 | The Cartographer | `build_graph.py`, graph UI | `graph.json`, interactive viz |
| 4 | The Oracle | `ask.py`, `app.py`, deploy | Public URL, full RAG |

---

## 13. Extension Points (Post-v1)

These are **out of scope** for the 4-week build but architected for easy addition:

- **Database:** Replace file index with SQLite for faster similarity search.
- **Local LLM:** Swap Groq for Ollama (privacy, offline).
- **Incremental graph updates:** WebSocket push when new notes added.
- **Multi-user:** Auth layer + per-user wiki namespaces.
- **Browser extension:** Capture directly from browser to `capture.py` API.
- **Obsidian sync:** Export wiki as Obsidian-compatible vault.

---

## 14. Architecture Decision Records (ADRs)

### ADR-001: File-system over database
**Decision:** Use Markdown files + JSON indexes.  
**Reason:** Simplicity, git-friendly, no infra cost, matches "personal brain" mental model.  
**Trade-off:** Slower at scale (>10k notes); acceptable for v1.

### ADR-002: Groq for LLM, local for embeddings
**Decision:** Cloud LLM for classification/synthesis; local embeddings for linking/RAG retrieval.  
**Reason:** LLM quality matters for classification; embeddings are cheap locally.  
**Trade-off:** Requires API key and network for classify/ask.

### ADR-003: Streamlit over custom frontend
**Decision:** Single Streamlit app for graph + search.  
**Reason:** Fastest path to public URL; one codebase.  
**Trade-off:** Graph interactivity limited vs. dedicated React app.

### ADR-004: PARA as sole taxonomy
**Decision:** LLM assigns exactly one PARA category per note.  
**Reason:** Matches problem statement; prevents over-tagging paralysis.  
**Trade-off:** Some notes fit multiple categories; tags provide secondary organization.

---

## 15. Success Criteria (Architecture-Level)

The architecture is successful when:

1. **Capture → raw** is append-only and idempotent (same content, new ID).
2. **Classify → wiki** produces consistent frontmatter parseable by downstream modules.
3. **Link** produces bidirectional, threshold-gated edges without manual intervention.
4. **Graph** is regeneratable entirely from `wiki/` (JSON is a derived view).
5. **Ask** returns grounded answers with traceable sources.
6. **Deploy** serves graph + ask from one URL with secrets managed safely.

---

*Next step: See `implementation-plan.md` for phase-wise build order and acceptance checkpoints.*
