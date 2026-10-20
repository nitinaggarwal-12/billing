# UroCura OS — End-to-End Architecture & System Design (`v2.0`)
**Multimodal Urology AI Coding, NCCI Chapter 7 Deterministic Rules Engine & Revenue Recovery Platform**
*(Inspired by Vitrocura Clinical & Revenue-Cycle Operating System — "The chart and the claim should not tell different stories.")*

---

## 1. Executive Summary & Business Viability ("Is It Worth It?")

### Why Urology Revenue Leakage Is a High-ROI Opportunity
In US hospital outpatient departments (HOPDs), Ambulatory Surgery Centers (ASCs), and specialty urology practices, **11% to 18% of legitimate, clinically documented revenue is lost between the physician's encounter documentation and the submitted X12 837P claim**. Unlike primary care (which relies predominantly on E/M codes `99213`–`99215`), urology combines:
1. **High-Complexity Endoscopic & Surgical Bundling (`CPT 50010–58999`)**: Procedures such as ureteroscopy with laser lithotripsy (`52353`), indwelling ureteral stent insertion (`52332`), and bundled lithotripsy-with-stent (`52356`) interact with hundreds of **CMS National Correct Coding Initiative (NCCI) Procedure-to-Procedure (PTP)** edits. Over-cautious billing departments frequently strip legitimate secondary procedures (e.g., contralateral stenting or separate-site biopsy) out of fear of NCCI denials instead of applying the appropriate anatomical/distinct-procedural modifiers (`-59`, `-XS`, `-XU`, `-RT`, `-LT`, `-50`).
2. **Morphology- & Measurement-Dependent Code Stratification**: Transurethral resection of bladder tumors (**TURBT**: `52234` small `0.5–2.0 cm`, `52235` medium `2.0–5.0 cm`, `52240` large `>5.0 cm`) depends on the exact centimeter measurement recorded in the operative note or pathology gross description. When a billing coder defaults to `52234` because the tumor dimension was buried in a handwritten diagram or ultrasound image, the practice loses **$240–$410 per case** in Medicare allowed amounts (and **$600–$1,100+** under commercial contracts).
3. **Buy-and-Bill HCPCS Level II J-Code Under-Capture**: In-office urology heavily utilizes expensive biologics and chemotherapeutics—intravesical **BCG (`J9030`)**, **OnabotulinumtoxinA / Botox (`J0585`)** for overactive bladder (`52287`), **Leuprolide acetate (`J9217`)**, and **Degarelix (`J9155`)**. Omitting drug units, failing to document single-dose vial wastage (`-JW` / `-JZ` modifiers), or dropping the paired administration code (`51720` / `96402`) creates immediate thousands-of-dollars leakage.
4. **Multimodal Documentation Fragmentation**: The evidence justifying a code rarely lives in a single text box. The procedure is in the **Operative Note PDF**, the exact stone burden (`14 mm`) or prostate volume (`68 cc`) is in the **DICOM CT/TRUS header & slice image**, the malignancy stage (`C67.2` lateral wall bladder cancer vs. `D49.4` unspecified neoplasm) arrives 72 hours later in the **Surgical Pathology Report**, and the physician's immediate post-op billing intent is sketched on a **Handwritten Encounter Superbill / Margin Note**.

---

## 2. Two-Engine Hybrid Architecture: Stateful LangGraph Orchestration + Deterministic Rules Engine

Pure LLM prompt frameworks (like unstructured chat agents or BMAD) fail in healthcare billing because LLMs hallucinate NCCI modifier indicators, confuse 2026 and 2027 CPT descriptors, and miscalculate Medicare Multiple Procedure Payment Reduction (**MPPR**) math. Conversely, pure legacy claim scrubbers only inspect the codes *after* the billing clerk has already deleted them—they never read the operative PDF, handwritten note, pathology report, or DICOM slices to discover what *should* have been billed.

