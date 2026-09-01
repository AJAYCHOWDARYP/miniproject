"""
OCR and Medical Document Parsing Service with Plain-Language Descriptions, Confidence Scoring, and Demographics Extraction.
"""
import io
import re
from typing import Dict, List, Any, Optional
from pypdf import PdfReader

CANONICAL_BIOMARKERS = {
    # Glycemic & Diabetes (Blood Sugar)
    "HBA1C": {
        "name": "HbA1c (Glycated Hemoglobin)",
        "friendly_name": "3-Month Blood Sugar (HbA1c)",
        "category": "Blood Sugar (Energy & Metabolism)",
        "unit": "%",
        "ref_min": 4.0,
        "ref_max": 5.6,
        "critical_high": 9.0,
        "description": "Shows your average blood sugar levels over the past 2 to 3 months."
    },
    "GLUCOSE_FASTING": {
        "name": "Fasting Blood Glucose",
        "friendly_name": "Fasting Blood Sugar",
        "category": "Blood Sugar (Energy & Metabolism)",
        "unit": "mg/dL",
        "ref_min": 70.0,
        "ref_max": 99.0,
        "critical_high": 250.0,
        "critical_low": 50.0,
        "description": "Checks your blood sugar level in the morning before eating or drinking anything."
    },
    "GLUCOSE_PP": {
        "name": "Post-Prandial Blood Glucose",
        "friendly_name": "After-Meal Blood Sugar",
        "category": "Blood Sugar (Energy & Metabolism)",
        "unit": "mg/dL",
        "ref_min": 70.0,
        "ref_max": 140.0,
        "critical_high": 300.0,
        "description": "Measures how effectively your body processes sugar 2 hours after a meal."
    },

    # Lipid Profile (Heart & Blood Fats)
    "CHOL_TOTAL": {
        "name": "Total Cholesterol",
        "friendly_name": "Total Cholesterol",
        "category": "Heart Health & Blood Fats",
        "unit": "mg/dL",
        "ref_min": 125.0,
        "ref_max": 200.0,
        "critical_high": 300.0,
        "description": "Total amount of all cholesterol fats traveling through your bloodstream."
    },
    "LDL": {
        "name": "LDL Cholesterol",
        "friendly_name": "'Bad' Cholesterol (LDL)",
        "category": "Heart Health & Blood Fats",
        "unit": "mg/dL",
        "ref_min": 0.0,
        "ref_max": 100.0,
        "critical_high": 190.0,
        "description": "Known as 'bad cholesterol' because high amounts can slowly build up along artery walls."
    },
    "HDL": {
        "name": "HDL Cholesterol",
        "friendly_name": "'Good' Cholesterol (HDL)",
        "category": "Heart Health & Blood Fats",
        "unit": "mg/dL",
        "ref_min": 40.0,
        "ref_max": 60.0,
        "description": "Known as 'good cholesterol' because it carries extra fat back to your liver to be cleared."
    },
    "TRIGLYCERIDES": {
        "name": "Triglycerides",
        "friendly_name": "Triglycerides",
        "category": "Heart Health & Blood Fats",
        "unit": "mg/dL",
        "ref_min": 0.0,
        "ref_max": 150.0,
        "critical_high": 500.0,
        "description": "A type of fat in your blood that comes from unused calories, sugars, and carbohydrates."
    },
    "VLDL": {
        "name": "VLDL Cholesterol",
        "friendly_name": "VLDL Blood Fat",
        "category": "Heart Health & Blood Fats",
        "unit": "mg/dL",
        "ref_min": 2.0,
        "ref_max": 30.0,
        "description": "Particles that carry triglycerides from your liver to tissues throughout your body."
    },

    # Complete Blood Count (CBC - Blood Health & Oxygen Delivery)
    "HEMOGLOBIN": {
        "name": "Hemoglobin (Hb)",
        "friendly_name": "Hemoglobin (Oxygen Carriers)",
        "category": "Blood Health & Oxygen Delivery",
        "unit": "g/dL",
        "ref_min": 12.0,
        "ref_max": 17.0,
        "critical_low": 7.0,
        "description": "The protein inside your red blood cells that carries fresh oxygen from your lungs to your whole body."
    },
    "WBC": {
        "name": "Total Leukocyte Count (WBC)",
        "friendly_name": "White Blood Cells (Immunity)",
        "category": "Immune Defense & White Blood Cells",
        "unit": "/cumm",
        "ref_min": 4000.0,
        "ref_max": 11000.0,
        "critical_high": 30000.0,
        "critical_low": 2000.0,
        "description": "Your body's primary immune defenders that help fight off bacteria, viruses, and infections."
    },
    "PLATELETS": {
        "name": "Platelet Count",
        "friendly_name": "Platelets (Clotting Cells)",
        "category": "Blood Clotting & Healing",
        "unit": "lakh/cumm",
        "ref_min": 1.5,
        "ref_max": 4.5,
        "critical_low": 0.5,
        "description": "Tiny cell fragments that bundle together to stop bleeding when you have a scratch or wound."
    },
    "RBC": {
        "name": "Red Blood Cell (RBC) Count",
        "friendly_name": "Red Blood Cell Count",
        "category": "Blood Health & Oxygen Delivery",
        "unit": "million/cumm",
        "ref_min": 4.2,
        "ref_max": 5.8,
        "description": "Total count of red blood cells transporting oxygen and nutrients throughout your tissues."
    },
    "HEMATOCRIT": {
        "name": "Hematocrit (PCV)",
        "friendly_name": "Hematocrit %",
        "category": "Blood Health & Oxygen Delivery",
        "unit": "%",
        "ref_min": 36.0,
        "ref_max": 50.0,
        "description": "The percentage of your overall blood volume that is composed of red blood cells."
    },

    # Kidney Health & Filtration
    "CREATININE": {
        "name": "Serum Creatinine",
        "friendly_name": "Serum Creatinine (Kidney Check)",
        "category": "Kidney Health & Filtration",
        "unit": "mg/dL",
        "ref_min": 0.6,
        "ref_max": 1.2,
        "critical_high": 4.0,
        "description": "A natural muscle waste product that healthy kidneys constantly filter and remove through urine."
    },
    "BUN": {
        "name": "Blood Urea Nitrogen (BUN)",
        "friendly_name": "BUN (Urea Nitrogen)",
        "category": "Kidney Health & Filtration",
        "unit": "mg/dL",
        "ref_min": 7.0,
        "ref_max": 20.0,
        "description": "Checks the amount of urea nitrogen waste in your blood from the breakdown of proteins."
    },
    "URIC_ACID": {
        "name": "Serum Uric Acid",
        "friendly_name": "Uric Acid",
        "category": "Joint & Kidney Health",
        "unit": "mg/dL",
        "ref_min": 3.5,
        "ref_max": 7.2,
        "description": "A byproduct of normal digestion; high levels can form crystals in joints or kidneys."
    },
    "EGFR": {
        "name": "Estimated GFR (eGFR)",
        "friendly_name": "Kidney Filtration Speed (eGFR)",
        "category": "Kidney Health & Filtration",
        "unit": "mL/min/1.73m2",
        "ref_min": 90.0,
        "ref_max": 120.0,
        "critical_low": 30.0,
        "description": "Calculates how many milliliters of blood your kidneys are successfully filtering every minute."
    },

    # Liver Function
    "SGOT_AST": {
        "name": "SGOT / AST (Aspartate Aminotransferase)",
        "friendly_name": "AST Liver Enzyme",
        "category": "Liver Health & Digestion",
        "unit": "U/L",
        "ref_min": 10.0,
        "ref_max": 40.0,
        "description": "An enzyme found in liver and heart cells; increases when cells are irritated or recovering."
    },
    "SGPT_ALT": {
        "name": "SGPT / ALT (Alanine Aminotransferase)",
        "friendly_name": "ALT Liver Enzyme",
        "category": "Liver Health & Digestion",
        "unit": "U/L",
        "ref_min": 7.0,
        "ref_max": 56.0,
        "description": "The most specific indicator for liver health; healthy liver cells keep this number low."
    },
    "BILIRUBIN_TOTAL": {
        "name": "Total Bilirubin",
        "friendly_name": "Total Bilirubin",
        "category": "Liver Health & Digestion",
        "unit": "mg/dL",
        "ref_min": 0.2,
        "ref_max": 1.2,
        "critical_high": 3.0,
        "description": "A golden-yellow pigment formed when your body recycles old red blood cells."
    },
    "ALKALINE_PHOS": {
        "name": "Alkaline Phosphatase (ALP)",
        "friendly_name": "Alkaline Phosphatase (ALP)",
        "category": "Liver & Bone Health",
        "unit": "U/L",
        "ref_min": 44.0,
        "ref_max": 147.0,
        "description": "An enzyme related to bile flow through your liver ducts and normal bone renewal."
    },

    # Thyroid Function
    "TSH": {
        "name": "Thyroid Stimulating Hormone (TSH)",
        "friendly_name": "Thyroid Control Hormone (TSH)",
        "category": "Thyroid & Energy Level",
        "unit": "uIU/mL",
        "ref_min": 0.4,
        "ref_max": 4.5,
        "description": "The master hormone that tells your thyroid gland how fast or slow your metabolism should run."
    },
    "FREE_T3": {
        "name": "Free T3",
        "friendly_name": "Active Thyroid (Free T3)",
        "category": "Thyroid & Energy Level",
        "unit": "pg/mL",
        "ref_min": 2.0,
        "ref_max": 4.4,
        "description": "The active thyroid hormone that directly fuels energy, heart rate, and body temperature."
    },
    "FREE_T4": {
        "name": "Free T4",
        "friendly_name": "Thyroid Hormone (Free T4)",
        "category": "Thyroid & Energy Level",
        "unit": "ng/dL",
        "ref_min": 0.8,
        "ref_max": 1.8,
        "description": "The main storage hormone released by the thyroid that converts into active T3 as needed."
    },

    # Vitamins & Essential Minerals
    "VITAMIN_D": {
        "name": "Vitamin D (25-Hydroxy)",
        "friendly_name": "Vitamin D (Bone & Immunity)",
        "category": "Vitamins & Minerals (Vitality)",
        "unit": "ng/mL",
        "ref_min": 30.0,
        "ref_max": 100.0,
        "critical_low": 10.0,
        "description": "Essential for absorbing calcium, keeping bones strong, and supporting your immune defenses."
    },
    "VITAMIN_B12": {
        "name": "Vitamin B12 (Cobalamin)",
        "friendly_name": "Vitamin B12 (Energy & Nerves)",
        "category": "Vitamins & Minerals (Vitality)",
        "unit": "pg/mL",
        "ref_min": 200.0,
        "ref_max": 900.0,
        "description": "Essential for daily physical energy, clear thinking, and protecting your nervous system."
    },
    "CALCIUM": {
        "name": "Serum Calcium",
        "friendly_name": "Serum Calcium (Bone Mineral)",
        "category": "Vitamins & Minerals (Vitality)",
        "unit": "mg/dL",
        "ref_min": 8.5,
        "ref_max": 10.5,
        "critical_low": 6.5,
        "critical_high": 13.0,
        "description": "The foundational mineral that keeps teeth and bones dense, and enables muscles to contract."
    },
    "SERUM_IRON": {
        "name": "Serum Iron",
        "friendly_name": "Serum Iron (Energy Mineral)",
        "category": "Vitamins & Minerals (Vitality)",
        "unit": "ug/dL",
        "ref_min": 60.0,
        "ref_max": 170.0,
        "description": "The mineral your bone marrow needs every single day to build fresh red blood cells."
    }
}



