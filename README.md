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
| [`cms_ingest.py`](file:///Users/nitinagga/Documents/billing/cms_ingest.py) | Production CMS landing-page discovery, million-row streaming NCCI PTP TSV parser, NGS $\rightarrow$ Wellpoint Federal MAC normalizer, and CPT 2026 $\leftrightarrow$ 2027 version diff verifier. |
| [`app.py`](file:///Users/nitinagga/Documents/billing/app.py) | Full-stack HTTP server (`0.0.0.0:$PORT`, default `8080`, `SIGTERM`-safe) serving the REST API (`/api/*`) and the 5-Workspace Executive Light UI. |
| [`static/index.html`](file:///Users/nitinagga/Documents/billing/static/index.html) | 100% Fluid Edge-to-Edge Executive Light Web Application with 5 interactive workspaces and a non-blocking Docked Right-Side Multimodal Inspector Drawer. |
| [`src/index.css`](file:///Users/nitinagga/Documents/billing/src/index.css) | Global stylesheet enforcing Rule 54 Executive Light Theme, Rule 25G 100% fluid layout, and Rule 26 rigid table cell containment. |
| [`tests/test_e2e_forensic.py`](file:///Users/nitinagga/Documents/billing/tests/test_e2e_forensic.py) | 7-Gate automated backend & clinical math E2E verification suite. |
| [`scripts/stop_forensic_gate.mjs`](file:///Users/nitinagga/Documents/billing/scripts/stop_forensic_gate.mjs) | Automated Headless Chrome multi-viewport (`1600x950`, `834x1194`, `390x844`) geometry, Rule 25/26/54 static audit, and E2E DOM test runner. |
| [`AGENTS.md`](file:///Users/nitinagga/Documents/billing/AGENTS.md) | Normative workspace governance constitution and quality gate invariants. |

---

## 3. Quick Start & Verification

```bash
# 1. Seed the verified Urology SQLite database
python3 seed_urology.py

# 2. Verify CMS Ingestion Pipeline & CPT 2026 <-> 2027 Temporal Version Diff
python3 cms_ingest.py --verify-local-seed --diff-versions 2026 2027

# 3. Run the 7-Gate E2E Backend & Clinical Rules Test Suite
python3 tests/test_e2e_forensic.py

# 4. Run the Headless Chrome Multi-Viewport & Rule 25/26/54 Forensic UI Gate
node scripts/stop_forensic_gate.mjs

# 5. Launch the UroCura OS Server (http://localhost:8080)
python3 app.py
```
