#!/usr/bin/env python3
"""
generate_sample_uploads.py — Generates authentic binary clinical sample files in `sample_uploads/`
for end-to-end multimodal file upload testing (.pdf, .png, .jpg, .dcm, .837p.txt).

Files generated:
  1. sample_uploads/operative_and_pathology_report_turbt.pdf  (Valid %PDF-1.4 document)
  2. sample_uploads/handwritten_superbill_botox_52287.png     (Valid PNG image w/ tEXt OCR layer & rendered note)
  3. sample_uploads/handwritten_note_contralateral_urs.jpg    (Valid JPEG image w/ COM/EXIF OCR layer)
  4. sample_uploads/ct_urogram_stone_study.dcm                (Valid DICOM Part 10 binary file w/ DICM preamble)
  5. sample_uploads/billing_dept_scrubbed_claim.837p.txt      (Valid ANSI X12 837P EDI claim file w/ SV1*HC segments)
"""

import os
import struct
import zlib

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_uploads")


def build_valid_pdf(filepath: str) -> None:
    """Creates a standards-compliant %PDF-1.4 file containing Operative & Surgical Pathology text."""
    lines = [
        "UROCURA CLINICAL & PATHOLOGY MULTIMODAL RECORD",
        "Patient: Michael Sterling | MRN: 774920 | SSN: 441-29-8810 | DOS: 2027-01-14",
        "--------------------------------------------------------------------------------",
        "1. OPERATIVE REPORT (PDF - IBM Docling Structured Section):",
        "PREOPERATIVE & POSTOPERATIVE DIAGNOSIS:",
        "  - Obstructive Benign Prostatic Hyperplasia, 84.2 cc gland (ICD-10-CM: N40.1)",
        "  - Adenocarcinoma of Prostate, Gleason 4+4=8, Grade Group 4 (ICD-10-CM: C61)",
        "  - Multifocal Papillary Bladder Tumor: 4.2 cm Right Lateral Wall + 1.4 cm Trigone (ICD-10-CM: C67.2)",
        "PROCEDURES PERFORMED:",
        "  A) Transurethral robotic waterjet ablation of prostate (Aquablation) w/ TRUS guidance (Doctor wrote 0421T; CPT 2027 = 52598).",
        "  B) Bipolar TURBT resection of 4.2 cm right lateral bladder wall tumor and 1.4 cm trigone tumor to muscularis propria (52235).",
        "  C) Subcutaneous hormonal antineoplastic administration (96402) of Degarelix (Firmagon, J9155) 240 mg starter loading dose.",
        "--------------------------------------------------------------------------------",
        "2. SURGICAL PATHOLOGY REPORT (#SP-27-10492):",
        "  - Specimen 1 (Right Lateral Bladder Wall, 4.2 x 3.1 cm): High-grade papillary urothelial carcinoma pT1 (ICD-10-CM: C67.2).",
        "  - Specimen 2 (Prostate Core Biopsy): Prostatic Adenocarcinoma Gleason 4+4=8 (ICD-10-CM: C61).",
    ]

    # Build PDF content stream with BT /F1 10 Tf ... Tj ET
    stream_cmds = ["BT", "/F1 10 Tf", "36 740 Td", "14 TL"]
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_cmds.append(f"({escaped}) '")
    stream_cmds.append("ET")
    stream_bytes = "\n".join(stream_cmds).encode("latin-1")

    objs = []
    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objs.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
    )
    objs.append(
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )
    objs.append(
        f"5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1")
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for o in objs:
        offsets.append(len(out))
        out.extend(o)

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objs) + 1}\n".encode("latin-1"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets:
        out.extend(f"{off:010d} 00000 n \n".encode("latin-1"))
    out.extend(
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "latin-1"
        )
    )

    with open(filepath, "wb") as f:
        f.write(out)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def build_valid_png(filepath: str) -> None:
    """
    Creates a valid 360x140 RGB PNG representing a warm yellow handwritten physician superbill note
    with ruled lines and embedded PNG tEXt OCR transcription chunk.
    """
    width, height = 360, 140
    raw_rows = bytearray()
    for y in range(height):
        raw_rows.append(0)  # Filter type 0
        for x in range(width):
            # Warm notepad background (#fffdf2) with left margin line and horizontal rules
            r, g, b = 255, 253, 242
            if x in (34, 35):
                r, g, b = 244, 114, 182  # Pink margin line
            elif y % 24 == 22:
                r, g, b = 191, 219, 254  # Blue ruled line
            # Simulated dark-blue fountain pen handwriting strokes across lines
            elif 45 <= x <= 325 and (y in (36, 37, 60, 61, 84, 85, 108, 109)) and ((x * 7 + y * 13) % 11 > 3):
                r, g, b = 30, 58, 138
            raw_rows.extend((r, g, b))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ocr_text = (
        "Handwritten Physician Superbill Note (Vision OCR Confidence 99.1%): "
        "Patient: Sarah Jenkins, MRN: 883104. DOS: 2026-10-16. "
        "Refractory Overactive Bladder (N32.81). Performed in-office cystourethroscopy with intradetrusor "
        "Botox (onabotulinumtoxinA, J0585) chemodenervation (CPT 52287): 100 Units injected across 20 detrusor sites. "
        "Opened 200U single-dose vial (Allergan Lot #B88412), 100U discarded per sterile protocol (J0585-JW x100)."
    )
    text_chunk_data = b"ClinicalOCR\x00" + ocr_text.encode("utf-8")
    idat_data = zlib.compress(bytes(raw_rows), 9)

    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", text_chunk_data)
        + _png_chunk(b"IDAT", idat_data)
        + _png_chunk(b"IEND", b"")
    )
    with open(filepath, "wb") as f:
        f.write(png_bytes)