UroCura combines **two tightly coupled engines** inside a 6-Node Stateful Cyclic Graph:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       UROCURA CLINICAL & REVENUE OPERATING SYSTEM                      │
│     100% Fluid Executive Light UI · 3-Way Claim Reconciliation · Docked Audit Drawer   │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ REST API (`/api/audit`, `/api/ptp-check`)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               NODE 1: HIPAA SAFE HARBOR PHI REDACTION & MAGIKA ROUTER                  │
│   • Strips 18 HIPAA identifiers (Name, MRN, DOB, SSN, Address, Dates->Year/DOS Token)  │
│   • Classifies payloads: Handwritten Image | Operative/Pathology PDF | DICOM (.dcm)    │
└──────────────┬───────────────────────────┬─────────────────────────────┬───────────────┘
               │                           │                             │
               ▼                           ▼                             ▼
┌──────────────────────────┐ ┌───────────────────────────┐ ┌─────────────────────────────┐
│ NODE 2A: HANDWRITTEN OCR │ │ NODE 2B: PDF/DOCLING NODE │ │ NODE 2C: DICOM VISION NODE  │
│ • Vision OCR & Layout    │ │ • Operative Report Parser │ │ • pydicom Tag Extractor     │
│ • Shorthand expansion    │ │ • Pathology Stage/Grade   │ │ • 16-bit Voxel -> PNG Slice │
│   ("R URS/LL + B/L stnt")│ │ • Urodynamics Matrix      │ │ • Stone mm / Prostate cc    │
└──────────────┬───────────┘ └─────────────┬─────────────┘ └─────────────┬───────────────┘
               └───────────────────────────┼─────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│            NODE 3: TEMPORAL VERSION CONTROLLER & CLINICAL ENTITY SYNTHESIZER           │
│   • Resolves Date of Service (DOS) -> Selects `CPT 2026` vs. `CPT 2027` Catalog        │
│   • Extracts Anatomic Site, Laterality (RT/LT/Bilateral), Tumor cm, Stone mm, Drug mg  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│            NODE 4: DETERMINISTIC CMS / NCCI / MPFS / MAC LCD RULES ENGINE              │
│   • Check 1: Temporal Code Validity (Active vs. Deleted/Superseded in 2026 vs. 2027)   │
│   • Check 2: NCCI PTP Bundling Matrix (Col 1 / Col 2 + Modifier Indicator 0 / 1 / 9)   │
│   • Check 3: NCCI Medically Unlikely Edits (MUE Daily Unit Ceiling & MAI 1/2/3)        │
│   • Check 4: MPFS RVU Indicators (Bilateral 0/1/2/3, MPPR 50%, Global 000/010/090/ZZZ) │
│   • Check 5: MAC-Specific LCD & Billing Article ICD-10-CM Medical Necessity Crosswalk  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│          NODE 5: INTERPRETIVE RAG & SPECIALTY UROLOGY REASONING ENGINE                 │
│   • AMA CPT Assistant Clinical Vignette & Interpretive Guidance Retrieval              │
│   • CMS NCCI Policy Manual Chapter 7 (Urinary/Male/Female Genital) Verbatim Citations  │
│   • Specialty Urology Heuristics (Buy-and-Bill J-Codes, TURBT Single-Largest Rule,     │
│     TRUS + Ultrasonic Guidance 76872+76942, E/M Modifier -25 Justification)            │
│   • Calculates Exact "Money Left on the Table" ($Δ = Verified Claim − Billing 837P)    │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│         NODE 6: HUMAN-IN-THE-LOOP (HITL) CHECKPOINT & X12 835 LEARNING LOOP            │
│   • Pauses high-dollar / modifier-unbundled claims for Coder or Physician Sign-Off     │
│   • Ingests X12 835 Remittance Advice (CARC/RARC denials & payments) to update weights │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Evaluation of the 4 Core Coding & Interpretive Pillars

### Pillar 1: AMA CPT with Strict Temporal Version Control (`CPT 2026` vs. `CPT 2027`)
- **Architectural Requirement**: Every CPT code, descriptor, RVU weight, and bundling edit is keyed by `(code, effective_year, effective_start_date, effective_end_date)`.
- **Why Version Control Is Non-Negotiable**:
  - The AMA releases the new CPT code set annually (e.g., **CPT 2027** effective **January 1, 2027**).
  - An encounter with a Date of Service (`DOS`) of `2026-11-15` audited or appealed in `2027-02-10` **must** be evaluated strictly against the `CPT 2026` + `NCCI Q4 2026` + `MPFS RVU26D` rule set. Conversely, a service performed on `2027-01-12` must use `CPT 2027` descriptors and `RVU27A`.
  - UroCura stores explicit version stamps on every audit finding (`cpt_version`, `ncci_version`, `mpfs_version`, `lcd_version`) and exposes a dedicated **CPT 2026 $\leftrightarrow$ 2027 Version Diff & Migration Matrix** in the UI.