def get_personal_trainer_coaching(code: str, status: str, val: float, unit: str) -> Dict[str, str]:
    """
    Generates empowering, everyday personal trainer coaching guidance and self-care options.
    """
    c = code.upper()
    if c in ["HBA1C", "GLUCOSE_FASTING", "GLUCOSE_PP"]:
        if status in ["above_range", "critical"]:
            return {
                "care_level": "Needs Extra Care (Trainer Focus)",
                "trainer_action": "Enjoy a 20-min brisk walk after meals, prioritize slow-digesting oats & leafy greens, and cut back on sweetened drinks."
            }
        elif status == "below_range":
            return {
                "care_level": "Needs Daily Boost (Nutrition Focus)",
                "trainer_action": "Carry healthy snacks (nuts, fruit) to prevent mid-morning energy dips and keep glucose stable."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Great work! Maintain your balanced meal timings and regular daily movement."
            }

    elif c in ["LDL", "CHOL_TOTAL", "TRIGLYCERIDES", "VLDL"]:
        if status in ["above_range", "critical"]:
            return {
                "care_level": "Needs Extra Care (Trainer Focus)",
                "trainer_action": "Incorporate soluble fiber (chia seeds, oats, beans), switch to extra virgin olive oil, and do 20 mins of daily aerobic cardio."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Heart-friendly numbers! Continue eating whole foods and staying active."
            }

    elif c == "HDL":
        if status in ["below_range", "critical"]:
            return {
                "care_level": "Needs Extra Care (Trainer Focus)",
                "trainer_action": "Boost your 'Good' HDL cholesterol with moderate cardio (brisk walking/swimming) and healthy nuts/avocados."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Excellent protective HDL cholesterol! Keep moving daily."
            }

    elif c == "VITAMIN_D":
        if status in ["below_range", "critical"]:
            return {
                "care_level": "Needs Extra Care (Trainer Focus)",
                "trainer_action": "Enjoy 15-20 mins of safe morning sunshine on arms/face, and incorporate fortified foods or egg yolks."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Strong bone density support! Maintain your outdoor morning habits."
            }

    elif c == "VITAMIN_B12":
        if status in ["below_range", "critical"]:
            return {
                "care_level": "Needs Daily Boost (Nutrition Focus)",
                "trainer_action": "Fuel your physical energy and nerves with dairy, eggs, fish, or fortified nutritional yeast."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Optimal cellular energy and nervous system vitality!"
            }

    elif c in ["HEMOGLOBIN", "SERUM_IRON"]:
        if status in ["below_range", "critical"]:
            return {
                "care_level": "Needs Daily Boost (Nutrition Focus)",
                "trainer_action": "Pair iron-rich foods (spinach, lentils, beans) with Vitamin C (lemon, tomatoes) to maximize absorption."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Superb oxygen-carrying capacity and stamina! Keep well-hydrated."
            }

    elif c in ["CREATININE", "BUN", "EGFR"]:
        if status in ["above_range", "below_range", "critical"]:
            return {
                "care_level": "Needs Extra Care (Trainer Focus)",
                "trainer_action": "Drink 2.5 to 3.0 Liters of water daily to support kidney filtration and keep protein intake well-balanced."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Healthy kidney balance! Maintain consistent daily hydration."
            }

    elif c in ["SGPT_ALT", "SGOT_AST", "BILIRUBIN"]:
        if status in ["above_range", "critical"]:
            return {
                "care_level": "Needs Extra Care (Trainer Focus)",
                "trainer_action": "Support liver recovery with cruciferous vegetables (broccoli/cabbage), plenty of water, and minimal fried foods."
            }
        else:
            return {
                "care_level": "Optimal (Maintain Routine)",
                "trainer_action": "Excellent metabolic vitality! Continue your wholesome whole-food routine."
            }

    # Default fallback
    if status in ["above_range", "critical"]:
        return {
            "care_level": "Needs Extra Care (Trainer Focus)",
            "trainer_action": "Focus on daily nutrient-dense meals, consistent hydration, and light-to-moderate physical movement."
        }
    elif status == "below_range":
        return {
            "care_level": "Needs Daily Boost (Nutrition Focus)",
            "trainer_action": "Incorporate targeted whole-food nutrition and track your daily wellness metrics."
        }
    else:
        return {
            "care_level": "Optimal (Maintain Routine)",
            "trainer_action": "All numbers look great! Maintain your healthy lifestyle and daily habits."
        }



