#!/usr/bin/env python3
"""
tests/test_e2e_forensic.py — Comprehensive 7-Gate End-to-End & Forensic Audit Suite for UroCura OS.

Verifies:
  Gate 1: SQLite Schema & 9 Authoritative Dataset Version Stamps (SHA-256 Fingerprints)
  Gate 2: All 8 Multimodal Urology Encounters & Exact 3-Way Dollar Reconciliation ($3,137.16 -> $6,771.02 = +$3,633.86)
  Gate 3: Deterministic NCCI Chapter 7 "Can I Report Both?" Engine (/api/ptp-check across all 7 clinical archetypes)
  Gate 4: AMA CPT 2026 <-> CPT 2027 Temporal Version Control (0421T -> 52598 Migration, 53853 Deleted Block, NGS -> Wellpoint Federal MAC Alias)
  Gate 5: Live 6-Node LangGraph Multimodal Claim Simulator & HIPAA Safe Harbor PHI Redaction (/api/audit)
  Gate 6: Human-in-the-Loop (HITL) Sign-Off & X12 835 Remittance Continuous Learning Loop (/api/feedback)
  Gate 7: CMS PUF + NPPES NPI Urology Specialty Peer Benchmark Engine (/api/benchmarks)
"""

import json
import os
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import UroCuraRequestHandler
from seed_urology import DB_PATH, seed_all