### Pillar 2: AMA CPT Assistant (Interpretive Authority & Clinical Vignette RAG)
- **Architectural Requirement**: A raw 5-digit CPT descriptor (`52356 — Cystourethroscopy, with ureteroscopy and/or pyeloscopy; with lithotripsy including insertion of indwelling ureteral stent`) tells you *what* the code is, but not *edge-case clinical boundaries*.
- **How UroCura Uses It**:
  - The `interpretive_guidance` table indexes structured rule summaries and clinical scenarios mapped to CPT Assistant citations (e.g., *CPT Assistant, Vol. 26, Issue 3: Reporting 52356 with contralateral 52332-59*; *CPT Assistant, Vol. 31, Issue 8: Reporting diagnostic TRUS 76872 alongside ultrasonic needle guidance 76942 during prostate biopsy 55700 when both a diagnostic anatomical survey and needle placement guidance are documented*).
  - Every AI recommendation cites the exact CPT Assistant issue and explains the documentation elements present in the operative report that satisfy the vignette criteria.

### Pillar 3: CMS / NCCI Deterministic Edits & Policy Manual Chapter 7 (`CPT 50000–58999`)
- **Architectural Requirement**: Answering *"I performed X and Y. Can I report both?"* requires two distinct CMS artifacts:
  1. **The Quantitative Edit Tables (`ncci_ptp_edits` & `ncci_mue`)**:
     - Contains `(column1_code, column2_code, modifier_indicator, effective_date)`.
     - `modifier_indicator = 0`: **Never unbundle**. Column 2 is an integral component of Column 1 under all circumstances (e.g., `52240` + `52234` multiple bladder tumors during the same session).
     - `modifier_indicator = 1`: **Conditionally unbundleable** with an NCCI-associated modifier (`-59`, `-XE` Separate Encounter, `-XS` Separate Structure/Organ, `-XP` Separate Practitioner, `-XU` Unusual Non-Overlapping Service) *only if* clinical documentation proves a distinct anatomic site, contralateral organ, or separate session.
  2. **The Qualitative Narrative Authority (`NCCI Policy Manual — Chapter 7: Genitourinary System`)**:
     - Provides the verbatim regulatory prose shown to the physician and billing compliance officer (e.g., *NCCI Policy Manual Chap. 7, Sec. F.4: "Diagnostic cystourethroscopy (CPT code 52000) is integral to surgical cystourethroscopy procedures and shall not be separately reported."*).

### Pillar 4: Specialty-Specific Urology Coding Layer (AUA CodingPlus-Equivalent Domain Rules)
- **Compliance & IP Hygiene**: Because AUA terms prohibit ingesting raw proprietary AUA publications directly into external LLM training corpora, UroCura encodes specialty-specific urology coding logic as **first-party deterministic clinical rules (`urology_specialty_rules`)** authored from public CMS/AMA regulations and verified urology clinical standards while flagging human reference pointers for certified urology coders:
  - **Rule URO-01 (TURBT Single-Largest-Tumor Mandate)**: Resection of multiple bladder tumors (`52234`, `52235`, `52240`) in one session maps strictly to a single unit of the code corresponding to the **single largest tumor diameter** (not the sum of diameters under Medicare NCCI Chapter 7, and never multiple TURBT codes together).
  - **Rule URO-02 (Ureteroscopy + Lithotripsy + Stent Bundling & Contralateral Carve-Out)**: Same-side `52353` + `52332` collapses into `52356`. However, if a diagnostic or therapeutic stent (`52332`) is placed in the **contralateral** ureter, `52356-RT` + `52332-XS-LT` is compliant and recovers **+$186–$410**.
  - **Rule URO-03 (Prostate Biopsy Dual Ultrasound Capture)**: When performing `55700` (prostate needle biopsy), if the urologist documents both a diagnostic transrectal ultrasound evaluation of prostate volume/lesions (`76872`) AND ultrasonic needle placement guidance (`76942`), both codes are reportable with distinct documentation.
  - **Rule URO-04 (Buy-and-Bill J-Code & Wastage Recovery)**: Every intravesical instillation (`51720`) or bladder chemodenervation (`52287`) or LHRH depot injection (`96402`) triggers an automatic cross-check against the medication administration log and NDC barcode (`J9030` BCG, `J0585` Botox 100U + `-JW`/`-JZ`, `J9217` Leuprolide, `J9155` Degarelix).
  - **Rule URO-05 (Pathology-Driven ICD-10-CM Specificity Upgrade)**: Holds or amends claims when initial post-op diagnosis (`R31.0` gross hematuria or `D49.4` neoplasm of unspecified behavior) is upgraded by surgical pathology to site-specific urothelial carcinoma (`C67.2` lateral wall, `C67.5` bladder neck, `C61` prostate adenocarcinoma) required by MAC Local Coverage Articles.

