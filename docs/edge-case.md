# SecondSelf — Edge Cases & Corner Scenarios

> **Sources:** [`architecture.md`](architecture.md) · [`Implementation-plan.md`](Implementation-plan.md)  
> **Purpose:** Catalog failure modes, corner scenarios, and expected system behavior so nothing surprises us during build, test, or deploy.

**Legend**

| Priority | Meaning |
|----------|---------|
| 🔴 Critical | Pipeline crash, data loss, or security risk — must handle in v1 |
| 🟠 High | Wrong output or broken UX — should handle in v1 |
| 🟡 Medium | Degraded experience — handle if time allows |
| 🟢 Low | Rare or cosmetic — document and defer |

---

## 1. Capture Pipeline (`capture.py`) — Phase 1

### 1.1 Input Validation

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CAP-001 | Empty note string: `python capture.py note ""` | Reject with clear error: "Note content cannot be empty." Do not write to `raw/`. | 🔴 |
| CAP-002 | Whitespace-only note: `"   \n\t  "` | Treat as empty; reject same as CAP-001. | 🔴 |
| CAP-003 | Very long note (> 1 MB text) | Accept but warn; truncate metadata preview if needed. Consider soft limit at 500 KB. | 🟡 |
| CAP-004 | Note with special characters (emoji, CJK, RTL text) | Save as UTF-8; preserve content exactly. Filename uses ASCII timestamp + UUID only. | 🟠 |
| CAP-005 | Note containing YAML frontmatter delimiters (`---`) | Save raw as-is; classifier must not confuse with wiki output. | 🟡 |
| CAP-006 | Note with null bytes or binary content pasted | Strip null bytes or reject with error. | 🟠 |
| CAP-007 | Missing subcommand: `python capture.py` | Print usage help; exit code 1. | 🟡 |
| CAP-008 | Unknown subcommand: `python capture.py foo` | Print usage help; exit code 1. | 🟡 |

### 1.2 Link Capture

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CAP-010 | Invalid URL: `not-a-url` | Reject before fetch: "Invalid URL format." | 🔴 |
| CAP-011 | Non-HTTPS URL: `http://example.com` | Reject or warn per architecture (https-only policy). | 🔴 |
| CAP-012 | URL with no scheme: `example.com` | Reject or auto-prefix `https://` with user warning. | 🟠 |
| CAP-013 | URL returns 404 / 500 | Save URL + error note in body; do not crash. Mark fetch status in sidecar. | 🟠 |
| CAP-014 | URL timeout (> 10s) | Save URL only; log timeout; continue. | 🟠 |
| CAP-015 | URL redirects (301/302) | Follow redirects (max 3 hops); store final URL. | 🟡 |
| CAP-016 | URL to large page (> 5 MB HTML) | Truncate fetched text to first N chars (e.g., 50 KB). | 🟠 |
| CAP-017 | URL requires authentication (paywall, login) | Save URL + whatever public HTML was returned; note "partial fetch" in sidecar. | 🟡 |
| CAP-018 | URL to localhost / private IP (`127.0.0.1`, `192.168.x.x`) | Block fetch (SSRF prevention). Save URL string only. | 🔴 |
| CAP-019 | URL to `file://` protocol | Reject — not allowed. | 🔴 |
| CAP-020 | Duplicate URL captured twice | Both saved as separate raw files (append-only). Dedup is out of scope for v1. | 🟢 |
| CAP-021 | JavaScript-heavy SPA (empty body on fetch) | Save URL + minimal fetched text; classifier works with URL + title tag if present. | 🟡 |
| CAP-022 | URL with unicode / IDN domain | Encode properly; fetch with punycode if needed. | 🟡 |