MEDICAL_KEYWORDS = [
    "glucose", "sugar", "hba1c", "cholesterol", "lipid", "triglyceride", "hdl", "ldl", "vldl",
    "hemoglobin", "leukocyte", "wbc", "rbc", "platelet", "hematocrit", "creatinine", "urea", "bun",
    "egfr", "uric acid", "bilirubin", "sgpt", "alt", "sgot", "ast", "alkaline phosphatase", "alp",
    "protein", "albumin", "globulin", "thyroid", "tsh", "t3", "t4", "vitamin", "calcium", "iron",
    "ferritin", "sodium", "potassium", "chloride", "laboratory", "diagnostic", "pathology", "specimen",
    "reference range", "ref range", "bio-reference", "normal range", "hospital", "clinic", "doctor",
    "patient name", "test name", "blood test", "urine test", "clinical report", "investigation report"
]


def is_valid_medical_report_text(text: str, parsed_results: Optional[List[Any]] = None) -> bool:
    """
    Checks if a document contains valid medical, laboratory, or diagnostic content.
    Returns True if recognized biomarkers exist or at least 2 clinical keywords are found.
    """
    if parsed_results and len(parsed_results) > 0:
        return True
    
    if not text or len(text.strip()) < 10:
        return False

    text_lower = text.lower()
    matches = sum(1 for kw in MEDICAL_KEYWORDS if kw in text_lower)
    return matches >= 2


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        return f"PDF Text Extraction Error: {str(e)}"