---

## 4. Database Schema (`urology_coding.db`)

| Table | Primary Key | Description |
| :--- | :--- | :--- |
| `cpt_hcpcs_catalog` | `(code, version_year)` | Version-controlled CPT (`2026`, `2027`) & HCPCS Level II codes, descriptors, category, status (`ACTIVE`, `REVISED`, `DELETED`, `NEW_2027`), and change notes. |
| `mpfs_rvu` | `(code, version_year)` | Work RVU, Non-Facility PE RVU, Facility PE RVU, MP RVU, Global Period (`000`/`010`/`090`/`ZZZ`), Bilateral Indicator (`0`/`1`/`2`/`3`), Multiple Procedure Indicator (`0`/`2`/`3`), and 2026 `-2.5%` efficiency adjustment flag. |
| `ncci_ptp_edits` | `(col1_code, col2_code, effective_year)` | Deterministic NCCI Procedure-to-Procedure pairs, Modifier Indicator (`0`/`1`/`9`), allowed modifiers, unbundle clinical condition, and NCCI Policy Manual Chapter 7 section citation. |
| `ncci_mue` | `(code, effective_year)` | Medically Unlikely Edits max daily units (`mue_limit`), MUE Adjudication Indicator (`MAI 1/2/3`), and unit rationale. |
| `interpretive_guidance` | `guidance_id` | AMA CPT Assistant clinical vignettes, NCCI Policy Manual Chapter 7 narrative sections, and Specialty Urology (`URO-01`..`URO-08`) decision rules. |
| `mac_lcd_articles` | `(article_id, mac_contractor)` | Medicare Administrative Contractor (`Novitas`, `Palmetto GBA`, `Wellpoint Federal / NGS`, `Noridian`, `CGS`, `First Coast`, `WPS`) Local Coverage Determinations & covered ICD-10-CM arrays. |
| `clinical_encounters` | `encounter_id` | Full multimodal patient cases: Handwritten Note OCR, Operative PDF, Pathology Report, DICOM `.dcm` tags & slice metrics, Doctor's Draft Codes, Billing Dept `837P` Codes, and AI Verified Claim. |
| `npi_peer_benchmarks` | `npi` | CMS Medicare Physician & Other Practitioners PUF + NPPES urologist profiles and state specialty decile benchmarks. |
| `coder_feedback_loop` | `feedback_id` | HITL coder/physician sign-offs, overrides, documentation addenda, and X12 835 Remittance (`CARC`/`RARC`) outcome logs. |
| `dataset_version_stamps` | `source_key` | Tracks exact version, effective date, row count, and SHA-256 hash of every ingested CMS/AMA dataset. |

---

## 5. MPFS Payment & "Money Left on the Table" Formula

For each line item $i$ in a claim under locality GPCI $(G_w, G_{pe}, G_{mp})$ and Conversion Factor $CF$ (where $CF_{2026,\text{non-QP}} = \$33.4009$, $CF_{2026,\text{QP}} = \$33.5675$, and $CF_{2027} = \$33.8500$):

$$\text{BaseAllowed}_i = \left[ (\text{RVU}_{w,i} \cdot E_{\text{adj}} \cdot G_w) + (\text{RVU}_{pe,i} \cdot G_{pe}) + (\text{RVU}_{mp,i} \cdot G_{mp}) \right] \times CF$$