### 1.3 File Capture

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CAP-030 | File does not exist | Error: "File not found: {path}". Exit 1. | 🔴 |
| CAP-031 | File exceeds 10 MB limit | Reject with clear size error. | 🔴 |
| CAP-032 | Empty file (0 bytes) | Accept copy; sidecar notes `size: 0`; classifier may produce minimal wiki note. | 🟡 |
| CAP-033 | PDF with no extractable text (scanned image) | Copy PDF; text sidecar empty or "no text extracted"; classify from filename/metadata. | 🟠 |
| CAP-034 | Password-protected PDF | Copy PDF; extraction fails gracefully; note in sidecar. | 🟠 |
| CAP-035 | Corrupt / malformed PDF | Copy PDF; log extraction error; continue. | 🟠 |
| CAP-036 | Non-PDF binary: `.png`, `.jpg`, `.zip` | Copy to `raw/` with original extension; no text sidecar; classify from filename. | 🟠 |
| CAP-037 | `.txt`, `.md`, `.csv` file | Copy + optionally inline text content for classifier. | 🟡 |
| CAP-038 | Filename with spaces, unicode, or special chars | Sanitize destination filename; preserve original in sidecar `original_filename`. | 🟠 |
| CAP-039 | Path traversal attempt: `../../etc/passwd` | Resolve to absolute path; reject if outside allowed directories. | 🔴 |
| CAP-040 | Symlink to file outside project | Do not follow symlinks outside project root; reject or warn. | 🔴 |
| CAP-041 | Same file captured twice | Two separate raw entries (different UUIDs). Content hash in sidecar for future dedup. | 🟢 |

### 1.4 Storage & Filesystem

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CAP-050 | `raw/` directory does not exist | Auto-create on first capture. | 🟠 |
| CAP-051 | Disk full during write | Fail with IO error; do not leave partial/corrupt file (write to temp then rename). | 🔴 |
| CAP-052 | OneDrive sync lock on file (Windows) | Retry write 2–3 times with backoff; log if persistent. | 🟠 |
| CAP-053 | Two captures in same second | UUID ensures unique filenames even if timestamps collide. | 🟠 |
| CAP-054 | Sidecar `.meta.json` write fails after content saved | Log warning; content file remains valid; retry sidecar or rebuild from filename. | 🟡 |
| CAP-055 | User manually edits/deletes raw file | Pipeline must handle missing files gracefully on classify (skip + warn). | 🟡 |
| CAP-056 | User manually adds file to `raw/` without sidecar | Classifier reads content directly; generate metadata on the fly or prompt re-capture. | 🟡 |

---

## 2. Auto-Classification (`classify.py`) — Phase 2

### 2.1 LLM & API Failures

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CLS-001 | Missing `GROQ_API_KEY` | Fail fast with: "Set GROQ_API_KEY in .env". | 🔴 |
| CLS-002 | Invalid / expired API key | Catch 401; print actionable error; do not corrupt index. | 🔴 |
| CLS-003 | Groq rate limit (429) | Exponential backoff retry (3 attempts); then skip file and log. | 🔴 |
| CLS-004 | Groq server error (500/503) | Retry with backoff; mark file as `status: failed` in index after max retries. | 🔴 |
| CLS-005 | Network offline during classify | Fail gracefully; leave raw unprocessed; no partial wiki write. | 🔴 |
| CLS-006 | Request timeout | Retry once; then mark failed. | 🟠 |
| CLS-007 | Token limit exceeded (very long raw capture) | Truncate input to model context window; note truncation in wiki body footer. | 🟠 |

