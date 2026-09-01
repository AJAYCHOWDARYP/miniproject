"""
Dynamic Activity & Movement Engine based strictly on verified patient report findings.
Translates laboratory biomarkers into practical, enjoyable, and safe daily movement routines.
"""
from typing import Dict, List, Any, Optional


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        v = obj.get(key)
        return v if v is not None else default
    v = getattr(obj, key, None)
    return v if v is not None else default


def generate_personalized_exercise_plan(
    profile: Optional[Any] = None,
    latest_report: Optional[Any] = None,
    report_results: Optional[List[Any]] = None,
    conditions: Optional[List[Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    age = float(_get_val(profile, "age", 35.0) or 35.0)
    activity_level = str(_get_val(profile, "activity_level", "moderate") or "moderate")
    cond_list = []

    if conditions:
        for c in conditions:
            c_name = _get_val(c, "condition_name", str(c))
            cond_list.append(str(c_name).lower())

    if "age" in kwargs and kwargs["age"] is not None: age = float(kwargs["age"])
    if "activity_level" in kwargs and kwargs["activity_level"] is not None: activity_level = str(kwargs["activity_level"])
    if "conditions" in kwargs and isinstance(kwargs["conditions"], list):
        cond_list.extend([str(c).lower() for c in kwargs["conditions"]])

    # Collect abnormal biomarkers from results or report
    abnormal_biomarkers = []
    normal_biomarkers = []
    if report_results:
        for r in report_results:
            name = _get_val(r, "biomarker_name", "")
            status = _get_val(r, "status_flag", "")
            val = _get_val(r, "numeric_value", "")
            unit = _get_val(r, "unit", "")
            if status in ["above_range", "below_range", "critical"]:
                abnormal_biomarkers.append(f"{name} ({val} {unit})".strip())
            elif status == "within_range":
                normal_biomarkers.append(name)
    elif latest_report:
        ai_layers = _get_val(latest_report, "ai_summary_layers", {})
        if isinstance(ai_layers, dict):
            abnormals = ai_layers.get("layer_2_abnormal_findings", [])
            for a in abnormals:
                abnormal_biomarkers.append(f"{a.get('biomarker_name')} ({a.get('value')})")

    has_data = bool(latest_report or report_results or abnormal_biomarkers)
    report_title = str(_get_val(latest_report, "title") or "Latest Medical Report")
    report_date = str(_get_val(latest_report, "report_date") or "")

    abnormal_text = " ".join(abnormal_biomarkers).lower()
    has_glucose_flag = "glucose" in abnormal_text or "hba1c" in abnormal_text or "sugar" in abnormal_text
    has_lipid_flag = "cholesterol" in abnormal_text or "ldl" in abnormal_text or "triglyceride" in abnormal_text
    has_vit_d_flag = "vitamin d" in abnormal_text or "vit d" in abnormal_text
    has_kidney_flag = "creatinine" in abnormal_text or "bun" in abnormal_text or "egfr" in abnormal_text
    has_hb_flag = "hemoglobin" in abnormal_text or "iron" in abnormal_text or "anemia" in abnormal_text

    clinical_focus = []
    if has_glucose_flag:
        clinical_focus.append("Post-Meal Glucose Disposal (15-20 min post-meal walks)")
    if has_lipid_flag:
        clinical_focus.append("Lipid Clearance & HDL Boost (Moderate aerobic cardio & intervals)")
    if has_vit_d_flag:
        clinical_focus.append("Sunshine Synthesis & Bone Loading (Morning outdoor walks & bodyweight)")
    if has_hb_flag:
        clinical_focus.append("Oxygen Conservation & Gentle Stamina (Paced low-intensity movement)")
    if has_kidney_flag:
        clinical_focus.append("Low-Impact Gentle Filtration (Hydration-supported light walks)")

    if not clinical_focus and has_data:
        clinical_focus.append("Aerobic Endurance & Daily Flexibility Maintenance")

    routines = []

    # 1. Morning Routine (07:30 AM)
    if has_vit_d_flag:
        routines.append({
            "category": "🌅 Morning Sunshine Walk (Vitamin D & Bone Density)",
            "time": "07:30 AM",
            "duration_minutes": 25,
            "activity": "Comfortable brisk walk outdoors with direct sunlight on face and arms, accompanied by 5 minutes of gentle bodyweight calf-raises.",
            "benefit": "Stimulates natural cutaneous Vitamin D synthesis and delivers safe mechanical impact to strengthen bone mineral density.",
            "target_biomarker": "Vitamin D Synthesis & Bone Mineralization"
        })
    elif has_lipid_flag:
        routines.append({
            "category": "🌅 Morning Aerobic Cardio Walk",
            "time": "07:30 AM",
            "duration_minutes": 30,
            "activity": "Continuous brisk walk, outdoor cycling, or treadmill walk with slight incline at a conversational aerobic pace.",
            "benefit": "Activates muscle lipoprotein lipase to accelerate triglyceride clearance and increase protective HDL cholesterol.",
            "target_biomarker": "Triglyceride & HDL Clearance"
        })
    elif has_hb_flag:
        routines.append({
            "category": "🌅 Morning Gentle Oxygenation Walk",
            "time": "07:30 AM",
            "duration_minutes": 15,
            "activity": "Relaxed, paced walk on flat terrain with deep nasal breathing intervals.",
            "benefit": "Enhances arterial oxygenation and blood circulation without causing shortness of breath or cellular fatigue.",
            "target_biomarker": "Oxygen Transport & Circulation"
        })
    elif has_kidney_flag:
        routines.append({
            "category": "🌅 Morning Low-Impact Hydration Walk",
            "time": "07:30 AM",
            "duration_minutes": 20,
            "activity": "Gentle, steady walk on comfortable ground after drinking a glass of water.",
            "benefit": "Promotes smooth systemic blood flow and supports healthy renal blood perfusion.",
            "target_biomarker": "Renal Blood Flow"
        })
    else:
        routines.append({
            "category": "🌅 Morning Aerobic Walk",
            "time": "07:30 AM",
            "duration_minutes": 30,
            "activity": "Brisk outdoor walking or treadmill walk at an easy conversational pace.",
            "benefit": "Boosts cardiovascular stamina and promotes steady blood circulation throughout the day.",
            "target_biomarker": "Cardiovascular Health"
        })

    # 2. Midday / Post-Meal Routine (01:45 PM - 02:30 PM)
    if has_glucose_flag:
        routines.append({
            "category": "🚶 Post-Meal Blood Sugar Walk",
            "time": "01:45 PM",
            "duration_minutes": 15,
            "activity": "Gentle 15-minute walk started within 20-30 minutes after finishing your lunch meal.",
            "benefit": "Engages large quadricep and soleus muscles to absorb circulating blood glucose directly without requiring additional insulin.",
            "target_biomarker": "Post-Meal Glucose Disposal"
        })
    elif has_lipid_flag:
        routines.append({
            "category": "🚴 Midday Vascular Interval Cardio",
            "time": "02:30 PM",
            "duration_minutes": 20,
            "activity": "Brisk walking intervals (2 minutes moderate, 1 minute fast) or stationary cycling.",
            "benefit": "Increases endothelial nitric oxide release, relaxing blood vessels and assisting liver lipid filtration.",
            "target_biomarker": "Arterial Elasticity & Lipid Clearance"
        })
    elif has_hb_flag:
        routines.append({
            "category": "🧘 Midday Diaphragmatic Breath & Posture",
            "time": "02:00 PM",
            "duration_minutes": 10,
            "activity": "Gentle seated spinal twists, shoulder rolls, and 5 minutes of rhythmic diaphragmatic box breathing.",
            "benefit": "Maximizes lung alveolar expansion and alleviates afternoon energy slumps without muscular strain.",
            "target_biomarker": "Cellular Oxygen Uptake"
        })
    elif has_kidney_flag:
        routines.append({
            "category": "🚶 Midday Gentle Circulation Break",
            "time": "02:00 PM",
            "duration_minutes": 10,
            "activity": "Light stroll and gentle ankle circles to break up sedentary sitting.",
            "benefit": "Prevents venous pooling in the legs and supports steady venous return.",
            "target_biomarker": "Venous Circulation"
        })
    else:
        routines.append({
            "category": "🚶 Midday Mobility Walk",
            "time": "02:00 PM",
            "duration_minutes": 15,
            "activity": "Light walking and shoulder rolls to break up seated time.",
            "benefit": "Maintains spinal mobility and prevents sluggish afternoon circulation.",
            "target_biomarker": "Circulation & Posture"
        })

    # 3. Evening Restorative Routine (06:30 PM - 07:00 PM)
    if has_glucose_flag:
        routines.append({
            "category": "🌙 Evening Cortisol-Lowering Stretch",
            "time": "06:30 PM",
            "duration_minutes": 15,
            "activity": "Gentle hamstring stretches, child's pose, and 5 minutes of calm deep breathing.",
            "benefit": "Reduces nighttime cortisol hormone spikes which are a major cause of dawn-phenomenon fasting blood sugar elevation.",
            "target_biomarker": "Fasting Glucose & Cortisol Control"
        })
    elif has_lipid_flag:
        routines.append({
            "category": "🌙 Evening Vascular Restorative Flow",
            "time": "06:30 PM",
            "duration_minutes": 15,
            "activity": "Gentle full-body yoga flow, cat-cow stretches, and legs-up-the-wall relaxation.",
            "benefit": "Eases central blood pressure and calms sympathetic nervous tone to support nighttime liver metabolism.",
            "target_biomarker": "Nocturnal Cardiovascular Recovery"
        })
    elif has_hb_flag:
        routines.append({
            "category": "🌙 Evening Restorative Recovery",
            "time": "06:30 PM",
            "duration_minutes": 15,
            "activity": "Gentle reclining butterfly pose and calm body-scan meditation.",
            "benefit": "Promotes deep restorative sleep where majority of erythropoiesis (red blood cell production) occurs.",
            "target_biomarker": "Restorative Recovery"
        })
    else:
        routines.append({
            "category": "🌙 Evening Flexibility & Stress Relief",
            "time": "06:30 PM",
            "duration_minutes": 15,
            "activity": "Gentle full-body stretching, cat-cow yoga flow, and 5 minutes of calm, deep diaphragmatic breathing.",
            "benefit": "Lowers cortisol stress hormones, eases muscular tension, and prepares your body for deep restorative sleep.",
            "target_biomarker": "Cortisol & Recovery"
        })

    safety_guidelines = [
        "Stay comfortably hydrated before, during, and after your movement sessions.",
        "Take a brisk 10-15 minute walk within 30 minutes after meals to help muscles absorb blood sugar.",
        "If you experience dizziness, joint pain, or shortness of breath, rest immediately and consult your physician."
    ]

    return {
        "title": f"Personalized Daily Movement Plan adapted from {report_title}" if has_data else "Easy Daily Movement Plan",
        "has_data": has_data,
        "report_title": report_title if has_data else None,
        "report_date": report_date if has_data else None,
        "report_title_linked": f"{report_title} ({report_date})" if report_date else report_title,
        "movement_focus_areas": clinical_focus,
        "clinical_focus": clinical_focus,
        "abnormal_biomarkers_addressed": abnormal_biomarkers,
        "routines": routines,
        "daily_routines": routines,
        "safety_guidelines": safety_guidelines,
        "guidance_note": "Designed strictly around your report findings. If you experience dizziness, joint pain, or shortness of breath, rest immediately and consult your physician."
    }