Where:
1. **2026 Efficiency Adjustment ($E_{\text{adj}}$)**: For non-time-based surgical/endoscopic codes subject to the CY 2026 MPFS Final Rule efficiency adjustment, $E_{\text{adj}} = 0.975$ ($-2.5\%$).
2. **Bilateral Surgery Adjustment (`bilateral_ind = 1` with Modifier `-50`)**: Paid at **$150\%$** of the single-side base allowed amount.
3. **Multiple Procedure Payment Reduction (`mult_proc_ind = 2`)**: When multiple surgical procedures are performed in the same session, the highest-RVU procedure is paid at **$100\%$** and each subsequent `mult_proc_ind = 2` surgical procedure is paid at **$50\%$**.
4. **Add-On Codes (`global_period = ZZZ`) & Buy-and-Bill Drugs (`J-codes`)**: Paid at **$100\%$** (exempt from MPPR reduction; J-codes priced via CMS ASP $+ 6\%$ $\times$ billed units).
5. **Money Left on the Table ($\Delta_{\text{recovery}}$)**:
   $$\Delta_{\text{recovery}} = \sum_{i \in \text{AI Verified Claim}} \text{NetAllowed}_i - \sum_{j \in \text{Billing Dept 837P}} \text{NetAllowed}_j$$

---

## 6. Multimodal Binary File Upload & Discrepancy Reconciliation Architecture

The end user uploads clinical files via the HTML5 Multi-File Drag-and-Drop & File Picker Dropzone (`#multimodal-dropzone` in `Workspace 3: 3. Upload Docs & 6-Node Analyzer`) or `POST /api/upload-analyze`:

1. **Node 0 — Magic-Byte File Classification (`classify_and_extract_binary_file`)**:
   - Inspects raw binary header signatures (Google Magika pattern) independent of file extension:
     - **`%PDF-1.4` (`PDF_DOCUMENT`)**: Parsed via `_extract_pdf_text_streams` (uncompressed `(...) Tj` / `(...) '` operators with escaped parenthesis handling + `FlateDecode` zlib decompression) and split into Operative vs. Surgical Pathology sections.
     - **`89 50 4E 47 0D 0A 1A 0A` (`PNG_HANDWRITTEN_IMAGE`)**: Parsed via `_extract_png_metadata_and_ocr` (`IHDR` pixel dimensions, `tEXt`/`iTXt` OCR chunks + Gemini Vision Handwritten Medical OCR fallback, plus live `data:image/png;base64,...` thumbnail preview).
     - **`FF D8 FF E0` (`JPEG_HANDWRITTEN_IMAGE`)**: Parsed via `_extract_jpeg_metadata_and_ocr` (`SOF0`/`SOF2` dimensions, `COM` `0xFFFE` OCR segment + Gemini Vision Handwritten Medical OCR fallback, plus live `data:image/jpeg;base64,...` thumbnail preview).
     - **`128-Byte Preamble + 44 49 43 4D (DICM)` (`DICOM_IMAGING_STUDY`)**: Parsed via `_extract_dicom_tags` reading Explicit VR Little Endian tags `(0008,0060)` Modality, `(0008,1030)` Study Description, `(0018,0050)` Slice Thickness, and `(0020,4000)` Quantitative Measurements.
     - **`ISA*` / `CLM*` / `SV1*HC:` (`X12_837P_EDI_CLAIM`)**: Parsed via `_extract_837p_or_text_claim` extracting `DTP*472*D8*YYYYMMDD` Date of Service, `HI*` ICD-10-CM diagnosis pointers, and `SV1*HC:<code>:<mod>*<charge>*UN*<units>` billed lines.
2. **Nodes 1–5 — Line-by-Line Discrepancy Reconciliation Matrix (`#upload-discrepancy-table`)**:
   - Scrubs all 18 HIPAA Safe Harbor PHI identifiers (`Node 1`), routes to `AMA_CPT_2026` vs. `AMA_CPT_2027` (`Node 3`), evaluates deterministic NCCI Chapter 7 PTP/MUE/MPPR rules (`Node 4`), and produces an explicit `discrepancies` array comparing *What Uploaded Docs Prove* against *What Billing 837P Coded* with exact dollar recovery (`+$3,935.55` / `+$3,574.74` across the 5-file sample packet).
