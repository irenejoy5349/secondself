# SecondSelf — Phase-Wise Implementation Plan

> **Sources:** [`architecture.md`](architecture.md) · [`PROBLEM_STATEMENT.md`](PROBLEM_STATEMENT.md)  
> **Goal:** Build, test, and deploy SecondSelf — capture → classify → link → graph → ask — in discrete, verifiable phases.

---

## Overview

| Phase | Name | Maps To | Badge |
|-------|------|---------|-------|
| **0** | Project Setup | Foundation | — |
| **1** | Capture Pipeline | Week 1 | 🏅 The Archivist |
| **2** | Auto-Classification | Week 2.1 | — |
| **3** | Auto-Linking | Week 2.2 | 🏅 The Librarian |
| **4** | Graph Builder & Viz | Week 3 | 🏅 The Cartographer |
| **5** | RAG + Streamlit UI | Week 4.1–4.2 | — |
| **6** | Local Pipeline Testing | Integration | — |
| **7** | Local UI Testing | Integration | — |
| **8** | Deployment | Week 4.2 | — |
| **9** | Final Verification & Ship | Final deliverables | 🏅 The Oracle |

**Dependency chain:**

```
Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
```

Each phase has **tasks**, **acceptance criteria**, and **verification steps**. Do not skip ahead — each phase's output is the next phase's input.

---

## Phase 0 — Project Setup

**Objective:** Scaffold the repository, dependencies, and shared configuration so all later phases have a consistent foundation.

### Tasks

- [ ] **0.1** Initialize Python project (Python 3.11+ recommended)
- [ ] **0.2** Create folder structure:
  ```
  secondself/
  ├── raw/
  ├── wiki/
  │   ├── Projects/
  │   ├── Areas/
  │   ├── Resources/
  │   └── Archives/
  ├── embeddings/
  └── static/
  ```
- [ ] **0.3** Create `requirements.txt` with pinned minimum versions:
  ```
  streamlit>=1.32
  groq>=0.4
  sentence-transformers>=2.2
  numpy>=1.24
  pyyaml>=6.0
  python-frontmatter>=1.0
  python-dotenv>=1.0
  requests>=2.31
  pypdf>=4.0
  ```
- [ ] **0.4** Create `config.py` — centralize paths and tunables:
  - `RAW_DIR`, `WIKI_DIR`, `EMBEDDINGS_DIR`, `GRAPH_PATH`
  - `GROQ_API_KEY`, `EMBEDDING_MODEL`
  - `SIMILARITY_THRESHOLD` (0.75), `RAG_TOP_K` (5), `RAG_SIMILARITY_THRESHOLD` (0.5)
- [ ] **0.5** Create `.env.example` (no secrets) and `.gitignore`:
  - Ignore: `.env`, `embeddings/`, `__pycache__/`, `.venv/`, `*.pyc`
  - Document whether `raw/` and `wiki/` are ignored (personal data)
- [ ] **0.6** Create placeholder files: `capture.py`, `classify.py`, `link.py`, `build_graph.py`, `ask.py`, `app.py`, `pipeline.py`
- [ ] **0.7** Add `.gitkeep` in empty dirs (`raw/`, `wiki/*`, `embeddings/`, `static/`)
- [ ] **0.8** Create virtual environment and install dependencies:
  ```bash
  python -m venv .venv
  .venv\Scripts\activate        # Windows
  pip install -r requirements.txt
  ```