### 2.2 LLM Output Quality

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CLS-010 | LLM returns invalid JSON | Retry with stricter prompt ("JSON only, no markdown fences"). Max 3 retries. | 🔴 |
| CLS-011 | LLM wraps JSON in markdown code fences | Strip ` ```json ` fences before parsing. | 🔴 |
| CLS-012 | LLM returns invalid `para_category` (e.g., "Personal") | Map to nearest valid PARA bucket or default to `Resources`; log warning. | 🟠 |
| CLS-013 | LLM returns empty tags array | Accept; write `tags: []`. | 🟢 |
| CLS-014 | LLM returns empty summary | Generate fallback: first sentence of body or "No summary available." | 🟡 |
| CLS-015 | LLM returns empty title | Derive slug from first line of body or raw filename. | 🟠 |
| CLS-016 | LLM hallucinates content not in raw capture | Prompt instructs "do not invent facts"; keep body close to source. | 🟡 |
| CLS-017 | LLM assigns wrong PARA category | Accept for v1; user can manually move file later. Document limitation. | 🟢 |
| CLS-018 | Note fits multiple PARA categories | Assign one (per ADR-004); tags capture secondary themes. | 🟡 |
| CLS-019 | Non-English content | Classify and tag in source language; do not force English translation unless configured. | 🟡 |

### 2.3 Wiki File Generation

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CLS-020 | Title produces duplicate slug | Append short UUID suffix: `my-note-a3f9.md`. | 🔴 |
| CLS-021 | Title with `/`, `\`, or filesystem-unsafe chars | Sanitize slug: lowercase, hyphens, alphanumeric only. | 🔴 |
| CLS-022 | Very long title (> 200 chars) | Truncate slug; keep full title in frontmatter `title` field. | 🟡 |
| CLS-023 | Raw file already classified (in `.index.json`) | Skip on `--all`; overwrite only with explicit `--force` flag. | 🔴 |
| CLS-024 | Raw file deleted but still in index | Remove stale index entry or mark `status: missing_source`. | 🟡 |
| CLS-025 | YAML frontmatter special chars in summary (quotes, colons) | Properly escape YAML strings. | 🔴 |
| CLS-026 | Body contains `---` mid-document | Use frontmatter library that handles delimiters correctly. | 🟠 |
| CLS-027 | Classify single file not in `raw/`: `python classify.py wiki/foo.md` | Reject: "Expected path under raw/." | 🟡 |
| CLS-028 | Empty raw file (0 bytes) | Skip with warning or produce stub wiki note with "Empty capture." | 🟡 |
| CLS-029 | `.index.json` corrupted / invalid JSON | Backup corrupt file; rebuild index by scanning wiki frontmatter `source_raw` fields. | 🟠 |
| CLS-030 | Concurrent classify runs (two terminals) | File locking or atomic index updates; last writer wins with warning. | 🟡 |

---

## 3. Auto-Linking (`link.py`) — Phase 3

### 3.1 Embeddings

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| LNK-001 | First run — model not downloaded | Download `all-MiniLM-L6-v2` (~80 MB); show progress; cache locally. | 🟠 |
| LNK-002 | Model download fails (offline) | Fail with clear error; do not partial-write embeddings. | 🔴 |
| LNK-003 | Wiki note with empty body | Embed title + summary only; skip if all empty. | 🟠 |
| LNK-004 | Very long note (> 10k tokens) | Truncate to first N chars for embedding; log truncation. | 🟡 |
| LNK-005 | Embedding file missing for existing note | Recompute on next `link.py --all`. | 🟠 |
| LNK-006 | Embedding dimension mismatch (model changed) | Detect shape mismatch; delete stale `.npy`; re-embed all. | 🔴 |
| LNK-007 | Single note in corpus (no pairs) | Skip linking; write embedding; log "insufficient corpus for links." | 🟡 |
| LNK-008 | Non-English notes | MiniLM handles multilingual reasonably; no special case needed for v1. | 🟢 |

### 3.2 Similarity & Linking Logic

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| LNK-010 | All pairs below threshold (0.75) | No links added; log "0 links created." | 🟢 |
| LNK-011 | Threshold too low → too many false-positive links | Tunable via `SIMILARITY_THRESHOLD` in config; document recommended range 0.70–0.85. | 🟡 |
| LNK-012 | Threshold too high → no links at all | Same as LNK-010; user lowers threshold. | 🟢 |
| LNK-013 | Note similar to itself | Never self-link; exclude same slug from comparison. | 🔴 |
| LNK-014 | A similar to B, but B not similar to A (asymmetric) | v1: link if either direction above threshold, or require mutual — document chosen policy. Recommend: link if max(A→B, B→A) ≥ τ. | 🟠 |
| LNK-015 | Duplicate link already exists | Idempotent: do not add second `[[slug]]` or duplicate frontmatter entry. | 🔴 |
| LNK-016 | Linked note slug no longer exists (deleted wiki file) | On `--all`, prune broken links from frontmatter and body. | 🟠 |
| LNK-017 | Link would create `## Related` section twice | Merge into existing section; no duplicate headers. | 🟠 |
| LNK-018 | 100+ related notes above threshold | Cap max links per note (e.g., top 10 by similarity score). | 🟡 |
| LNK-019 | Notes with identical content (duplicate captures) | High similarity → linked; dedup is separate concern. | 🟡 |
| LNK-020 | Re-run `link.py --all` after manual wiki edit | Re-read files; update links; do not duplicate. | 🔴 |
| LNK-021 | User manually removed a link | `--all` may re-add if similarity still above threshold; `--new` respects existing. Document behavior. | 🟡 |

### 3.3 File Modification

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| LNK-030 | Frontmatter parse fails during link update | Skip file; log error; do not corrupt file. | 🔴 |
| LNK-031 | Write fails mid-update (disk full) | Atomic write: temp file + rename. | 🔴 |
| LNK-032 | Note moved to different PARA folder manually | Links use slugs (not paths); still valid if slug unchanged. | 🟡 |
| LNK-033 | Slug renamed manually | Orphan edges in graph until rebuild; link.py should update by ID not slug in v2. | 🟡 |