3. **Rule 25H & 3-Subagent UI/UX Visual Forensic Architecture (`ui-designer`, `cross-viewport-auditor`, `a11y-code-hygiene-auditor`)**:
   - **Zero Tab Truncation & Single-Row Filter Toolbar (`Rule 25A`–`25E`)**: All 5 primary workspace tabs render without ellipsis truncation (`scrollWidth <= clientWidth` on `1600x950`); `.filter-toolbar` uses a single-row 5-column CSS Grid (`1.6fr 1fr 1.15fr 0.95fr auto`, `56px` height) with zero duplicate navigation/upload buttons.
   - **Zero Paired-Card Internal Bottom Gaps (`0px` across Workspaces 2, 3, 4, 5)**: Paired `.two-col-grid > .section-card` columns match natural content heights (`0px` internal bottom gap) via live clinical telemetry boxes (`#ptp-pair-mue-telemetry` + Node 4 MPPR Audit Gate in Workspace 2, `#sim-left-telemetry-strip` in Workspace 3, full-width 5-column `.mac-lcd-grid` + CY 2026/2027 Conversion Factor Reference Box in Workspace 4, and `#gpci-formula-callout` with worked locality proofs in Workspace 5).
   - **Distinct 5-File Extraction Cards & Real `360x140px` Handwritten JPEG Preview**: `.extracted-file-card` displays compact human-readable modality badges (`837P EDI`, `DICOM`, `JPEG OCR`, `PNG OCR`, `PDF DOC`), distinct short filenames, a real `360x140px` handwritten surgical progress note JPEG scan (`18,375 bytes`), and a 4-line `.file-preview-snippet` clamp (`74px` height, `15px` line-height) that never slices text horizontally.
   - **Cross-Viewport (`1600x950`, `834x1194`, `390x844`) & WCAG 2.1 AA Accessibility**: Mobile `@media (max-width: 640px)` overrides `table.table-fixed tbody td, .gp-blue-grid-table tbody td { max-width: 100%; width: 100%; }` (`348px` full cell width); Tablet `@media (max-width: 1100px)` spans odd last-child items across both columns (`grid-column: 1 / -1`); `--text-muted: #475569` guarantees `>= 6.4:1` contrast; and full ARIA `role="tablist"`, `role="tab"`, `role="tabpanel"`, `role="dialog"`, `<th scope="col">`, and `:focus-visible` keyboard focus rings are enforced.

---

## 6A. Navigation Model, URL Contract & Keyboard Map (Rule 25A/25D/25H, WAI-ARIA Tabs, WCAG 2.4.3)

**Single navigation surface.** Five task-named top tabs own all routing; no panel renders a second navigation rail or page switcher. Technical descriptors (NCCI Ch. 7, 6-node LangGraph, 4-pillar authority) live in each panel's section header, never in the tab label.

| Tab | Label (user sees) | Internal key | URL slug | Primary action (`Cmd/Ctrl+Enter`) |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Work Queue | `queue` | `?tab=queue` | — (`/` focuses search) |
| 2 | Code Pair Check | `ptp` | `?tab=pairs` | `runPtpEvaluation()` |
| 3 | Upload & Analyze | `simulator` | `?tab=upload` | `runLiveSimulator()` |
| 4 | Rules & Versions | `governance` | `?tab=rules` | — |
| 5 | Peer Benchmarks | `benchmarks` | `?tab=benchmarks` | — |

**URL state.** `switchWorkspace(key)` writes `?tab=<slug>` with `history.pushState` (user action) or `replaceState` (restore); an open dossier adds `&enc=<ENCOUNTER_ID>`. `popstate` → `restoreFromUrl()` so browser Back/Forward and reload restore the exact workspace and open dossier. Bootstrap calls `restoreFromUrl()` after data loads.

**Keyboard map.**

