"""
Secure Tokenized Doctor Sharing Service.
"""

from typing import Dict, List, Any
from datetime import datetime, timezone


def generate_doctor_clinical_summary(
    user_name: str,
    age: float,
    sex: str,
    active_conditions: List[str],
    allergies: List[str],
    medications: List[Dict[str, Any]],
    adherence_stats: Dict[str, Any],
    recent_lab_results: List[Dict[str, Any]],
    recent_symptoms: List[Dict[str, Any]],
    patient_notes: str = ""
) -> Dict[str, Any]:
    """Format clinical summary optimized for physician review."""
    return {
        "report_title": "Patient Health & Treatment Summary for Doctor Review",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "patient_demographics": {
            "name": user_name,
            "age": age,
            "sex": sex
        },
        "active_conditions": active_conditions,
        "allergies": allergies,
        "current_medications": [
            {
                "medicine": m.get("brand_name"),
                "strength": m.get("strength"),
                "frequency": m.get("frequency_type"),
                "food_relation": m.get("food_relation"),
                "prescriber": m.get("prescribing_doctor")
            }
            for m in medications
        ],
        "medication_adherence": {
            "adherence_rate": f"{adherence_stats.get('adherence_pct', 100)}%",
            "grade": adherence_stats.get("adherence_grade")
        },
        "recent_lab_findings": [
            {
                "test": r.get("biomarker_name"),
                "value": f"{r.get('numeric_value')} {r.get('unit')}".strip(),
                "status": r.get("status_flag"),
                "date": str(r.get("recorded_date"))
            }
            for r in recent_lab_results
        ],
        "recent_symptoms_logged": recent_symptoms,
        "patient_notes_and_questions": patient_notes or "Patient has not attached additional notes.",
        "disclaimer": "This summary is organized by the patient using the Healthcare AI Assistant to support consultation."
    }