---

## 4. Graph Builder (`build_graph.py`) — Phase 4

### 4.1 Node Construction

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| GRPH-001 | Empty wiki (no notes) | Export valid JSON: `{ "meta": { "node_count": 0, "edge_count": 0 }, "nodes": [], "edges": [] }`. | 🔴 |
| GRPH-002 | Wiki note missing frontmatter | Skip or include with defaults; log warning. | 🟠 |
| GRPH-003 | Missing `para_category` in frontmatter | Default to `Resources`; gray color in graph. | 🟠 |
| GRPH-004 | Duplicate slugs in different PARA folders | Should not happen if classify is correct; last wins + log error. | 🔴 |
| GRPH-005 | Note with empty title | Use slug as label. | 🟡 |
| GRPH-006 | `full_content` exceeds JSON size ( huge notes) | Truncate `full_content` to 10 KB for graph; full text stays in wiki file. | 🟠 |
| GRPH-007 | Special characters in node label break JSON | Proper JSON escaping via `json.dump`. | 🔴 |
| GRPH-008 | HTML/markdown in content breaks vis-network tooltip | Escape HTML entities in tooltip text. | 🟠 |

### 4.2 Edge Construction

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| GRPH-010 | Link in frontmatter points to non-existent slug | Skip edge; log orphan link warning. | 🟠 |
| GRPH-011 | `[[wiki-link]]` in body points to missing note | Skip edge; log warning. | 🟠 |
| GRPH-012 | Duplicate edge (frontmatter + body reference same target) | Deduplicate; keep higher weight if available. | 🟠 |
| GRPH-013 | Bidirectional links (A→B and B→A) | Single undirected edge or two directed edges — pick one; vis-network treats as one edge. | 🟡 |
| GRPH-014 | Self-loop in frontmatter | Skip self-loop edge. | 🟠 |
| GRPH-015 | Malformed `[[link]]` syntax: `[[`, `[[ note ]]` | Ignore malformed patterns; regex strict on `[[slug]]`. | 🟡 |
| GRPH-016 | Link slug case mismatch: `[[My-Note]]` vs `my-note` | Normalize slugs to lowercase for matching. | 🟠 |

### 4.3 Output & Staleness

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| GRPH-020 | `graph.json` write fails | Keep previous `graph.json` if exists; log error. | 🔴 |
| GRPH-021 | Wiki updated but graph not rebuilt | App shows stale graph until refresh; "Refresh Graph" button triggers rebuild. | 🟡 |
| GRPH-022 | 500+ nodes — graph unusably dense | Still export; UI may warn "large graph"; physics tuning or filter by PARA category (v2). | 🟡 |
| GRPH-023 | Single isolated node (no edges) | Include as node with zero edges; renders as lone dot. | 🟢 |

---

## 5. Interactive Graph (UI) — Phases 4, 5, 7

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| UI-001 | `graph.json` missing on app start | Auto-run `build_graph.py` or show empty state with instructions. | 🔴 |
| UI-002 | `graph.json` malformed | Show error banner; fall back to rebuild. | 🔴 |
| UI-003 | Zero nodes | Show: "No notes yet. Capture something to get started." | 🟠 |
| UI-004 | vis-network CDN unreachable | Bundle vis-network locally in `static/` as fallback. | 🟠 |
| UI-005 | Graph iframe height = 0 (Streamlit quirk) | Set explicit `height=600` in `st.components.v1.html()`. | 🔴 |
| UI-006 | Hover tooltip overflow (very long content) | Truncate preview to 200 chars in tooltip. | 🟡 |
| UI-007 | Node click with no sidebar space (mobile) | Collapsible sidebar or modal for note content. | 🟡 |
| UI-008 | Rapid zoom/pan causes lag (100+ nodes) | Disable physics after stabilization; limit node count label rendering. | 🟡 |
| UI-009 | JSON injected into HTML causes XSS | Escape all user content before JS injection; use `json.dumps` not string concat. | 🔴 |
| UI-010 | Dark mode / light mode contrast | PARA colors must be readable on both; test in Streamlit themes. | 🟢 |

---

## 6. RAG Q&A (`ask.py`) — Phase 5