| Keys | Behaviour |
| :-- | :-- |
| `←` `→` `Home` `End` (focus on a tab) | Move selection + focus across the tablist (roving `tabindex`: active tab `0`, others `-1`) |
| `Alt+1` … `Alt+5` | Jump to workspace 1–5 |
| `/` | Focus the Work Queue search (switches to Tab 1 if needed) |
| `Cmd/Ctrl+Enter` | Run the active workspace's primary action |
| `Esc` | Close the docked dossier drawer |
| `Tab` / `Shift+Tab` inside the drawer | Cycle within the drawer while it is open |

**Docked drawer (Rule 25F).** `openDrawer(id, { trigger })` records the originating button, moves focus to the dossier heading (`#drw-title[tabindex=-1]`, retried across frames because `visibility` is still hidden at transition p=0), and writes `&enc=`. Header controls: `Collapse →` (slides to a 52px rail with an `◀ Expand` button so the dossier stays one click away), `✕ Close` (Esc). `closeDrawer()` restores focus to the originating control and removes `&enc=`. Each Work Queue row has exactly **one** drawer trigger (the `Inspect Dossier →` button; the encounter ID is plain text) plus a distinct secondary handoff `Check pair A + B →` that deep-links into Code Pair Check with both AI-verified codes prefilled.

**Header (Rule 25A/25D/25G).** Single compact row (`~91px` including tabs): brand + short context on the left, global-only telemetry pills on the right (`CPT 2026 · 2027 routing by DOS`, `PHI Safe Harbor gate on`, `Pending HITL: N`, `Coder verified: N` — derived live from encounter data). Header pills never repeat values owned by a workspace KPI card; the slogan subtitle was removed. First Work Queue row starts at `346px` (gate threshold `<= 380px`).

## 6B. 5-State Completeness, Honest Failure & Token-Only Components

- **Loading**: `setButtonBusy(btn, true, label)` disables the primary button, sets `aria-busy`, and shows a staged label (`Running Nodes 0–5…`); `renderSkeleton(card)` paints shimmer rows sized to the final layout (`aria-busy` on the card). Busy state is set synchronously before the first `await` so even sub-50ms local calls expose it.
- **Error / Retry**: `renderErrorState(card, what, detail, retryJs)` renders an inline `role="alert"` box with `↺ Retry`; upload retry re-submits the cached `LAST_UPLOAD_PACKET` so users never re-select files. HITL sign-off **never** fakes `CODER_VERIFIED` on API failure — status stays unchanged and the toast says why.
- **Empty**: `renderEmptyState(...)` seeds the upload results area before the first analysis; Work Queue keeps `#no-matching-cards` with `↺ Reset All Filters`.
- **Zero silent synthetic fallback (Rule 25L)**: when served over HTTP, a failed `/api/ptp-check` shows the error state; the illustrative fallback exists only for `file://` standalone demos and is labelled *Offline demo — illustrative only*.
- **Tokens only**: component templates use CSS custom properties (`--emerald-strong`, `--rose-text`, `--paper-bg`, …); `0` raw hex inside `style="..."`. Motion animates specific properties only (`0` `transition: all`) on the `120/200/320ms` scale and honours `prefers-reduced-motion`. Emoji are not used as icons in chrome (only `✓`/`✕` glyphs; toasts are the single allowed emoji surface).
- **Fail-closed gate** (`scripts/stop_forensic_gate.mjs` → *Navigation & IA Gate*): `firstRowTopPx <= 380`, `0` header/KPI duplicates, `1` trigger per row and `0` non-button triggers, `ArrowRight` moves selection+focus+URL, `?tab=` survives reload and Back, focus inside drawer on open / returned on Esc, collapse rail `40–70px`, synchronous busy state + skeleton, plus static checks for slogan, `transition: all`, reduced-motion, inline hex, and emoji icons.

---

## 7. Quick Start & Verification Commands

```bash
# 1. Seed the verified Urology SQLite database & generate 5 real binary sample files
python3 seed_urology.py
python3 generate_sample_uploads.py

# 2. Run the CMS Ingestion & Version Diff Verifier
python3 cms_ingest.py --verify-local-seed --diff-versions 2026 2027

# 3. Start the UroCura Clinical & Revenue Operating System Server (Port 8080)
python3 app.py

# 4. Run the Full 8-Gate E2E & Headless Chrome Forensic Test Suite
python3 tests/test_e2e_forensic.py
node scripts/stop_forensic_gate.mjs
```