def extract_patient_demographics(text: str) -> Dict[str, Any]:
    demographics = {}
    lines = text.splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Patient Name Extraction
        if not demographics.get("name"):
            name_match = re.search(r"(?:patient\s*name|pt\s*name|name)\s*[:\-\|]\s*([A-Za-z\s\.\,\'\-]+)", line_clean, re.IGNORECASE)
            if name_match:
                raw_name = name_match.group(1).strip()
                raw_name = re.split(r"(?:age|gender|sex|dob|date|ref|dr|doctor|mrn|id|phone)", raw_name, flags=re.IGNORECASE)[0].strip()
                if len(raw_name) >= 2 and not raw_name.lower().startswith("dr"):
                    demographics["name"] = raw_name.title()

        # Age Extraction
        if not demographics.get("age"):
            age_match = re.search(r"(?:age|yrs?)\s*[:\-\|\/]?\s*([0-9]{1,3})\s*(?:years?|yrs?|y)?", line_clean, re.IGNORECASE)
            if age_match:
                demographics["age"] = f"{age_match.group(1)} Years"

        # Gender Extraction
        if not demographics.get("gender"):
            gender_match = re.search(r"(?:gender|sex)\s*[:\-\|\/]?\s*(Male|Female|Other|M|F)\b", line_clean, re.IGNORECASE)
            if gender_match:
                g = gender_match.group(1).upper()
                demographics["gender"] = "Male" if g in ["M", "MALE"] else "Female" if g in ["F", "FEMALE"] else "Other"

        # Weight Extraction
        if not demographics.get("weight"):
            wt_match = re.search(r"(?:weight|wt|body weight)\s*[:\-\|\/]?\s*([0-9]{1,3}(?:\.[0-9]+)?)\s*(?:kg|kgs|lbs|pounds)?", line_clean, re.IGNORECASE)
            if wt_match:
                demographics["weight"] = f"{wt_match.group(1)} kg"

    return demographics


