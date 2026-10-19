# UroCura OS — Multimodal Urology AI Coding, NCCI Chapter 7 Rules Engine & Revenue Recovery Platform

> **"The chart and the claim should not tell different stories."**
> Inspired by the [Vitrocura](https://www.vitrocura.com/) clinical and revenue-cycle operating system, **UroCura OS** identifies and recovers legitimate revenue left on the table between the urologist's multimodal clinical encounter and the hospital/clinic billing department's scrubbed `X12 837P` claim.

---

## 1. Core Capabilities & The 4 Coding Authority Pillars

1. **Pillar 1 — AMA CPT with Strict Temporal Version Control (`CPT 2026` vs. `CPT 2027`)**:
   - Routes every claim strictly by **Date of Service (`DOS`)**.
   - Prevents retrospective audit failures and clearinghouse rejections across year boundaries (e.g., automatically migrating sunset Category III `0421T` to new **CPT 2027** Category I `52598` for robotic waterjet prostate ablation on `DOS >= 2027-01-01`, and blocking deleted legacy codes like `53853`).
2. **Pillar 2 — AMA CPT Assistant Interpretive Authority & Clinical Vignette RAG**:
   - Grounds edge-case unbundling decisions in official AMA CPT Assistant clinical vignettes (e.g., *Vol. 26, Issue 3* for contralateral ureteral stenting `52356-RT` + `52332-XS-LT`; *Vol. 31, Issue 8* for dual diagnostic transrectal ultrasound `76872` + ultrasonic needle biopsy guidance `76942-59` alongside prostate biopsy `55700`).
3. **Pillar 3 — CMS / NCCI Deterministic Edits & Policy Manual Chapter 7 (`CPT 50000–58999`)**:
   - Answers **"I performed X and Y. Can I report both?"** using the CMS NCCI Procedure-to-Procedure (PTP) bundling matrix (`Modifier Indicator 0` = Never unbundle vs. `Modifier Indicator 1` = Conditionally unbundleable with `-59`/`-XS`/`-XE`/`-XP`/`-XU`/`-25`), Medically Unlikely Edits (`MUE` daily unit caps), and verbatim **2026 NCCI Policy Manual Chapter 7 (Genitourinary System)** citations.
   - Computes exact locality-adjusted Medicare allowed amounts using **MPFS Relative Value Files (`RVU26D-nonQP` / `RVU26D-QP` / `RVU27A`)**, including the CY 2026 `-2.5%` efficiency adjustment, Bilateral Indicator `1` (`150%` payment with Modifier `-50`), Multiple Procedure Payment Reduction (`100% / 50% / 50%` MPPR), and Add-On Code (`Global = ZZZ`, `100%` payment) rules.
4. **Pillar 4 — Specialty-Specific Urology Coding Layer (AUA CodingPlus-Aligned Clean-Room Rules) & MAC LCDs**:
   - First-party deterministic urology heuristics (`URO-01`..`URO-07`) covering TURBT single-largest-tumor sizing (`52234` vs. `52235` vs. `52240`), buy-and-bill HCPCS Level II J-codes (`J9030` BCG, `J0585` Botox + `-JW` single-dose vial wastage, `J9155` Degarelix `1 mg/unit` conversion, `J9217` Leuprolide), multichannel urodynamics (`51729` + `+51797` + `51784` + `51741` while blocking bundled `51798` PVR), and dual-string MAC resolution (`National Government Services (NGS)` $\leftrightarrow$ `Wellpoint Federal (formerly NGS)` effective `2026-04-01`).

---

## 2. Repository Structure

| File | Description |
| :--- | :--- |
| [`DESIGN.md`](file:///Users/nitinagga/Documents/billing/DESIGN.md) | Full end-to-end architectural blueprint, 6-Node LangGraph + Deterministic Rules Engine specification, database schema, and MPFS payment formulas. |
| [`seed_urology.py`](file:///Users/nitinagga/Documents/billing/seed_urology.py) | Initializes and seeds `urology_coding.db` with CPT 2026/2027 catalogs, MPFS RVUs, GPCI localities, NCCI PTP & MUE edits, CPT Assistant / NCCI Ch. 7 guidance, MAC LCD articles, NPI benchmarks, and 8 multimodal clinical encounters. |
| [`generate_sample_uploads.py`](file:///Users/nitinagga/Documents/billing/generate_sample_uploads.py) | Generates 5 authentic binary clinical sample files in `sample_uploads/` (`.pdf` `%PDF-1.4`, `.png` `89 50 4E 47`, `.jpg` `FF D8 FF E0`, `.dcm` DICOM Part-10 `DICM`, and `.837p.txt` ANSI X12 837P EDI claim). |
| [`cms_ingest.py`](file:///Users/nitinagga/Documents/billing/cms_ingest.py) | Production CMS landing-page discovery, million-row streaming NCCI PTP TSV parser, NGS $\rightarrow$ Wellpoint Federal MAC normalizer, and CPT 2026 $\leftrightarrow$ 2027 version diff verifier. |
| [`app.py`](file:///Users/nitinagga/Documents/billing/app.py) | Full-stack HTTP server (`0.0.0.0:$PORT`, default `8080`, `SIGTERM`-safe) serving the REST API (`/api/*`, including `POST /api/upload-analyze` and `GET /api/sample-files`) and the 5-Workspace Executive Light UI. |
| [`static/index.html`](file:///Users/nitinagga/Documents/billing/static/index.html) | 100% Fluid Edge-to-Edge, Zero-Blank-Space (`Rule 25H`) Executive Light Web Application with 5 high-density workspaces, 0 truncated top tabs, a single-row 5-column filter toolbar (`56px`), a Multi-File Binary Drag-and-Drop Discrepancy Studio (`#multimodal-dropzone`) with 5 distinct file cards & real `360x140px` handwritten JPEG preview, 0px internal bottom gaps across all paired cards, and a non-blocking Docked Right-Side Multimodal Inspector Drawer. |
| [`src/index.css`](file:///Users/nitinagga/Documents/billing/src/index.css) | Global stylesheet enforcing Rule 54 Executive Light Theme, WCAG 2.1 AA contrast (`--text-muted: #475569`, `:focus-visible` rings), Rule 25G 100% fluid layout, Rule 25H zero internal card/viewport blank space, and Rule 26 rigid table cell containment with Mobile (`390x844`) specificity override. |
| [`tests/test_e2e_forensic.py`](file:///Users/nitinagga/Documents/billing/tests/test_e2e_forensic.py) | 8-Gate automated backend, binary upload, and clinical math E2E verification suite. |
| [`scripts/stop_forensic_gate.mjs`](file:///Users/nitinagga/Documents/billing/scripts/stop_forensic_gate.mjs) | Automated Headless Chrome 3-Subagent UI/UX Visual Forensic Gate (`ui-designer` + `cross-viewport-auditor` + `a11y-code-hygiene-auditor`) verifying `1600x950`/`834x1194`/`390x844` viewports across all 5 tabs, 0 tab truncation, 1-row filter toolbar, `0px` paired-card internal bottom gaps, 1-line drawer close button, and WCAG 2.1 AA / ARIA compliance. |
| [`AGENTS.md`](file:///Users/nitinagga/Documents/billing/AGENTS.md) | Normative workspace governance constitution and quality gate invariants. |

---

## 3. End-User Multimodal File Upload & Discrepancy Detection Workflow

1. **Multi-File Drag-and-Drop or File Picker (`Workspace 3: 3. Upload Docs & 6-Node Analyzer`)**:
   - Click **`📤 Upload PDF / PNG / JPEG / DICOM / 837P`** in the top toolbar or navigate to Tab 3 (`#multimodal-dropzone`).
   - Drag and drop (or browse from disk) any combination of:
     - **`.pdf`**: Operative Reports & Surgical Pathology Addenda (`%PDF-1.4` parsed via native text stream / `FlateDecode` extractor).
     - **`.png` / `.jpg` / `.jpeg`**: Handwritten physician superbills or post-op margin notes (`IHDR`/`tEXt` & `SOF0`/`COM` + Vision Handwritten Medical OCR with live image thumbnail preview).
     - **`.dcm`**: DICOM Part 10 CT Urogram / TRUS Ultrasound studies (`128-byte` preamble + `DICM` magic header + Explicit VR Little Endian tags `(0008,0060)`, `(0008,1030)`, `(0018,0050)`, `(0020,4000)`).
     - **`.837p` / `.txt` / `.csv`**: Billing Dept scrubbed ANSI X12 837P EDI claim files (`DTP*472` Date of Service, `HI*` ICD-10-CM diagnosis pointers, and `SV1*HC:` service lines).
   - Or click **`📂 Load & Analyze 5 Real Binary Sample Files (.PDF + .PNG + .JPG + .DCM + .837P)`** to test all 5 binary formats in 1 click.
2. **6-Node Pipeline & Line-by-Line Discrepancy Matrix (`#upload-discrepancy-table`)**:
   - **Node 0 (Magika Magic-Byte Gate)** classifies each binary stream independent of file extension.
   - **Node 1 (HIPAA Safe Harbor PHI Gate)** scrubs all 18 PHI identifiers (`[REDACTED-NAME]`, `[REDACTED-MRN]`, `[REDACTED-SSN]`) before downstream analysis.
   - **Nodes 2–5** extract clinical measurements, route to **CPT 2026 vs. CPT 2027** by Date of Service, evaluate NCCI Chapter 7 PTP/MUE/MPPR rules, and render an explicit **Line-by-Line Discrepancy Reconciliation Table** comparing *What Uploaded Docs Prove* vs. *What Billing 837P Coded* vs. *AI-Verified Fix & Dollar Recovery*.

---

## 4. Quick Start & Verification

```bash
# 1. Seed the verified Urology SQLite database & generate 5 real binary sample files
python3 seed_urology.py
python3 generate_sample_uploads.py

# 2. Verify CMS Ingestion Pipeline & CPT 2026 <-> 2027 Temporal Version Diff
python3 cms_ingest.py --verify-local-seed --diff-versions 2026 2027

# 3. Run the 8-Gate E2E Backend, Binary Upload & Clinical Rules Test Suite
python3 tests/test_e2e_forensic.py

# 4. Run the Headless Chrome Multi-Viewport & Rule 25/26/54 Forensic UI Gate
node scripts/stop_forensic_gate.mjs

# 5. Launch the UroCura OS Server (http://localhost:8080)
python3 app.py
```
