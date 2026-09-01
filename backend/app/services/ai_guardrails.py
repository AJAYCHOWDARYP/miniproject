"""
AI Plain-Language Clinical Insights Engine.
Translates complex medical laboratory reports into clear, friendly, and practical explanations.
"""
import re
from typing import Dict, List, Any, Optional
from app.core.config import settings

STANDARD_DISCLAIMER = (
    "A Friendly Health Note: This summary explains your laboratory report in everyday language to help you prepare for your doctor visit. "
    "This AI Assistant does not provide diagnoses or prescribe medications. Always discuss these results directly with your healthcare provider."
)


def evaluate_emergency_triage(text: str) -> Optional[Dict[str, Any]]:
    text_lower = text.lower()
    for kw in settings.EMERGENCY_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            return {
                "is_emergency": True,
                "detected_keyword": kw,
                "title": "🚨 URGENT: Potential Medical Emergency Detected",
                "message": (
                    f"You mentioned '{kw}'. If you or someone near you is experiencing sudden, severe, or life-threatening symptoms, "
                    "please seek emergency medical care right away.\n\n"
                    "• Call emergency services immediately (911 in US/Canada, 112 in Europe/India, 999 in UK).\n"
                    "• Go to the nearest Emergency Room.\n"
                    "• Do not wait for online analysis."
                ),
                "hotlines": [
                    {"region": "US / Canada", "number": "911"},
                    {"region": "India", "number": "112 / 108"},
                    {"region": "UK", "number": "999"},
                    {"region": "Europe", "number": "112"},
                    {"region": "Crisis / Suicide Hotline", "number": "988 (US) / 112 (Universal)"}
                ]
            }
    return None


def evaluate_prescription_refusal(text: str) -> Optional[str]:
    patterns = [
        r"what (medicine|drug|pill|antibiotic|steroid) should i (take|use|start)",
        r"prescribe (me|for me)",
        r"can i (stop|quit|discontinue)",
        r"(stop|quit|discontinue).*(taking|medicine|medication|pill|tablet|drug|dose)",
        r"should i (increase|double|change|reduce) (my|the) dose",
        r"what is the (correct|safe )?dose for",
        r"give me a prescription",
    ]
    text_lower = text.lower()
    for pat in patterns:
        if re.search(pat, text_lower):
            return (
                "Only a licensed healthcare professional can prescribe medications, change dosages, "
                "or recommend stopping a treatment safely. Medication decisions require checking your complete physical health and history.\n\n"
                "I can help you organize your daily prescription schedule, set reminders, or prepare questions for your doctor or pharmacist."
            )
    return None


def evaluate_diagnosis_refusal(text: str) -> Optional[str]:
    patterns = [
        r"do i have (cancer|diabetes|hiv|heart attack|kidney disease|stroke|tumor|leukemia|hypertension)",
        r"diagnose (me|this|my condition)",
        r"what disease do i have",
        r"am i dying",
    ]
    text_lower = text.lower()
    for pat in patterns:
        if re.search(pat, text_lower):
            return (
                "I cannot provide a medical diagnosis. A proper diagnosis requires a full in-person evaluation, examination, and testing by a qualified doctor.\n\n"
                "I can help explain which specific numbers on your lab report are outside normal ranges and give you clear questions to ask your doctor."
            )
    return None