def calculate_gauge_percentage(val: float, ref_min: float, ref_max: float) -> float:
    if ref_max <= ref_min:
        return 50.0
    span = ref_max - ref_min
    pct = ((val - ref_min) / span) * 100.0
    return round(max(0.0, min(120.0, pct)), 1)


def parse_lab_text_to_structured_results(text: str) -> List[Dict[str, Any]]:
    results = []
    lines = text.splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 3 or line_clean.startswith("---") or line_clean.startswith("==="):
            continue

        matched = False
        for code, meta in CANONICAL_BIOMARKERS.items():
            keywords = [meta["friendly_name"].lower(), meta["name"].lower(), code.lower().replace("_", " ")]
            
            if code == "HBA1C":
                keywords.extend(["hba1c", "glycated hemoglobin", "a1c", "glycohemoglobin", "3-month blood sugar"])
            elif code == "GLUCOSE_FASTING":
                keywords.extend(["fasting blood glucose", "fasting glucose", "fbs", "fasting blood sugar", "glucose - fasting", "fasting plasma glucose"])
            elif code == "GLUCOSE_PP":
                keywords.extend(["post prandial glucose", "ppbs", "glucose post lunch", "postprandial glucose", "after-meal blood sugar"])
            elif code == "CHOL_TOTAL":
                keywords.extend(["total cholesterol", "serum cholesterol", "cholesterol - total"])
            elif code == "LDL":
                keywords.extend(["ldl cholesterol", "ldl-c", "direct ldl", "ldl - cholesterol", "bad cholesterol"])
            elif code == "HDL":
                keywords.extend(["hdl cholesterol", "hdl-c", "direct hdl", "hdl - cholesterol", "good cholesterol"])
            elif code == "TRIGLYCERIDES":
                keywords.extend(["triglycerides", "serum triglycerides", "tg"])
            elif code == "VLDL":
                keywords.extend(["vldl cholesterol", "vldl-c", "vldl"])
            elif code == "CREATININE":
                keywords.extend(["serum creatinine", "creatinine", "s. creatinine", "kidney check"])
            elif code == "BUN":
                keywords.extend(["blood urea nitrogen", "bun", "blood urea"])
            elif code == "URIC_ACID":
                keywords.extend(["uric acid", "serum uric acid"])
            elif code == "EGFR":
                keywords.extend(["egfr", "estimated gfr", "glomerular filtration rate"])
            elif code == "HEMOGLOBIN":
                keywords.extend(["hemoglobin", "hb count", "hb (hemoglobin)", "haemoglobin", "oxygen carriers"])
            elif code == "WBC":
                keywords.extend(["total leukocyte", "wbc count", "wbc", "total wbc", "tlc", "white blood cells"])
            elif code == "PLATELETS":
                keywords.extend(["platelet count", "platelets", "total platelets", "clotting cells"])
            elif code == "RBC":
                keywords.extend(["rbc count", "red blood cell count", "total rbc"])
            elif code == "HEMATOCRIT":
                keywords.extend(["hematocrit", "pcv", "packed cell volume"])
            elif code == "SGOT_AST":
                keywords.extend(["sgot", "ast", "aspartate aminotransferase", "sgot/ast"])
            elif code == "SGPT_ALT":
                keywords.extend(["sgpt", "alt", "alanine aminotransferase", "sgpt/alt"])
            elif code == "BILIRUBIN_TOTAL":
                keywords.extend(["total bilirubin", "bilirubin - total", "serum bilirubin"])
            elif code == "ALKALINE_PHOS":
                keywords.extend(["alkaline phosphatase", "alp", "alk phos"])
            elif code == "TSH":
                keywords.extend(["tsh", "thyroid stimulating hormone", "ultrasensitive tsh", "thyroid control"])
            elif code == "FREE_T3":
                keywords.extend(["free t3", "ft3"])
            elif code == "FREE_T4":
                keywords.extend(["free t4", "ft4"])
            elif code == "VITAMIN_D":
                keywords.extend(["vitamin d", "25-hydroxy vitamin d", "vit d3", "25-oh vitamin d", "vitamin d3"])
            elif code == "VITAMIN_B12":
                keywords.extend(["vitamin b12", "vit b12", "cyanocobalamin", "b12"])
            elif code == "CALCIUM":
                keywords.extend(["serum calcium", "calcium", "total calcium"])
            elif code == "SERUM_IRON":
                keywords.extend(["serum iron", "iron total", "total iron"])

            for kw in keywords:
                match = re.search(r"\b" + re.escape(kw) + r"\b", line_clean.lower())
                if match:
                    remainder = line_clean[match.end():]
                    nums = re.findall(r"([0-9]+\.?[0-9]*)", remainder)
                    if nums:
                        val = float(nums[0])
                        ref_min = meta["ref_min"]
                        ref_max = meta["ref_max"]

                        range_match = re.search(r"([0-9]+\.?[0-9]*)\s*[\-\–\to]+\s*([0-9]+\.?[0-9]*)", remainder[len(nums[0]):])
                        if range_match:
                            try:
                                ref_min = float(range_match.group(1))
                                ref_max = float(range_match.group(2))
                            except ValueError:
                                pass

                        status = "within_range"
                        if ref_min is not None and val < ref_min:
                            status = "below_range"
                        elif ref_max is not None and val > ref_max:
                            status = "above_range"

                        crit_high = meta.get("critical_high")
                        crit_low = meta.get("critical_low")
                        if (crit_high and val >= crit_high) or (crit_low and val <= crit_low):
                            status = "critical"

                        gauge_pct = calculate_gauge_percentage(val, ref_min, ref_max)
                        confidence = 0.98 if range_match else 0.92
                        coaching = get_personal_trainer_coaching(code, status, val, meta["unit"])

                        results.append({
                            "biomarker_name": meta["name"],
                            "friendly_name": meta["friendly_name"],
                            "canonical_code": code,
                            "category": meta["category"],
                            "numeric_value": val,
                            "string_value": str(val),
                            "unit": meta["unit"],
                            "ref_min": ref_min,
                            "ref_max": ref_max,
                            "ref_range_raw": f"{ref_min} - {ref_max} {meta['unit']}",
                            "status_flag": status,
                            "care_level": coaching["care_level"],
                            "trainer_action": coaching["trainer_action"],
                            "gauge_percentage": gauge_pct,
                            "confidence": confidence,
                            "is_high_confidence": confidence >= 0.90,
                            "explanation_simple": meta["description"],
                            "significance": f"{meta['friendly_name']} is {'in the healthy normal zone' if status == 'within_range' else 'outside the standard healthy zone'}.",
                            "recommendation": coaching["trainer_action"]
                        })
                        matched = True
                        break
            if matched:
                break

    return results
