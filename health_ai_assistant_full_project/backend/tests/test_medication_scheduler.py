"""
Tests for Medication Scheduling & Adherence.
"""
from app.services.medical_extractor import parse_prescription_text
from app.services.scheduler_service import calculate_adherence_statistics


def test_parse_prescription_text():
    rx_text = """
    Rx:
    1. Tab. Metformin 500 mg - twice daily after food for 30 days
    2. Tab. Telmisartan 40 mg - once daily before food for 90 days
    """
    parsed = parse_prescription_text(rx_text, "Dr. Chen")
    assert parsed["prescribing_doctor"] == "Dr. Chen"
    meds = parsed["medications"]
    assert len(meds) == 2
    assert "Metformin" in meds[0]["brand_name"]
    assert meds[0]["strength"] == "500 mg"


def test_adherence_calculation():
    logs = [
        {"status": "TAKEN"},
        {"status": "TAKEN"},
        {"status": "TAKEN"},
        {"status": "SKIPPED"},
        {"status": "TAKEN"}
    ]
    stats = calculate_adherence_statistics(logs)
    assert stats["total_scheduled"] == 5
    assert stats["taken_count"] == 4
    assert stats["skipped_count"] == 1
    assert stats["adherence_pct"] == 80.0