def build_valid_jpeg(filepath: str) -> None:
    """
    Creates a valid JPEG file (\xFF\xD8\xFF) containing an embedded COM (Comment / OCR layer) segment
    with the physician's handwritten contralateral ureteroscopy post-op note.
    """
    ocr_comment = (
        "Handwritten Post-Op Margin Note (JPEG Vision OCR Confidence 98.7%): "
        "Patient: David Vance, SSN: 552-19-4021. DOS: 2026-10-14. "
        "1) Right flexible ureteroscopy with Holmium laser lithotripsy of 11 mm right proximal ureteral stone (N20.1) "
        "and insertion of right 6Frx26cm indwelling double-J ureteral stent (52356-RT). "
        "2) Contralateral LEFT cystoscopic insertion of left 6Frx26cm double-J ureteral stent for Grade 3 left hydronephrosis "
        "secondary to 8 mm left UPJ stone (N13.2) (52332-XS-LT). Diagnostic TRUS prostate biopsy 55700 + 76872 (66.8cc) + 76942."
    ).encode("utf-8")

    com_segment = b"\xff\xfe" + struct.pack(">H", len(ocr_comment) + 2) + ocr_comment

    # Minimal valid 1x1 baseline JPEG stream + COM OCR segment
    minimal_jpeg_body = bytes.fromhex(
        "ffe000104a46494600010101006000600000"
        "ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432"
        "ffc0000b080001000101011100"
        "ffc4001f0000010501010101010100000000000000000102030405060708090a0b"
        "ffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9fa"
        "ffda0008010100003f00fbfdffd9"
    )
    jpeg_bytes = b"\xff\xd8" + com_segment + minimal_jpeg_body
    with open(filepath, "wb") as f:
        f.write(jpeg_bytes)


def _dicom_elem_ExplicitVR(group: int, elem: int, vr: bytes, val_bytes: bytes) -> bytes:
    if len(val_bytes) % 2 == 1:
        val_bytes += b" "
    return struct.pack("<HH2sH", group, elem, vr, len(val_bytes)) + val_bytes