- [ ] **0.9** Obtain Groq API key from [console.groq.com](https://console.groq.com) and add to `.env`

### Acceptance Criteria

- [ ] All directories exist per architecture spec
- [ ] `pip install -r requirements.txt` succeeds without errors
- [ ] `config.py` loads env vars via `python-dotenv`
- [ ] `.env` is gitignored; `.env.example` is committed
- [ ] `python -c "import config"` runs without error

### Verification

```bash
python -c "from config import RAW_DIR, WIKI_DIR; print(RAW_DIR, WIKI_DIR)"
dir raw wiki
```

**Deliverable:** Empty but correctly structured repo ready for Phase 1.

---

## Phase 1 — Capture Pipeline (`capture.py`)

**Objective:** One command captures any note, link, or file into `raw/` with timestamp + unique ID.  
**Badge:** 🏅 The Archivist  
**Week:** 1

### Tasks

- [ ] **1.1** Implement CLI with subcommands: `note`, `link`, `file`
  ```bash
  python capture.py note "Your text here"
  python capture.py link "https://example.com/article"
  python capture.py file "./path/to/document.pdf"
  ```
- [ ] **1.2** Generate capture metadata on every save:
  - UUID v4 (full ID in sidecar JSON)
  - UTC ISO 8601 timestamp
  - Filename: `raw/{timestamp}_{short_uuid}.{ext}`
- [ ] **1.3** **Note capture:** Write content to `.md` file with optional title header
- [ ] **1.4** **Link capture:**
  - Store URL in file body
  - Fetch page title/description via HTTP (timeout 10s, https only)
  - Save fetched text alongside URL
- [ ] **1.5** **File capture:**
  - Copy binary to `raw/` with original extension
  - Extract text sidecar for PDFs using `pypdf`
  - Enforce max file size (10 MB)
- [ ] **1.6** Write sidecar JSON `{filename}.meta.json` with:
  ```json
  {
    "id": "uuid",
    "captured_at": "ISO8601",
    "source_type": "note|link|file",
    "original_filename": "...",
    "content_hash": "sha256:..."
  }
  ```
- [ ] **1.7** Print confirmation: saved path + ID
- [ ] **1.8** Capture **10+ real items** from your own scattered notes/links/files (not synthetic test data)

### Acceptance Criteria

- [ ] `raw/` and `wiki/` folder structure exists
- [ ] One command captures a note, a link, AND a file
- [ ] Every capture has a timestamp + unique ID
- [ ] 10+ real items in `raw/`
- [ ] Raw files are append-only (never overwritten)

### Verification

```bash
python capture.py note "Meeting notes from Tuesday standup"
python capture.py link "https://fortelabs.com/blog/para/"
python capture.py file "C:\Users\you\Documents\article.pdf"
dir raw
# Confirm: 10+ files, each with .meta.json sidecar
```

**Deliverable:** Working `capture.py` + populated `raw/` folder.

---

## Phase 2 — Auto-Classification (`classify.py`)

**Objective:** Send raw captures to Groq/Llama 3; output PARA-categorized wiki notes with tags and summary.  
**Week:** 2.1

### Tasks

- [ ] **2.1** Implement Groq client wrapper with error handling and rate-limit retries
- [ ] **2.2** Design classification prompt that returns **strict JSON**:
  ```json
  {
    "para_category": "Projects|Areas|Resources|Archives",
    "tags": ["tag1", "tag2"],
    "summary": "One-line summary.",
    "title": "Human-readable title",
    "body": "Cleaned markdown body"
  }
  ```
- [ ] **2.3** Implement `classify_raw(raw_path) -> wiki_path` function
- [ ] **2.4** Write wiki note with YAML frontmatter:
  ```yaml
  ---
  id: ...
  source_raw: raw/...
  para_category: Resources
  tags: [...]
  summary: "..."
  created_at: ...
  links: []
  ---
  ```
- [ ] **2.5** Route output to `wiki/{para_category}/{slug}.md`
- [ ] **2.6** Create and maintain `wiki/.index.json`:
  ```json
  {
    "raw/20260723T143022_a3f9b2.md": {
      "wiki_path": "wiki/Resources/para-method.md",
      "status": "classified",
      "classified_at": "..."
    }
  }
  ```
- [ ] **2.7** Implement batch mode: `python classify.py --all` (skip already-indexed)
- [ ] **2.8** Implement single-file mode: `python classify.py raw/some_file.md`
- [ ] **2.9** Run classifier on all Phase 1 captures (10+ items)

### Acceptance Criteria

- [ ] Any raw capture → category + tags + summary automatically
- [ ] PARA categorization working (notes land in correct subfolder)
- [ ] LLM output is parsed reliably (handle malformed JSON with retry)
- [ ] `wiki/.index.json` tracks processed state
- [ ] 10+ wiki notes created from real raw captures

### Verification

```bash
python classify.py --all
dir wiki\Projects wiki\Areas wiki\Resources wiki\Archives
type wiki\Resources\some-note.md
type wiki\.index.json
```

**Deliverable:** Organized `wiki/` folder with PARA structure and frontmatter.

---

## Phase 3 — Auto-Linking (`link.py`)

**Objective:** Compute embeddings, find semantically related notes, and insert bidirectional wiki links.  
**Badge:** 🏅 The Librarian  
**Week:** 2.2

### Tasks

- [ ] **3.1** Load `sentence-transformers/all-MiniLM-L6-v2` model (cache on first run)
- [ ] **3.2** Implement `embed_note(wiki_path) -> np.ndarray` and save to `embeddings/{note_id}.npy`
- [ ] **3.3** Build in-memory embedding index from all wiki notes
- [ ] **3.4** Implement cosine similarity comparison (numpy)
- [ ] **3.5** For each note pair above threshold (`τ = 0.75`):
  - Add slug to both notes' `links:` frontmatter array
  - Append `## Related` section with `[[linked-note-slug]]` if not present
  - Avoid duplicates and self-links
- [ ] **3.6** Implement incremental mode: `python link.py --new` (only unlinked/new notes)
- [ ] **3.7** Implement full rebuild: `python link.py --all`
- [ ] **3.8** Log similarity scores for debugging (which pairs linked and why)
- [ ] **3.9** Run on full wiki corpus — target **15+ real items** with at least some auto-links

### Acceptance Criteria

- [ ] Embeddings computed per note (`.npy` files in `embeddings/`)
- [ ] Related notes auto-linked (no manual tagging)
- [ ] Links are bidirectional where similarity is mutual above threshold
- [ ] Runs on 15+ real items → organized, linked `wiki/`
- [ ] Re-running `link.py` is idempotent (no duplicate links)

### Verification

```bash
python link.py --all
dir embeddings
# Open two related wiki notes — confirm ## Related section and links: in frontmatter
python -c "import numpy as np; print(np.load('embeddings/some_id.npy').shape)"
```

**Deliverable:** Linked wiki corpus with cached embeddings.

---

## Phase 4 — Graph Builder & Visualization Prep

**Objective:** Convert wiki notes + links into `graph.json` and prepare interactive vis-network rendering.  
**Badge:** 🏅 The Cartographer  
**Week:** 3

### Tasks

#### 4.1 — Graph Data Model (`build_graph.py`)

- [ ] **4.1.1** Walk all `wiki/**/*.md` files and parse frontmatter + body
- [ ] **4.1.2** Build node list:
  - `id` (slug), `label` (title), `para_category`, `tags`, `summary`
  - `content_preview` (first 200 chars), `full_content`, `wiki_path`
- [ ] **4.1.3** Build edge list from:
  - `links:` frontmatter array
  - `[[wiki-link]]` patterns in note bodies
- [ ] **4.1.4** Deduplicate edges; include `weight` if available from link.py
- [ ] **4.1.5** Export `graph.json` with `meta` block (counts, generated_at)
- [ ] **4.1.6** CLI: `python build_graph.py` → writes/updates `graph.json`

#### 4.2 — Graph Visualization Template

- [ ] **4.2.1** Create `static/graph_template.html` with vis-network CDN
- [ ] **4.2.2** Implement force-directed layout with physics enabled
- [ ] **4.2.3** Color nodes by PARA category:
  - Projects = `#4A90D9` (blue)
  - Areas = `#50C878` (green)
  - Resources = `#FF8C42` (orange)
  - Archives = `#9E9E9E` (gray)
- [ ] **4.2.4** Hover tooltip: title, summary, tags, content preview
- [ ] **4.2.5** Enable drag, zoom, pan
- [ ] **4.2.6** Optional: CSS pulse animation on nodes (visual "alive" effect)
- [ ] **4.2.7** Standalone test page: open HTML with injected `graph.json` data in browser

### Acceptance Criteria

- [ ] Script builds nodes + edges from notes and exports clean JSON
- [ ] `graph.json` validates against expected schema
- [ ] Graph built from real wiki notes, not dummy data
- [ ] vis-network template renders graph with hover, drag, and zoom
- [ ] Node count matches wiki note count; edge count matches link count

### Verification

```bash
python build_graph.py
python -c "import json; g=json.load(open('graph.json')); print(g['meta'])"
# Open static/graph_template.html in browser with graph data injected
```

**Deliverable:** `graph.json` + working `static/graph_template.html`.

---

## Phase 5 — RAG Q&A + Streamlit App

**Objective:** Implement `ask()` for retrieval-augmented answers and assemble the unified Streamlit UI.  
**Week:** 4.1 + 4.2 (code only — deploy in Phase 8)

### Tasks

#### 5.1 — Ask Your Brain (`ask.py`)

- [ ] **5.1.1** Implement embedding index loader (reuse `embeddings/` cache)
- [ ] **5.1.2** Implement `ask(question, top_k=5, similarity_threshold=0.5) -> AskResult`:
  - Embed the question
  - Retrieve top-K similar notes by cosine similarity
  - Assemble context from retrieved note bodies + metadata
  - Send to Groq/Llama 3 with grounded prompt
  - Return answer + source citations with relevance scores
- [ ] **5.1.3** Prompt rules:
  - Answer ONLY from provided notes
  - Cite sources as `[Source: note-title]`
  - If no notes above threshold: return honest "not enough information" message
- [ ] **5.1.4** CLI test mode: `python ask.py "What do my notes say about PARA?"`
- [ ] **5.1.5** Test with 5+ real questions about your own captured notes

#### 5.2 — Streamlit App (`app.py`)

- [ ] **5.2.1** Page layout:
  - Header: "SecondSelf — Your Personal AI Second Brain"
  - Left/main: interactive graph (vis-network via `st.components.v1.html`)
  - Right sidebar: ask-anything search bar + answer + sources
  - Footer: stats (note count, link count, last updated)
- [ ] **5.2.2** Load `graph.json` on startup; rebuild if missing/stale
- [ ] **5.2.3** Cache expensive ops: `@st.cache_data` for graph load, embedding index
- [ ] **5.2.4** "Refresh Graph" button → runs `build_graph.py` logic inline
- [ ] **5.2.5** Ask button → calls `ask()` and displays answer + clickable source links
- [ ] **5.2.6** Click node in graph → show full note content in sidebar

#### 5.3 — Pipeline Orchestrator (`pipeline.py`)

- [ ] **5.3.1** Implement `python pipeline.py` → classify → link → build_graph
- [ ] **5.3.2** Skip already-processed items via `wiki/.index.json`
- [ ] **5.3.3** Log summary: N classified, M linked, graph rebuilt

### Acceptance Criteria

- [ ] `ask()` returns answers synthesized from your own notes (retrieval + LLM)
- [ ] Answers include source citations
- [ ] `ask()` does not hallucinate when no relevant notes exist
- [ ] One Streamlit app contains both the graph and the search bar
- [ ] App runs locally: `streamlit run app.py`
- [ ] `pipeline.py` orchestrates classify → link → graph in one command

### Verification

```bash
python ask.py "Summarize my notes on productivity"
streamlit run app.py
# Browser: verify graph renders, ask bar returns grounded answer with sources
python pipeline.py
```

**Deliverable:** Working `ask.py`, `app.py`, and `pipeline.py` running locally.

---

## Phase 6 — Local Pipeline Testing

**Objective:** Verify the full backend pipeline end-to-end on real data before UI/deployment polish.

### Tasks

- [ ] **6.1** **Fresh capture test:** Capture 3 new real items (note + link + file)
- [ ] **6.2** Run full pipeline: `python pipeline.py`
- [ ] **6.3** Verify chain:
  ```
  raw/ (3 new files)
    → wiki/ (3 new classified notes in PARA folders)
    → embeddings/ (3 new .npy files)
    → wiki/ (new auto-links if similar notes exist)
    → graph.json (updated node/edge counts)
  ```
- [ ] **6.4** Verify `wiki/.index.json` reflects all processed items
- [ ] **6.5** Test edge inputs:
  - Empty note string → graceful error
  - Invalid URL → capture saves URL, fetch fails gracefully
  - Non-PDF file (e.g., `.txt`, `.png`) → copies without crash
  - Re-run `classify.py --all` → no duplicate wiki notes
  - Re-run `link.py --all` → no duplicate links
- [ ] **6.6** Confirm total corpus: **15+ real items** in wiki with embeddings

### Acceptance Criteria

- [ ] End-to-end flow works: capture → classify → link → graph
- [ ] Pipeline is idempotent on re-run
- [ ] No crashes on common edge inputs
- [ ] All index/state files stay consistent
- [ ] Logs show clear progress and errors

### Verification Checklist

| Step | Command | Expected |
|------|---------|----------|
| Capture | `python capture.py note "..."` | New file in `raw/` |
| Classify | `python classify.py --all` | New note in `wiki/` |
| Link | `python link.py --all` | Embeddings + links updated |
| Graph | `python build_graph.py` | `graph.json` updated |
| Ask | `python ask.py "..."` | Grounded answer with sources |
| Full | `python pipeline.py` | All stages complete |

**Deliverable:** Verified, repeatable local pipeline.

---

## Phase 7 — Local UI Testing

**Objective:** Validate the Streamlit app UX and RAG quality before public deployment.

### Tasks

- [ ] **7.1** Launch app: `streamlit run app.py`
- [ ] **7.2** **Graph tests:**
  - All nodes visible and colored by PARA category
  - Hover shows title, summary, preview
  - Drag repositioning works
  - Zoom in/out works
  - Click node shows full content in sidebar
- [ ] **7.3** **Ask tests** — run 10 real questions:

  | Question Type | Example | Pass If |
  |---------------|---------|---------|
  | Direct fact | "What is PARA?" | Answer cites relevant note |
  | Synthesis | "Summarize my project ideas" | Combines multiple notes |
  | Missing info | "What is quantum computing?" | Honest "not in notes" response |
  | Specific note | "What did I capture about X?" | Finds and cites that note |
  | Broad topic | "What are my areas of interest?" | Retrieves Area-category notes |

- [ ] **7.4** Test "Refresh Graph" button after adding new captures + pipeline run
- [ ] **7.5** Test app cold start (restart Streamlit — graph and ask still work)
- [ ] **7.6** Check performance: app loads in < 30s on first run (embedding model download excluded)

### Acceptance Criteria

- [ ] Interactive force-directed graph renders from real `graph.json`
- [ ] Hover reveals note content; drag + zoom work
- [ ] Ask bar returns grounded answers with source links
- [ ] UI handles empty states (no notes, no graph yet)
- [ ] No console errors in browser dev tools

**Deliverable:** Locally validated Streamlit app ready for deployment.

---

## Phase 8 — Deployment

**Objective:** Deploy the complete app to a free platform with a public URL.

### Tasks

- [ ] **8.1** Prepare repo for public deployment:
  - Add `sample_wiki/` with anonymized demo notes OR pre-built `graph.json` for demo
  - Ensure no personal data in committed files
  - Add `README.md` with setup instructions
- [ ] **8.2** Create `packages.txt` or ensure `requirements.txt` is complete for cloud build
- [ ] **8.3** Add Streamlit config `.streamlit/config.toml` (theme, layout)
- [ ] **8.4** Push to **public GitHub repo**
- [ ] **8.5** Deploy to **Streamlit Cloud** (preferred) or **Hugging Face Spaces**:
  1. Connect GitHub repo
  2. Set main file: `app.py`
  3. Add secrets: `GROQ_API_KEY`
  4. Deploy and wait for build
- [ ] **8.6** Verify public URL loads without errors
- [ ] **8.7** Document live URL in `README.md`

### Deployment Checklist

| Item | Status |
|------|--------|
| `.env` not in repo | ☐ |
| `GROQ_API_KEY` in platform secrets | ☐ |
| `requirements.txt` installs cleanly on cloud | ☐ |
| Demo data or sample wiki included | ☐ |
| `app.py` is entry point | ☐ |
| Public URL accessible | ☐ |

### Acceptance Criteria

- [ ] App deployed live with a public URL
- [ ] Graph renders on deployed instance
- [ ] Ask bar works on deployed instance (with API key)
- [ ] No secrets exposed in repo or browser

**Deliverable:** Live public URL (e.g., `https://secondself.streamlit.app`).

---

## Phase 9 — Final Verification & Ship

**Objective:** End-to-end validation on deployed app; complete all final deliverables.  
**Badge:** 🏅 The Oracle

### Tasks

- [ ] **9.1** **Deployed E2E test:**
  1. Open public URL
  2. Confirm graph loads with real/demo notes
  3. Ask 3 questions — verify grounded answers + sources
  4. Test graph interactions (hover, drag, zoom)
- [ ] **9.2** **Local E2E test** (full loop on your machine):
  ```
  capture → pipeline.py → streamlit run app.py → ask question
  ```
- [ ] **9.3** Finalize `README.md`:
  - Project description and problem statement summary
  - Architecture diagram (or link to `architecture.md`)
  - Setup: clone, venv, pip install, `.env` config
  - Usage: capture, classify, link, graph, ask commands
  - Deployment instructions
  - Live demo URL
  - Privacy note (Groq API, personal data)
- [ ] **9.4** Verify all weekly badges earned:

  | Badge | Criteria | Done |
  |-------|----------|------|
  | 🏅 The Archivist | 10+ captures in `raw/` | ☐ |
  | 🏅 The Librarian | 15+ linked wiki notes | ☐ |
  | 🏅 The Cartographer | Interactive graph from real notes | ☐ |
  | 🏅 The Oracle | Deployed app with graph + ask | ☐ |

- [ ] **9.5** Final repo cleanup:
  - Remove debug prints and temp files
  - Confirm `.gitignore` excludes personal data, secrets, embeddings
  - Tag release: `v1.0.0`

### Final Deliverables Checklist

- [ ] Public GitHub repo with clean README + setup instructions
- [ ] Live deployed URL — interactive graph + ask-your-brain search, both working
- [ ] End-to-end flow verified: capture → classify → link → graph → ask
- [ ] All 4 weekly milestones complete
- [ ] `architecture.md`, `Implementation-plan.md`, and `edge-case.md` in repo

### Verification

```bash
# Local full loop
python capture.py note "Final verification note"
python pipeline.py
streamlit run app.py

# Remote
# Open public URL → graph + ask → confirm working
```

**Deliverable:** Shipped SecondSelf v1.0 — public repo + live URL + verified pipeline.

---

## Phase Summary Timeline

```
Week 1   │ Phase 0 + Phase 1          │ Capture pipeline
Week 2   │ Phase 2 + Phase 3          │ Classify + link
Week 3   │ Phase 4                    │ Graph builder + viz
Week 4   │ Phase 5 + 6 + 7 + 8 + 9   │ Ask + UI + test + deploy
```

---

## Quick Reference — Commands

| Action | Command |
|--------|---------|
| Capture note | `python capture.py note "..."` |
| Capture link | `python capture.py link "https://..."` |
| Capture file | `python capture.py file "./doc.pdf"` |
| Classify all | `python classify.py --all` |
| Link all | `python link.py --all` |
| Build graph | `python build_graph.py` |
| Ask question | `python ask.py "Your question?"` |
| Full pipeline | `python pipeline.py` |
| Run UI | `streamlit run app.py` |

---

## Risk Register (Per Phase)

| Phase | Risk | Mitigation |
|-------|------|------------|
| 0 | Missing API key | Set up Groq account before Phase 2 |
| 1 | OneDrive path sync issues | Use local non-synced path if file locks occur |
| 2 | LLM returns invalid JSON | Retry with stricter prompt; validate with schema |
| 3 | First embedding download slow | Run once before batch; document in README |
| 4 | Orphan wiki-links (broken edges) | Validate slugs exist before adding edges |
| 5 | Streamlit + vis-network height issues | Set explicit iframe height in `st.components.v1.html` |
| 8 | Cloud cold start timeout | Pre-build `graph.json`; cache embeddings |
| 8 | Free tier resource limits | Use MiniLM (small model); limit demo corpus size |

---

*Next step: Generate [`edge-case.md`](edge-case.md) for corner scenarios and failure modes.*