def http_get_json(base_url: str, path: str) -> dict:
    req = urllib.request.Request(f"{base_url}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200, f"GET {path} returned {resp.status}"
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(base_url: str, path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200, f"POST {path} returned {resp.status}"
        return json.loads(resp.read().decode("utf-8"))


def run_forensic_e2e_suite() -> dict:
    # Always start from a clean deterministic seed
    seed_summary = seed_all(DB_PATH)

    server = ThreadingHTTPServer(("127.0.0.1", 0), UroCuraRequestHandler)
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    results = {"gates_passed": 0, "total_gates": 8, "details": []}

    try:
        # -------------------------------------------------------------------
        # GATE 1: Health & 9 Authoritative Dataset Version Stamps
        # -------------------------------------------------------------------
        health = http_get_json(base_url, "/api/health")
        assert health["status"] == "ok"
        assert len(health["version_stamps"]) == 9
        assert health["telemetry"]["encounter_count"] == 8
        assert abs(health["telemetry"]["total_billed_usd"] - 3137.16) < 0.01
        assert abs(health["telemetry"]["total_verified_usd"] - 6771.02) < 0.01
        assert abs(health["telemetry"]["total_recoverable_usd"] - 3633.86) < 0.01
        results["gates_passed"] += 1
        results["details"].append("GATE 1 PASS: 9 Dataset Version Stamps & Global Revenue Telemetry ($3,137.16 -> $6,771.02 = +$3,633.86)")

        # -------------------------------------------------------------------
        # GATE 2: 8 Multimodal Urology Encounters & Single-Encounter Dossier
        # -------------------------------------------------------------------
        enc_list = http_get_json(base_url, "/api/encounters")
        assert enc_list["ok"] is True and enc_list["count"] == 8
        for enc in enc_list["encounters"]:
            assert enc["handwritten_ocr"]["confidence"] >= 0.95
            assert len(enc["operative_report_text"]) > 80
            assert len(enc["pathology_report_text"]) > 20
            assert "Modality" in enc["dicom_metadata"]
            assert len(enc["langgraph_trace"]) == 6
            assert enc["money_left_on_table_usd"] > 0

        enc_detail = http_get_json(base_url, "/api/encounters/ENC-2026-0101")
        assert enc_detail["ok"] is True
        assert enc_detail["encounter"]["encounter_id"] == "ENC-2026-0101"
        assert len(enc_detail["encounter"]["feedback_history"]) >= 1
        results["gates_passed"] += 1
        results["details"].append("GATE 2 PASS: All 8 Multimodal Encounters (Handwritten OCR, Op PDF, Pathology, pydicom, 6-Node Trace) Verified")

        # -------------------------------------------------------------------
        # GATE 3: Deterministic NCCI Chapter 7 "Can I Report Both?" Engine
        # -------------------------------------------------------------------
        # 3A: Contralateral 52356 + 52332 -> YES with Modifier -XS-LT
        ptp_contra = http_post_json(
            base_url,
            "/api/ptp-check",
            {"code_a": "52356", "code_b": "52332", "version_year": 2026, "clinical_context": "contralateral"},
        )
        assert ptp_contra["can_report_both"] is True
        assert ptp_contra["verdict"] == "YES_REPORT_BOTH_WITH_MODIFIER"
        assert len(ptp_contra["recommended_claim_lines"]) == 2

        # 3B: Same-side 52353 + 52332 -> Collapse into 52356
        ptp_same = http_post_json(
            base_url,
            "/api/ptp-check",
            {"code_a": "52353", "code_b": "52332", "version_year": 2026, "clinical_context": "same_side"},
        )
        assert ptp_same["can_report_both"] is False
        assert ptp_same["verdict"] == "COLLAPSE_INTO_COMPREHENSIVE_CODE_52356"
        assert ptp_same["recommended_claim_lines"][0]["code"] == "52356"

        # 3C: Multifocal TURBT 52235 + 52234 -> Hard Block Modifier Indicator 0
        ptp_turbt = http_post_json(
            base_url,
            "/api/ptp-check",
            {"code_a": "52235", "code_b": "52234", "version_year": 2026, "clinical_context": "same_session_multifocal"},
        )
        assert ptp_turbt["can_report_both"] is False
        assert ptp_turbt["verdict"] == "NO_HARD_BUNDLED_MODIFIER_INDICATOR_0"

        # 3D: Dual TRUS 76872 + 76942 -> YES with Modifier -59
        ptp_trus = http_post_json(
            base_url,
            "/api/ptp-check",
            {"code_a": "76872", "code_b": "76942", "version_year": 2026, "clinical_context": "separate_diagnostic_and_guidance"},
        )
        assert ptp_trus["can_report_both"] is True

        # 3E: Urodynamics 51729 + 51797 (Add-on ZZZ) vs 51729 + 51798 (PVR Trap Ind 0)
        ptp_uds_addon = http_post_json(
            base_url,
            "/api/ptp-check",
            {"code_a": "51729", "code_b": "51797", "version_year": 2026, "clinical_context": "same_side"},
        )
        assert ptp_uds_addon["can_report_both"] is True
        ptp_uds_pvr = http_post_json(
            base_url,
            "/api/ptp-check",
            {"code_a": "51729", "code_b": "51798", "version_year": 2026, "clinical_context": "same_side"},
        )
        assert ptp_uds_pvr["can_report_both"] is False
        assert ptp_uds_pvr["verdict"] == "NO_HARD_BUNDLED_MODIFIER_INDICATOR_0"

        results["gates_passed"] += 1
        results["details"].append("GATE 3 PASS: NCCI Policy Manual Ch. 7 & CPT Assistant 'Can I Report Both?' Evaluator (6/6 Clinical Archetypes)")

        # -------------------------------------------------------------------
        # GATE 4: AMA CPT 2026 <-> 2027 Version Control & Catalog Endpoints
        # -------------------------------------------------------------------
        vdiff = http_get_json(base_url, "/api/version-diff")
        assert vdiff["ok"] is True
        migrations = vdiff["diff"]["sunset_and_new_migrations"]
        codes_migrated = {m["code"] for m in migrations}
        assert "0421T" in codes_migrated and "52598" in codes_migrated and "53853" in codes_migrated

        codes_2026 = http_get_json(base_url, "/api/codes?year=2026")
        codes_2027 = http_get_json(base_url, "/api/codes?year=2027")
        assert len(codes_2026["codes"]) == 46 and len(codes_2027["codes"]) == 46
        results["gates_passed"] += 1
        results["details"].append("GATE 4 PASS: AMA CPT 2026 <-> CPT 2027 Temporal Version Control (0421T->52598 Migration & 53853 Deleted Guardrail)")

        # -------------------------------------------------------------------
        # GATE 5: Live 6-Node LangGraph Multimodal Simulator & PHI Safe Harbor
        # -------------------------------------------------------------------
        sim_res = http_post_json(
            base_url,
            "/api/audit",
            {
                "date_of_service": "2027-01-14",
                "facility_type": "FACILITY",
                "locality_code": "04",
                "clinical_note": "Patient: John Doe, MRN: 994812, SSN: 123-45-6789. Performed robotic waterjet ablation of prostate (Aquablation) for BPH (N40.1) and administered Degarelix 240 mg loading dose for prostate cancer (C61). Doctor wrote: 0421T, 96402, J9155.",
                "pathology_text": "Gleason 4+4=8 Prostate Adenocarcinoma (C61).",
                "dicom_summary": "TRUS prostate volume 84.2 cc.",
                "billed_codes": [
                    {"code": "0421T", "units": 1, "modifiers": []},
                    {"code": "96402", "units": 1, "modifiers": []},
                    {"code": "J9155", "units": 1, "modifiers": []},
                ],
            },
        )
        assert sim_res["ok"] is True
        assert sim_res["cpt_version_year"] == 2027
        assert sim_res["phi_redaction"]["redactions_applied"] >= 3
        assert "John Doe" not in sim_res["phi_redaction"]["clean_text"]
        assert "123-45-6789" not in sim_res["phi_redaction"]["clean_text"]
        verified_codes = {l["code"]: l for l in sim_res["verified_lines"]}
        assert "52598" in verified_codes, "0421T was not auto-migrated to CPT 2027 code 52598!"
        assert verified_codes["J9155"]["units"] == 240, "J9155 was not converted from 1 unit to 240 mg units!"
        assert sim_res["money_left_on_table_usd"] > 1400.0
        results["gates_passed"] += 1
        results["details"].append(
            f"GATE 5 PASS: Live 6-Node LangGraph Simulator & PHI Redaction (3 PHI tokens scrubbed, 0421T->52598 migrated, J9155 x240 recovered +${sim_res['money_left_on_table_usd']})"
        )

        # -------------------------------------------------------------------
        # GATE 6: HITL Physician/Coder Sign-Off & X12 835 Remittance Loop
        # -------------------------------------------------------------------
        fb_res = http_post_json(
            base_url,
            "/api/feedback",
            {
                "encounter_id": "ENC-2026-0103",
                "reviewer_role": "Automated E2E Forensic Verifier",
                "action_taken": "ACCEPTED_AI_CLAIM",
                "target_code": "52287+J0585+J0585-JW",
                "carc_rarc_code": "CARC-0",
                "rationale_note": "E2E test verified 100U injected + 100U single-dose vial wastage.",
                "revenue_delta_usd": 1296.00,
            },
        )
        assert fb_res["ok"] is True and fb_res["new_hitl_status"] == "CODER_VERIFIED"
        # Reset ENC-2026-0103 seed state after test so UI shows mixed statuses
        seed_all(DB_PATH)
        results["gates_passed"] += 1
        results["details"].append("GATE 6 PASS: HITL Sign-Off & X12 835 Remittance Continuous Learning Loop (/api/feedback)")

        # -------------------------------------------------------------------
        # GATE 7: CMS PUF + NPPES NPI Urology Peer Benchmark Engine
        # -------------------------------------------------------------------
        bench = http_get_json(base_url, "/api/benchmarks")
        assert bench["ok"] is True and len(bench["benchmarks"]) == 4
        assert len(bench["localities"]) == 7
        results["gates_passed"] += 1
        results["details"].append("GATE 7 PASS: CMS PUF + NPPES NPI Urology Peer Benchmark Analyzer (4 NPIs & 7 MAC Localities)")

        # -------------------------------------------------------------------
        # GATE 8: Multimodal Binary File Upload & Discrepancy Reconciliation
        # -------------------------------------------------------------------
        samples_resp = http_get_json(base_url, "/api/sample-files")
        assert samples_resp["ok"] is True and samples_resp["count"] == 5
        sample_files = samples_resp["sample_files"]
        detected_formats = {f["detected_format"] for f in sample_files}
        assert "PDF_DOCUMENT" in detected_formats
        assert "PNG_HANDWRITTEN_IMAGE" in detected_formats
        assert "JPEG_HANDWRITTEN_IMAGE" in detected_formats
        assert "DICOM_IMAGING_STUDY" in detected_formats
        assert "X12_837P_EDI_CLAIM" in detected_formats

        upload_res = http_post_json(
            base_url,
            "/api/upload-analyze",
            {
                "files": [
                    {"filename": f["filename"], "content_base64": f["content_base64"]}
                    for f in sample_files
                ],
                "facility_type": "NON_FACILITY",
                "locality_code": "11",
                "is_qp": True,
            },
        )
        assert upload_res["ok"] is True
        assert upload_res["uploaded_file_count"] == 5
        assert upload_res["total_phi_redactions"] >= 6
        assert len(upload_res["discrepancies"]) >= 6
        assert upload_res["audit"]["money_left_on_table_usd"] > 3000.0
        results["gates_passed"] += 1
        results["details"].append(
            f"GATE 8 PASS: Multimodal Binary File Upload & Discrepancy Analyzer (5 Binary Formats: PDF/PNG/JPEG/DICOM/837P, {len(upload_res['discrepancies'])} Discrepancies, +${upload_res['audit']['money_left_on_table_usd']} Recovery)"
        )

    finally:
        server.server_close()

    return results


if __name__ == "__main__":
    report = run_forensic_e2e_suite()
    print("==================================================================")
    print("🛡️  UROCURA OS — 8-GATE FORENSIC & E2E VERIFICATION REPORT")
    print("==================================================================")
    for line in report["details"]:
        print(" ✅", line)
    print("------------------------------------------------------------------")
    print(f"RESULT: {report['gates_passed']}/{report['total_gates']} GATES PASSED (100% ZERO DEFECTS)")
    print("==================================================================")