def generate_layered_report_insights(
    report_title: str,
    report_date: str,
    results: List[Dict[str, Any]],
    historical_results: Optional[List[Dict[str, Any]]] = None,
    demographics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    abnormal_items = []
    normal_items = []
    why_this_matters_list = []
    
    categories_detected = set()
    auto_verified_count = 0

    for r in results:
        flag = r.get("status_flag", "within_range")
        name = r.get("biomarker_name", "Test")
        cat = r.get("category", "General Health")
        categories_detected.add(cat)
        val = r.get("numeric_value") or r.get("string_value", "N/A")
        unit = r.get("unit", "")
        ref = r.get("ref_range_raw", "")
        desc = r.get("explanation_simple", f"Checks {name} in your blood.")
        confidence = r.get("confidence", 0.95)
        if confidence >= 0.90:
            auto_verified_count += 1
        
        item_obj = {
            "biomarker_name": name,
            "canonical_code": r.get("canonical_code"),
            "category": cat,
            "value": f"{val} {unit}".strip(),
            "numeric_value": r.get("numeric_value"),
            "unit": unit,
            "status": flag,
            "reference_range": ref,
            "explanation": desc,
            "source": f"{report_title} ({report_date})"
        }

        if flag in ["above_range", "below_range", "critical"]:
            item_obj["note"] = f"Result is {'above' if flag == 'above_range' else 'below' if flag == 'below_range' else 'significantly outside'} the healthy standard range ({ref})."
            abnormal_items.append(item_obj)

            b_name_lower = name.lower()
            if "glucose" in b_name_lower or "hba1c" in b_name_lower:
                what_it_means = "This test measures the amount of sugar in your bloodstream."
                why_it_matters = "When blood sugar stays higher than ideal over time, it means your body is finding it harder to clear sugar into your cells for energy. Lowering this helps prevent fatigue and long-term diabetes."
                doctor_discuss = [
                    "Is my blood sugar level high enough that we should do a repeat fasting test?",
                    "What simple changes to my carbohydrates, sweets, or daily meals would help the most?",
                    "Would a daily 20-30 minute walk after meals help bring this number down?"
                ]
            elif "cholesterol" in b_name_lower or "ldl" in b_name_lower or "triglyceride" in b_name_lower:
                what_it_means = "This checks the amount of circulating fats in your blood."
                why_it_matters = "Having extra 'bad' (LDL) cholesterol or triglycerides means excess fat particles are traveling through your blood vessels, which can slowly accumulate on artery walls over time."
                doctor_discuss = [
                    "How does this cholesterol level affect my overall heart health?",
                    "What healthy food swaps (like adding oats, beans, olive oil, and fiber) should I focus on?",
                    "Do we need follow-up testing in 3 to 6 months to check my progress?"
                ]
            elif "vitamin d" in b_name_lower:
                what_it_means = "Vitamin D is an essential sunshine nutrient that works like a hormone in your body."
                why_it_matters = "When Vitamin D is low, your body cannot absorb calcium properly, which can cause tired muscles, fatigue, bone aches, or lower immune resilience."
                doctor_discuss = [
                    "Would a daily Vitamin D supplement help bring my levels back into the healthy green zone?",
                    "What dose do you recommend, and for how many weeks should I take it?"
                ]
            elif "creatinine" in b_name_lower or "bun" in b_name_lower:
                what_it_means = "This checks how effectively your kidneys are filtering and cleaning natural waste from your blood."
                why_it_matters = "Kidneys filter your blood 24/7. Staying well-hydrated with clean water helps your kidneys flush waste smoothly and keeps this score healthy."
                doctor_discuss = [
                    "How much water should I drink daily to support healthy kidney filtration?",
                    "Are any of my current medications or pain relievers affecting my kidneys?"
                ]
            else:
                what_it_means = f"This measures {name} in your body."
                why_it_matters = f"Your result ({val} {unit}) is outside the standard reference range ({ref}). Keeping this in balance supports your daily energy and wellness."
                doctor_discuss = [
                    "What could be causing this number to be outside the normal range?",
                    "What simple lifestyle or dietary steps can I take to improve it?"
                ]

            why_this_matters_list.append({
                "biomarker_name": name,
                "value": f"{val} {unit}".strip(),
                "reference_range": ref,
                "status": flag,
                "what_it_means": what_it_means,
                "why_it_matters": why_it_matters,
                "what_to_discuss": doctor_discuss
            })
        else:
            normal_items.append(item_obj)

    total_tests = len(results)
    abnormal_count = len(abnormal_items)
    requires_review_count = total_tests - auto_verified_count
    
    cat_str = ", ".join(sorted(list(categories_detected))) if categories_detected else "General Health Panels"
    if total_tests == 0:
        report_desc = f"We reviewed this document from {report_date}. No measurable blood or lab numbers were detected in the text. The reason for testing was not explicitly specified in the report."
        overall_headline = "No measurable laboratory results found in this document."
    elif abnormal_count == 0:
        report_desc = (
            f"This is your medical report titled '{report_title}' dated {report_date}. It includes {total_tests} health measurements "
            f"covering {cat_str}. Great news: all {total_tests} of your tested parameters are in the healthy normal range. "
            "The reason for testing was not explicitly specified in the report."
        )
        overall_headline = "Great news! All your tested health numbers are in the healthy normal zone."
    else:
        report_desc = (
            f"This is your medical report titled '{report_title}' dated {report_date}. It includes {total_tests} health measurements "
            f"covering {cat_str}. {len(normal_items)} parameter(s) are in the healthy green range, and {abnormal_count} result(s) are outside standard ranges and deserve a quick look with your doctor. "
            "The reason for testing was not explicitly specified in the report."
        )
        overall_headline = f"Here is what your test results mean in plain English ({len(normal_items)} healthy, {abnormal_count} need attention)."

    l1_summary = (
        f"This report analyzed {total_tests} health measurement(s). "
        f"{len(normal_items)} are in the healthy range, and {abnormal_count} need your attention. "
        "Below is a clear, simple breakdown of what every number means for your body."
    )

    interpretations = []
    doctor_considerations = []
    diet_recs = []
    activity_recs = []

    for item in abnormal_items:
        b_name = item["biomarker_name"].lower()
        if "hba1c" in b_name or "glucose" in b_name:
            interpretations.append({
                "biomarker": item["biomarker_name"],
                "value": item["value"],
                "cautious_association": "Blood sugar levels are naturally influenced by recent meals, carbohydrate intake, sleep, stress, hydration, and how physically active you have been.",
                "source_trace": item["source"]
            })
            doctor_considerations.append("Your doctor may review your daily carbohydrate intake, physical activity, or schedule a repeat fasting check.")
            diet_recs.append("Choose wholesome, slow-digesting carbs (like rolled oats, lentils, beans, and fresh green veggies) and cut back on sugary sodas, candy, and white bread.")
            activity_recs.append("Enjoy a brisk 20-30 minute walk every day, especially after meals, to help your muscles naturally use up excess blood sugar.")
        elif "cholesterol" in b_name or "ldl" in b_name or "triglyceride" in b_name:
            interpretations.append({
                "biomarker": item["biomarker_name"],
                "value": item["value"],
                "cautious_association": "Cholesterol and blood fat levels can be improved through healthy dietary fats, eating more soluble fiber, regular movement, and healthy liver function.",
                "source_trace": item["source"]
            })
            doctor_considerations.append("Your doctor may discuss heart-healthy dietary adjustments, physical movement, or follow-up lipid testing in 3-6 months.")
            diet_recs.append("Eat more soluble fiber (chia seeds, flaxseeds, oats, beans, and apples) and switch to heart-friendly fats like olive oil, avocados, and walnuts.")
            activity_recs.append("Light to moderate aerobic exercise (like brisk walking, cycling, or swimming) helps boost your 'Good' HDL cholesterol and clears blood fats.")
        elif "creatinine" in b_name or "egfr" in b_name or "bun" in b_name:
            interpretations.append({
                "biomarker": item["biomarker_name"],
                "value": item["value"],
                "cautious_association": "Kidney waste numbers are strongly influenced by daily water intake, protein consumption, muscle mass, and certain medications or pain relievers.",
                "source_trace": item["source"]
            })
            doctor_considerations.append("Your doctor may check your daily hydration levels, review current medications, or order a routine follow-up kidney panel.")
            diet_recs.append("Drink plenty of clean water throughout the day (aim for 2 to 2.5 liters) and discuss your daily protein intake with your doctor.")
        elif "vitamin d" in b_name or "b12" in b_name or "iron" in b_name:
            interpretations.append({
                "biomarker": item["biomarker_name"],
                "value": item["value"],
                "cautious_association": f"Low levels of {item['biomarker_name']} are very common and usually caused by dietary habits, limited sunshine exposure, or digestion absorption.",
                "source_trace": item["source"]
            })
            doctor_considerations.append(f"Your doctor may recommend specific food choices or a simple daily supplement for {item['biomarker_name']}.")
            diet_recs.append(f"Enjoy foods rich in {item['biomarker_name']} (such as fortified milk/plant milk, mushrooms, eggs, fish, and safe sunshine exposure) as advised by your doctor.")
        else:
            interpretations.append({
                "biomarker": item["biomarker_name"],
                "value": item["value"],
                "cautious_association": "Laboratory variations are common and can be influenced by hydration, stress, and lifestyle. A healthcare professional can help you understand what this means for your individual health.",
                "source_trace": item["source"]
            })

    if not diet_recs:
        diet_recs.append("Enjoy a balanced, wholesome diet full of fresh vegetables, whole grains, clean protein, and plenty of water every day.")
    if not activity_recs:
        activity_recs.append("Aim for about 150 minutes of enjoyable physical movement per week (like 25-30 minutes of daily walking, swimming, or dancing).")

    doctor_questions = [
        "What simple diet or lifestyle step will help improve my numbers the most?",
        "Do you recommend repeating any of these tests in 3 to 6 months to track my progress?",
        "Could my current hydration, sleep, stress, or supplements have influenced these numbers?",
        "Are there specific everyday foods or daily movement routines you recommend for me?"
    ]
    if abnormal_count > 0:
        doctor_questions.insert(0, f"What is the best way for us to bring my {abnormal_items[0]['biomarker_name']} ({abnormal_items[0]['value']}) back into the healthy normal zone?")

    overall_summary_card = {
        "headline": overall_headline,
        "total_analyzed": total_tests,
        "within_range_count": len(normal_items),
        "outside_range_count": abnormal_count,
        "normal_parameters": [n["biomarker_name"] for n in normal_items],
        "attention_parameters": [a["biomarker_name"] for a in abnormal_items],
        "synthesis": (
            f"Your report from {report_date} shows {len(normal_items)} measurement(s) in the healthy normal range and {abnormal_count} item(s) that need a little extra attention. "
            "With simple daily food choices, light movement, and your doctor's advice, these numbers can be managed effectively."
        )
    }

    personalized_suggestions = {
        "diet": list(dict.fromkeys(diet_recs)),
        "physical_activity": list(dict.fromkeys(activity_recs)),
        "medication_treatment": "Never start, stop, or change any medication on your own. If you have questions about medicines or supplements, discuss options directly with your doctor or pharmacist.",
        "professional_followup": (
            f"Bring this report to your doctor so you can review {'the results for ' + ', '.join([a['biomarker_name'] for a in abnormal_items[:3]]) if abnormal_items else 'your overall health progress'} together."
        )
    }

    extraction_verification = {
        "total_extracted": total_tests,
        "auto_verified_count": auto_verified_count,
        "requires_review_count": requires_review_count
    }

    return {
        "patient_demographics": demographics or {},
        "report_description": report_desc,
        "extraction_verification": extraction_verification,
        "layer_1_simple_explanation": l1_summary,
        "layer_2_normal_findings": normal_items,
        "layer_2_abnormal_findings": abnormal_items,
        "why_this_matters": why_this_matters_list,
        "layer_3_possible_interpretations": interpretations,
        "layer_4_historical_trends": "Your progress is automatically compared across visits.",
        "layer_4_doctor_considerations": list(set(doctor_considerations)),
        "layer_5_questions_for_doctor": doctor_questions,
        "overall_summary_card": overall_summary_card,
        "personalized_suggestions": personalized_suggestions,
        "disclaimer": STANDARD_DISCLAIMER
    }
