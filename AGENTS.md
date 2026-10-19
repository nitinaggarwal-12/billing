# AGENTS.md — UroCura OS Normative Workspace Constitution (`v2.0`)

## 1. Core Architectural & Clinical Coding Invariants

1. **Two-Engine Hybrid Mandate (Stateful LangGraph + Deterministic CMS/NCCI Rules Engine)**:
   - Never rely on unconstrained LLM prompts or keyword matching for CPT/HCPCS selection or NCCI unbundling.
   - All clinical encounters must pass through the **6-Node Stateful Pipeline**:
     1. `Node 1`: HIPAA Safe Harbor 18-Identifier PHI Redaction Gate (`redact_phi_safe_harbor`).
     2. `Node 2`: Multimodal Extraction (Handwritten Vision OCR, Operative PDF via Docling schema, Surgical Pathology ICD-10-CM specificity, and `pydicom` tag & slice extraction).
     3. `Node 3`: Temporal Version Controller (`AMA_CPT_2026` vs. `AMA_CPT_2027` routed strictly by Date of Service `DOS`).
     4. `Node 4`: Deterministic CMS / NCCI / MPFS / MAC LCD Rules Engine (`ncci_ptp_edits`, `ncci_mue`, `mpfs_rvu`, `gpci_localities`, `mac_lcd_articles`).
     5. `Node 5`: 4-Pillar Interpretive RAG & Revenue Delta Calculator (`AMA CPT`, `AMA CPT Assistant`, `CMS NCCI Policy Manual Chapter 7`, and `Specialty Urology Rules URO-01..URO-07`).
     6. `Node 6`: Human-in-the-Loop (HITL) Sign-Off & X12 835 Remittance (`CARC`/`RARC`) Continuous Learning Store (`coder_feedback_loop`).

2. **Strict Temporal Version Control (`CPT 2026` vs. `CPT 2027` Effective Jan 1, 2027)**:
   - Every audit finding must carry an explicit version stamp (`AMA_CPT_2026` vs. `AMA_CPT_2027`).
   - Dates of Service on or after `2027-01-01` must automatically migrate sunset Category III codes (e.g., `0421T` $\rightarrow$ Category I `52598`) and apply 2027 descriptors/RVUs.

3. **Zero AUA Copyright Ingestion Invariant**:
   - Never scrape or ingest proprietary AUA publications into LLM training or RAG vector stores. Specialty urology coding heuristics (`URO-01`..`URO-07`) must be maintained as clean-room deterministic clinical rules derived from public CMS/AMA regulations.

4. **Universal Executive Light Theme, 100% Fluid Layout & Rigid Table Containment (`Rule 25`, `Rule 26` & `Rule 54`)**:
   - **Rule 54**: Root canvas `#f8fafc`, cards/tables/drawers `#ffffff`, primary text `#0f172a`, zero dark-mode root classes.
   - **Rule 25**: 100% fluid edge-to-edge layout (`width: 100%; max-width: 100%`), single persistent 5-tab top navigation bar, non-blocking right-side docked drawer (`.docked-drawer`), zero `window.alert()`/`window.prompt()`, and live filter binding with `#no-matching-cards` empty state.
   - **Rule 26**: Global table cell containment (`overflow: hidden; max-width: 0;`) on `table.table-fixed tbody td` and `.gp-blue-grid-table tbody td`, and `span.truncate { display: inline-block; max-width: 100%; }`.

5. **Multimodal Binary File Upload & Discrepancy Reconciliation (`POST /api/upload-analyze` & `GET /api/sample-files`)**:
   - Inspect binary magic headers (`%PDF-1.4`, `\x89PNG\r\n\x1a\n`, `\xFF\xD8\xFF` JPEG, `128-byte preamble + DICM` Part-10 DICOM, and `ANSI X12 837P`) via `classify_and_extract_binary_file` before running Node 1 PHI redaction and Nodes 2–5 line-by-line discrepancy reconciliation (`#multimodal-dropzone`, `#uploaded-files-extraction-grid`, `#upload-discrepancy-table`).

6. **Fail-Closed Automated Quality Gates**:
   - Every change must pass both `python3 tests/test_e2e_forensic.py` (`8/8` backend, binary upload, & clinical math gates) and `node scripts/stop_forensic_gate.mjs` (`100%` multi-viewport zero-overflow & DOM verification).
