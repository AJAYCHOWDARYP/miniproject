"""
Tests for OCR extraction & Lab Parsing.
"""
from app.services.ocr_service import parse_lab_text_to_structured_results


def test_parse_standard_lab_text():
    sample_text = """
    QUEST DIAGNOSTICS LABORATORY REPORT
    Patient: Alex Morgan | Date: 2026-06-12
    
    Test Name               Result      Units       Reference Interval
    ------------------------------------------------------------------
    HbA1c                   5.8         %           4.0 - 5.6
    Fasting Blood Glucose   102.0       mg/dL       70 - 99
    Total Cholesterol       195.0       mg/dL       125 - 200
    LDL Cholesterol         118.0       mg/dL       < 100
    HDL Cholesterol         51.0        mg/dL       40 - 60
    Serum Creatinine        0.95        mg/dL       0.6 - 1.2
    Hemoglobin              14.2        g/dL        12.0 - 17.0
    """
    results = parse_lab_text_to_structured_results(sample_text)
    assert len(results) >= 5

    hba1c_item = next((r for r in results if r["canonical_code"] == "HBA1C"), None)
    assert hba1c_item is not None
    assert hba1c_item["numeric_value"] == 5.8
    assert hba1c_item["status_flag"] == "above_range"

    chol_item = next((r for r in results if r["canonical_code"] == "CHOL_TOTAL"), None)
    assert chol_item is not None
    assert chol_item["numeric_value"] == 195.0
    assert chol_item["status_flag"] == "within_range"