### 6.1 Retrieval

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| ASK-001 | Empty question string | Reject: "Please enter a question." | 🔴 |
| ASK-002 | Question with only whitespace | Same as ASK-001. | 🔴 |
| ASK-003 | No embeddings exist yet | Return: "No indexed notes found. Run the pipeline first." | 🔴 |
| ASK-004 | No notes above similarity threshold (0.5) | Return honest message: "I don't have enough in your notes to answer that." Do NOT call LLM. | 🔴 |
| ASK-005 | Question in different language than notes | Embed as-is; MiniLM cross-lingual retrieval may be weak — return best effort. | 🟡 |
| ASK-006 | Very long question (> 2k chars) | Truncate question for embedding. | 🟡 |
| ASK-007 | Top-K notes exceed LLM context window | Truncate retrieved bodies; prioritize highest similarity first. | 🔴 |
| ASK-008 | Retrieved notes contradict each other | LLM prompt: "If notes conflict, mention the conflict and cite both sources." | 🟡 |
| ASK-009 | Question about future events / general knowledge not in notes | Retrieval scores low → fallback message; no hallucination. | 🔴 |
| ASK-010 | Question exactly matches a note title | That note should rank #1; verify retrieval sanity. | 🟡 |

### 6.2 LLM Synthesis

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| ASK-020 | Groq API failure during ask | Return: "Unable to generate answer. Try again later." Include retrieved sources if available. | 🔴 |
| ASK-021 | LLM hallucinates facts not in retrieved notes | Grounding prompt + low temperature; post-check that answer cites provided sources only. | 🔴 |
| ASK-022 | LLM refuses to answer | Return refusal message; show sources anyway. | 🟡 |
| ASK-023 | LLM returns answer without citations | Prompt requires `[Source: title]` format; retry if missing. | 🟠 |
| ASK-024 | Single retrieved note — answerable | Synthesize concise answer from one source. | 🟢 |
| ASK-025 | Retrieved notes all from Archives | Still valid; answer from archived content. | 🟢 |
| ASK-026 | Prompt injection in user question: "Ignore instructions..." | System prompt anchors to notes-only; do not execute embedded instructions. | 🟠 |
| ASK-027 | Prompt injection in note content | Same — treat note body as data, not instructions. | 🟠 |

### 6.3 Ask CLI & App Integration

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| ASK-030 | `python ask.py` with no arguments | Print usage example. | 🟡 |
| ASK-031 | Multiple questions in rapid succession (Streamlit) | Disable button during processing; show spinner. | 🟠 |
| ASK-032 | `@st.cache_data` serves stale embedding index | Cache invalidates when `embeddings/` mtime changes or on "Refresh". | 🟠 |
| ASK-033 | Source link in UI points to deleted wiki file | Graceful "source unavailable" in UI. | 🟡 |

---

## 7. Pipeline Orchestrator (`pipeline.py`) — Phases 5, 6

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| PIPE-001 | Pipeline run with empty `raw/` | Log "Nothing to process." Exit 0. | 🟡 |
| PIPE-002 | Classify succeeds, link fails | Report partial success; graph build uses whatever wiki exists. | 🟠 |
| PIPE-003 | Pipeline interrupted mid-run (Ctrl+C) | No corrupt index; resume skips completed items. | 🔴 |
| PIPE-004 | One raw file fails classification; others succeed | Continue batch; summarize failures at end. | 🔴 |
| PIPE-005 | Pipeline run while Streamlit app is open | File reads may be stale; app refresh picks up changes. | 🟡 |
| PIPE-006 | `wiki/.index.json` out of sync with filesystem | Reconciliation: scan wiki for `source_raw` and rebuild index. | 🟠 |
| PIPE-007 | Partial pipeline: only new items since last run | `--all` vs default incremental; document flags. | 🟡 |

---

## 8. Configuration & Environment — Phase 0

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| CFG-001 | `.env` file missing | Load defaults; warn that `GROQ_API_KEY` is required for classify/ask. | 🟠 |
| CFG-002 | Invalid value for `SIMILARITY_THRESHOLD` (e.g., `"abc"`) | Fall back to default 0.75; log warning. | 🟡 |
| CFG-003 | Threshold outside 0.0–1.0 | Clamp to valid range; warn. | 🟡 |
| CFG-004 | Custom `RAW_DIR` / `WIKI_DIR` via env | All modules read from `config.py`; paths created if missing. | 🟡 |
| CFG-005 | Project run from wrong working directory | Use paths relative to project root (resolve via `config.py` base dir). | 🔴 |
| CFG-006 | Python 3.9 or below | Document 3.11+ requirement; may fail on type hints. | 🟡 |