def build_valid_dicom(filepath: str) -> None:
    """
    Creates a valid DICOM Part 10 binary file (.dcm) with 128-byte preamble + 'DICM' magic header
    and Explicit VR Little Endian clinical tags.
    """
    preamble = b"\x00" * 128 + b"DICM"
    tags = bytearray()
    tags.extend(_dicom_elem_ExplicitVR(0x0008, 0x0060, b"CS", b"CT"))  # Modality
    tags.extend(
        _dicom_elem_ExplicitVR(
            0x0008,
            0x1030,
            b"LO",
            b"CT UROGRAM & AQUABEAM TRUS CONTOUR (Prostate 84.2cc, R Stone 11.2mm, L Hydro G3, Bladder Mass 4.2cm)",
        )
    )
    tags.extend(_dicom_elem_ExplicitVR(0x0018, 0x0050, b"DS", b"1.25"))  # SliceThickness
    tags.extend(
        _dicom_elem_ExplicitVR(
            0x0020, 0x4000, b"LT", b"pydicom Extracted: RightStone=11.2mm (1180 HU); LeftUPJStone=8.4mm (Grade 3 Hydronephrosis); RightLateralBladderTumor=4.24cm; ProstateEllipsoidVolume=84.2cc"
        )
    )
    with open(filepath, "wb") as f:
        f.write(preamble + bytes(tags))


def build_valid_837p(filepath: str) -> None:
    """
    Creates an ANSI X12 837P (005010X222A1) EDI Professional Claim file representing what the
    hospital/clinic Billing Department actually coded and submitted to the clearinghouse.
    """
    edi_segments = [
        "ISA*00*          *00*          *ZZ*UROCLINIC837   *ZZ*FIRSTCOASTMAC  *270114*1620*^*00501*000000912*0*P*:~",
        "GS*HC*UROCLINIC837*FIRSTCOASTMAC*20270114*1620*912*X*005010X222A1~",
        "ST*837*0001*005010X222A1~",
        "BHT*0019*00*CLM2027011401*20270114*1620*CH~",
        "NM1*85*2*BISCAYNE BAY UROLOGY CENTER*****XX*1730194827~",
        "CLM*ENC-UPLOAD-01*1131.50***22:B:1*Y*A*Y*Y~",
        "DTP*472*D8*20270114~",
        "HI*ABK:N401*ABF:D494~",
        "LX*1~",
        "SV1*HC:0421T*815.20*UN*1***1~",
        "LX*2~",
        "SV1*HC:52234*274.18*UN*1***2~",
        "LX*3~",
        "SV1*HC:96402*36.10*UN*1***1~",
        "LX*4~",
        "SV1*HC:J9155*6.07*UN*1***1~",
        "SE*16*0001~",
        "GE*1*912~",
        "IEA*1*000000912~",
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(edi_segments) + "\n")


def generate_all_samples() -> dict:
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    files = {
        "pdf": os.path.join(SAMPLE_DIR, "operative_and_pathology_report_turbt.pdf"),
        "png": os.path.join(SAMPLE_DIR, "handwritten_superbill_botox_52287.png"),
        "jpg": os.path.join(SAMPLE_DIR, "handwritten_note_contralateral_urs.jpg"),
        "dcm": os.path.join(SAMPLE_DIR, "ct_urogram_stone_study.dcm"),
        "edi_837p": os.path.join(SAMPLE_DIR, "billing_dept_scrubbed_claim.837p.txt"),
    }
    build_valid_pdf(files["pdf"])
    build_valid_png(files["png"])
    build_valid_jpeg(files["jpg"])
    build_valid_dicom(files["dcm"])
    build_valid_837p(files["edi_837p"])
    return {k: {"path": v, "bytes": os.path.getsize(v)} for k, v in files.items()}


if __name__ == "__main__":
    summary = generate_all_samples()
    print("✅ Generated Authentic Multimodal Sample Uploads in sample_uploads/:")
    for k, info in summary.items():
        print(f"  - [{k.upper()}] {info['path']} ({info['bytes']} bytes)")
