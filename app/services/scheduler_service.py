"""
Medication Reminder Scheduling and Adherence Engine.
"""

from typing import Dict, List, Any


def get_safe_missed_dose_guidance(medication_name: str) -> Dict[str, Any]:
    """Safety guidance on missed medication doses without double-dosing."""
    return {
        "title": f"Missed Dose Safety Guide: {medication_name}",
        "guidance": (
            "1. Take the missed dose as soon as you remember.\n"
            "2. If it is almost time for your next regular dose, skip the missed dose and resume your normal schedule.\n"
            "3. NEVER take two doses or a double dose to make up for a missed one.\n"
            "4. If you have specific questions, contact your prescribing doctor or pharmacist."
        ),
        "warning": "Do not alter your medication schedule without consulting your healthcare provider."
    }


def calculate_adherence_statistics(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate daily and weekly adherence percentages."""
    if not logs:
        return {
            "total_scheduled": 0,
            "taken_count": 0,
            "skipped_count": 0,
            "snoozed_count": 0,
            "adherence_pct": 100.0,
            "adherence_grade": "Excellent (No missed doses logged)"
        }

    total = len(logs)
    taken = sum(1 for log in logs if log.get("status") == "TAKEN")
    skipped = sum(1 for log in logs if log.get("status") == "SKIPPED")
    snoozed = sum(1 for log in logs if log.get("status") == "SNOOZED")

    adherence_pct = round((taken / total) * 100.0, 1) if total > 0 else 100.0

    if adherence_pct >= 90.0:
        grade = "Excellent adherence"
    elif adherence_pct >= 75.0:
        grade = "Good adherence"
    else:
        grade = "Needs attention — discuss routines with your caregiver or doctor"

    return {
        "total_scheduled": total,
        "taken_count": taken,
        "skipped_count": skipped,
        "snoozed_count": snoozed,
        "adherence_pct": adherence_pct,
        "adherence_grade": grade
    }