---

## 9. Security & Privacy

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| SEC-001 | `.env` accidentally committed to git | `.gitignore` blocks; pre-push checklist in README. | 🔴 |
| SEC-002 | Personal notes pushed to public GitHub | `.gitignore` for `raw/` and `wiki/` OR use `sample_wiki/` for deploy. | 🔴 |
| SEC-003 | API key visible in Streamlit browser devtools | Keys only in server-side secrets; never in frontend JS. | 🔴 |
| SEC-004 | Note content sent to Groq (third party) | Disclose in README; user opts in by providing API key. | 🟠 |
| SEC-005 | SSRF via link capture (internal URLs) | Block private IP ranges and non-HTTPS (CAP-018, CAP-019). | 🔴 |
| SEC-006 | XSS via note content in graph HTML | Escape all injected content (UI-009). | 🔴 |
| SEC-007 | Path traversal via CLI file argument | Validate resolved path (CAP-039). | 🔴 |
| SEC-008 | Malicious PDF (exploit in parser) | Use pypdf with updated version; catch parse exceptions. | 🟠 |
| SEC-009 | Public deployment exposes ask() to anonymous users | Accept for demo; rate-limit or auth in v2 if abuse occurs. | 🟡 |

---

## 10. Deployment — Phases 8, 9

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| DEP-001 | Streamlit Cloud build fails on `sentence-transformers` | Pin versions; add `packages.txt` for system deps if needed. | 🔴 |
| DEP-002 | Cold start timeout (> 60s) | Pre-build `graph.json`; lazy-load embedding model on first ask. | 🔴 |
| DEP-003 | Out of memory on free tier (model load) | Use MiniLM only; limit demo corpus; `@st.cache_resource` for model. | 🔴 |
| DEP-004 | `GROQ_API_KEY` not set in cloud secrets | App loads graph; ask returns "API key not configured." | 🔴 |
| DEP-005 | Repo has no wiki data for demo | Ship `sample_wiki/` + pre-built `graph.json`. | 🟠 |
| DEP-006 | OneDrive-synced repo causes deploy issues | Push from clean local clone; not directly from synced folder. | 🟡 |
| DEP-007 | Hugging Face Spaces GPU not available | CPU inference for MiniLM is sufficient. | 🟡 |
| DEP-008 | App sleeps on free tier (Streamlit) | Accept cold start on revisit; show loading spinner. | 🟡 |
| DEP-009 | vis-network blocked by CSP on cloud platform | Use inline/bundled JS; avoid external CDN if blocked. | 🟠 |
| DEP-010 | User visits public URL and asks about private demo data | Demo data is intentionally public/anonymized. | 🟢 |

---

## 11. Data Integrity & Recovery

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| DAT-001 | User deletes a wiki note manually | Graph rebuild removes node; backlinks become orphan edges (GRPH-010). | 🟡 |
| DAT-002 | User edits wiki note body manually | Re-embed on next `link.py --all`; graph reflects on rebuild. | 🟡 |
| DAT-003 | `embeddings/` deleted but wiki intact | Regenerate all embeddings on next link run. | 🟠 |
| DAT-004 | `graph.json` deleted but wiki intact | Rebuild via `build_graph.py` or app auto-rebuild. | 🟠 |
| DAT-005 | Entire `wiki/` lost; `raw/` intact | Re-run `classify.py --all` to regenerate wiki. | 🟠 |
| DAT-006 | `wiki/.index.json` lost | Rebuild from wiki frontmatter `source_raw` fields. | 🟠 |
| DAT-007 | Git merge conflict in `.index.json` | Document: prefer manual merge or regenerate index. | 🟡 |
| DAT-008 | Same content captured 5 times | 5 raw files, 5 wiki notes, 5 highly similar nodes — expected; dedup is v2. | 🟢 |

---

## 12. Performance & Scale

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| PERF-001 | 15 notes (target corpus) | All operations complete in < 30s locally. | 🟢 |
| PERF-002 | 100 notes | Link O(n²) comparisons ~ 10k pairs — acceptable (< 1 min). | 🟡 |
| PERF-003 | 1,000+ notes | O(n²) linking becomes slow; document SQLite/ANN for v2 (ADR-001). | 🟡 |
| PERF-004 | Batch classify 50 raw files | Respect Groq rate limits; sequential with backoff. | 🟠 |
| PERF-005 | Large PDF (10 MB, 500 pages) | Text extraction may be slow; run async or show progress. | 🟡 |
| PERF-006 | Graph with 200+ nodes in browser | Laggy physics; stabilize then disable physics. | 🟡 |

