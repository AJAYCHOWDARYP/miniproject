"""
Prescription Digitizer and Entity Extraction Service.
"""

import re
from typing import Dict, List, Any
from datetime import date, timedelta


def parse_prescription_text(text: str, doctor_name: str = "Dr. Healthcare Provider") -> Dict[str, Any]:
    """Extract structured medication objects from raw prescription text."""
    medications = []
    lines = text.splitlines()

    freq_map = {
        "once": "once_daily",
        "1 time": "once_daily",
        "twice": "twice_daily",
        "2 times": "twice_daily",
        "bid": "twice_daily",
        "thrice": "thrice_daily",
        "3 times": "thrice_daily",
        "tid": "thrice_daily",
        "as needed": "as_needed",
        "prn": "as_needed",
        "daily": "once_daily"
    }

    food_map = {
        "after food": "after_food",
        "post meal": "after_food",
        "after meal": "after_food",
        "before food": "before_food",
        "pre meal": "before_food",
        "before meal": "before_food",
        "empty stomach": "empty_stomach",
        "with food": "with_food"
    }

    for line in lines:
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 3:
            continue
        
        strength_match = re.search(r"([0-9]+\s*(?:mg|mcg|g|ml|IU))", line_clean, re.IGNORECASE)
        if strength_match:
            strength = strength_match.group(1)
            brand_part = line_clean[:strength_match.start()].strip()
            brand_part = re.sub(r"^[0-9\.\-\*\)\s]+", "", brand_part).replace("Tab.", "").replace("Cap.", "").strip()
            if not brand_part:
                brand_part = "Prescribed Medication"

            freq = "twice_daily"
            for k, v in freq_map.items():
                if k in line_clean.lower():
                    freq = v
                    break

            food = "after_food"
            for k, v in food_map.items():
                if k in line_clean.lower():
                    food = v
                    break

            duration_days = 30
            dur_match = re.search(r"([0-9]+)\s*(?:days|day|weeks|months)", line_clean, re.IGNORECASE)
            if dur_match:
                try:
                    num = int(dur_match.group(1))
                    if "week" in line_clean.lower():
                        duration_days = num * 7
                    elif "month" in line_clean.lower():
                        duration_days = num * 30
                    else:
                        duration_days = num
                except ValueError:
                    pass

            schedules = []
            if freq == "once_daily":
                schedules.append({"scheduled_time_str": "08:30", "dose_quantity": "1 tablet", "reminder_enabled": True})
            elif freq == "twice_daily":
                schedules.append({"scheduled_time_str": "08:30", "dose_quantity": "1 tablet", "reminder_enabled": True})
                schedules.append({"scheduled_time_str": "20:30", "dose_quantity": "1 tablet", "reminder_enabled": True})
            elif freq == "thrice_daily":
                schedules.append({"scheduled_time_str": "08:30", "dose_quantity": "1 tablet", "reminder_enabled": True})
                schedules.append({"scheduled_time_str": "14:00", "dose_quantity": "1 tablet", "reminder_enabled": True})
                schedules.append({"scheduled_time_str": "20:30", "dose_quantity": "1 tablet", "reminder_enabled": True})
            else:
                schedules.append({"scheduled_time_str": "09:00", "dose_quantity": "1 dose", "reminder_enabled": True})

            medications.append({
                "brand_name": brand_part,
                "generic_name": brand_part,
                "strength": strength,
                "dosage_form": "Tablet" if "tab" in line_clean.lower() else "Capsule" if "cap" in line_clean.lower() else "Dose",
                "frequency_type": freq,
                "route": "Oral",
                "food_relation": food,
                "start_date": date.today(),
                "end_date": date.today() + timedelta(days=duration_days),
                "duration_days": duration_days,
                "prescribing_doctor": doctor_name,
                "special_instructions": "Take strictly as prescribed by your doctor.",
                "schedules": schedules
            })

    return {
        "prescribing_doctor": doctor_name,
        "prescription_date": date.today(),
        "notes": "Parsed from medical prescription.",
        "medications": medications
    }