---

## 13. Cross-Module Edge Cases (End-to-End)

| ID | Scenario | Expected Behavior | Priority |
|----|----------|-------------------|----------|
| E2E-001 | Capture → immediate ask (before pipeline) | Ask finds nothing; UI prompts to run pipeline. | 🟠 |
| E2E-002 | Full loop: capture → pipeline → ask | New note appears in graph and is retrievable by ask. | 🔴 |
| E2E-003 | Capture link that 404s → classify → ask "what was that link?" | Answer references URL and fetch failure note. | 🟡 |
| E2E-004 | Classify note to Projects; later archive manually | Graph color may not update until para_category in frontmatter changed. | 🟡 |
| E2E-005 | Re-capture same PDF after editing it | New raw entry; two wiki notes; both linked if similar. | 🟢 |
| E2E-006 | Run on machine A, deploy graph built on machine B | Paths in `wiki_path` are relative — works if same repo structure. | 🟠 |
| E2E-007 | Unicode note title appears in ask citation | Citation renders correctly in Streamlit markdown. | 🟡 |

---

## 14. Testing Matrix (Phase 6 & 7 Quick Reference)

Use this checklist during local testing to confirm edge-case handling:

### Capture (Phase 6.5)

- [ ] Empty note → error, no file
- [ ] Invalid URL → error, no crash
- [ ] HTTPS URL that 404s → saved with fetch failure noted
- [ ] 11 MB file → rejected
- [ ] `.png` file → copied, no crash
- [ ] Re-capture same content → two separate files

### Classification

- [ ] Re-run `classify.py --all` → no duplicate wiki notes
- [ ] Missing API key → clear error message
- [ ] Very long note → classified (possibly truncated)

### Linking

- [ ] Re-run `link.py --all` → no duplicate links
- [ ] Single note corpus → no crash
- [ ] Embeddings directory deleted → regenerated

### Graph

- [ ] Empty wiki → valid empty `graph.json`
- [ ] Orphan `[[link]]` → skipped with warning in logs

### Ask

- [ ] Question about unknown topic → "not enough information"
- [ ] Empty question → rejected
- [ ] Question about known topic → answer with sources

### Pipeline

- [ ] Ctrl+C mid-pipeline → resumable without corruption
- [ ] One failure in batch → others still processed

### UI (Phase 7)

- [ ] Empty graph state → friendly message
- [ ] Ask during LLM call → button disabled / spinner shown
- [ ] Refresh graph after new capture → updated node count

---

## 15. Out of Scope for v1 (Document Only)

These scenarios are known limitations — do not block v1 ship:

| Scenario | Planned Handling |
|----------|------------------|
| Duplicate content deduplication | v2: hash-based dedup at capture |
| Manual PARA override UI | v2: edit in Streamlit sidebar |
| Offline LLM (no Groq) | v2: Ollama integration |
| Multi-user / auth | v2: login + namespaces |
| Real-time sync across devices | v2: cloud storage or git sync workflow |
| OCR for scanned PDFs | v2: tesseract integration |
| Audio/video capture | v2: transcription pipeline |
| Version history for notes | v2: git-based or SQLite audit log |
| Undo delete | v2: trash folder |
| Browser extension capture | v2: extension → capture API |

---

## 16. Edge-Case Handling Principles

When implementing, follow these rules consistently:

1. **Never crash silently** — log the error, print a user-readable message, exit with non-zero code where appropriate.
2. **Never corrupt data** — use atomic writes (temp + rename); partial failures leave prior state intact.
3. **Fail closed on security** — block SSRF, path traversal, and XSS rather than permissive defaults.
4. **Fail open on retrieval** — if no relevant notes, say so honestly; do not hallucinate.
5. **Idempotent pipelines** — re-running classify/link/graph must not duplicate or break existing data.
6. **Recoverable state** — `wiki/` is source of truth; `embeddings/`, `graph.json`, and `.index.json` are regenerable.

---

*Referenced by [`Implementation-plan.md`](Implementation-plan.md) Phase 6 (local testing) and Phase 7 (UI testing). Update this document when new edge cases are discovered during implementation.*
