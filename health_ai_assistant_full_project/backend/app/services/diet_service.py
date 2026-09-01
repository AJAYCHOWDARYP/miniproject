"""
Dynamic Nutrition and Meal Schedule Engine based strictly on verified patient report findings.
Translates laboratory biomarkers into everyday meals, foods to enjoy, foods to limit, and plain-language benefits.
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


def generate_personalized_diet_plan(
    profile: Optional[Any] = None,
    latest_report: Optional[Any] = None,
    report_results: Optional[List[Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    # Extract profile attributes with safe fallbacks
    age = float(_get_val(profile, "age", 35.0) or 35.0)
    sex = str(_get_val(profile, "gender") or _get_val(profile, "sex") or "Not Specified")
    height_cm = float(_get_val(profile, "height_cm", 170.0) or 170.0)
    weight_kg = float(_get_val(profile, "weight_kg", 70.0) or 70.0)
    activity_level = str(_get_val(profile, "activity_level", "moderate") or "moderate")
    dietary_preferences = _get_val(profile, "dietary_preferences", ["balanced"]) or ["balanced"]
    allergies = _get_val(profile, "allergies", []) or []

    if "age" in kwargs and kwargs["age"] is not None: age = float(kwargs["age"])
    if "sex" in kwargs and kwargs["sex"] is not None: sex = str(kwargs["sex"])
    if "height_cm" in kwargs and kwargs["height_cm"] is not None: height_cm = float(kwargs["height_cm"])
    if "weight_kg" in kwargs and kwargs["weight_kg"] is not None: weight_kg = float(kwargs["weight_kg"])
    if "activity_level" in kwargs and kwargs["activity_level"] is not None: activity_level = str(kwargs["activity_level"])
    if "dietary_preferences" in kwargs and kwargs["dietary_preferences"] is not None: dietary_preferences = kwargs["dietary_preferences"]
    if "allergies" in kwargs and kwargs["allergies"] is not None: allergies = kwargs["allergies"]

    # Calculate caloric and hydration targets
    if str(sex).lower() in ["female", "f"]:
        bmr = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age - 161.0
    else:
        bmr = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age + 5.0

    multipliers = {"sedentary": 1.2, "moderate": 1.45, "active": 1.70}
    factor = multipliers.get(str(activity_level).lower(), 1.4)
    tdee = max(1400, int(bmr * factor))
    target_water = round(max(1.8, weight_kg * 0.033), 1)

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

    if "abnormal_biomarkers" in kwargs and isinstance(kwargs["abnormal_biomarkers"], list):
        abnormal_biomarkers.extend(kwargs["abnormal_biomarkers"])

    has_data = bool(latest_report or report_results or abnormal_biomarkers)
    report_title = str(_get_val(latest_report, "title") or "Latest Medical Report")
    report_date = str(_get_val(latest_report, "report_date") or "")

    abnormal_text = " ".join(abnormal_biomarkers).lower()
    has_glucose_flag = "glucose" in abnormal_text or "hba1c" in abnormal_text or "sugar" in abnormal_text
    has_lipid_flag = "cholesterol" in abnormal_text or "ldl" in abnormal_text or "triglyceride" in abnormal_text
    has_vit_d_flag = "vitamin d" in abnormal_text or "vit d" in abnormal_text
    has_kidney_flag = "creatinine" in abnormal_text or "bun" in abnormal_text or "egfr" in abnormal_text or "uric acid" in abnormal_text
    has_hb_flag = "hemoglobin" in abnormal_text or "iron" in abnormal_text or "ferritin" in abnormal_text
    has_liver_flag = "alt" in abnormal_text or "ast" in abnormal_text or "bilirubin" in abnormal_text or "sgpt" in abnormal_text or "sgot" in abnormal_text
    has_thyroid_flag = "tsh" in abnormal_text or "t3" in abnormal_text or "t4" in abnormal_text or "thyroid" in abnormal_text

    clinical_focus = []
    if has_glucose_flag:
        clinical_focus.append("Blood Sugar Stability (Low-Glycemic, High-Fiber Complex Carbs)")
    if has_lipid_flag:
        clinical_focus.append("Heart & Blood Fat Clearance (Soluble Fiber & Heart-Healthy Monounsaturated Fats)")
    if has_vit_d_flag:
        clinical_focus.append("Vitamin D & Bone Density (Fortified Foods, Safe Sunshine & Healthy Fats)")
    if has_kidney_flag:
        clinical_focus.append("Kidney Flushing & Hydration (Adequate Daily Water & Controlled Protein)")
    if has_hb_flag:
        clinical_focus.append("Red Blood Cell & Iron Support (Iron-Rich Leafy Greens, Lentils & Vitamin C)")
    if has_liver_flag:
        clinical_focus.append("Liver Antioxidant Support (Cruciferous Veggies, Green Tea & Turmeric)")
    if has_thyroid_flag:
        clinical_focus.append("Thyroid Metabolic Health (Selenium, Zinc & Iodine-Balanced Whole Foods)")

    if not clinical_focus and has_data:
        clinical_focus.append("Overall Vitality & Long-Term Cellular Maintenance (Balanced Whole Foods)")

    # Build 5 daily report-driven meals
    meals = []

    # 1. Breakfast (08:00 AM)
    if has_glucose_flag and has_lipid_flag:
        b_food = "Steel-cut oats cooked in unsweetened almond milk, topped with 1 tbsp chia seeds, 1 tbsp ground flaxseed, crushed raw walnuts, and a dash of Ceylon cinnamon."
        b_reason = "Ceylon cinnamon slows gastric emptying for blood sugar stability, while soluble beta-glucan and flaxseed omega-3s bind excess cholesterol."
        b_target = "Glucose & Cholesterol Control"
    elif has_glucose_flag:
        b_food = "Steel-cut rolled oats with unsweetened almond milk, topped with chia seeds, crushed walnuts, and a pinch of Ceylon cinnamon."
        b_reason = "Ceylon cinnamon and soluble oat fiber slow glucose absorption and prevent morning blood sugar spikes."
        b_target = "Blood Sugar Management"
    elif has_lipid_flag:
        b_food = "Oatmeal with chia seeds, ground flaxseeds, sliced green apple, and a handful of raw walnuts."
        b_reason = "Beta-glucan soluble fiber actively binds to bile acids in your gut, pulling excess LDL cholesterol out of circulation."
        b_target = "Cholesterol Clearance"
    elif has_hb_flag:
        b_food = "Sprouted mung bean salad with pomegranate seeds, crushed almonds, lemon juice, and a slice of toasted sprouted grain bread."
        b_reason = "Vitamin C in fresh lemon and pomegranate maximizes the absorption of non-heme plant iron by up to 300%."
        b_target = "Iron & Hemoglobin Production"
    elif has_kidney_flag:
        b_food = "Light vegetable poha (flattened rice) with carrots, green peas, and fresh cilantro, served with herbal chamomile tea."
        b_reason = "Low-phosphorus, moderate-potassium breakfast that provides clean energy without placing filtration strain on kidneys."
        b_target = "Kidney-Friendly Digestion"
    elif has_vit_d_flag:
        b_food = "Fortified Greek/plant yogurt or scrambled eggs with sautéed button mushrooms, spinach, and a teaspoon of cold-pressed olive oil."
        b_reason = "Healthy dietary lipids significantly improve the intestinal assimilation of fat-soluble Vitamin D."
        b_target = "Vitamin D Assimilation"
    else:
        b_food = "Warm oatmeal or sprouted grain toast with mashed avocado, poached egg, and fresh berries."
        b_reason = "Provides sustained energy with healthy fats, clean protein, and natural antioxidant vitamins."
        b_target = "General Vitality"

    meals.append({
        "time": "08:00 AM",
        "meal_name": "🌅 Energizing Breakfast",
        "food": b_food,
        "reason": b_reason,
        "target_biomarker": b_target,
        "portion": "1 Medium Bowl (approx. 350-400 kcal)"
    })

    # 2. Mid-Morning Snack (11:00 AM)
    if has_vit_d_flag:
        mm_food = "Handful of raw almonds and walnuts paired with fortified plant yogurt or a boiled egg."
        mm_reason = "Healthy dietary fats maximize the absorption of fat-soluble Vitamin D."
        mm_target = "Vitamin D & Bone Vitality"
    elif has_hb_flag:
        mm_food = "Small bowl of soaked black raisins, dried figs (anjeer), and a few roasted pumpkin seeds."
        mm_reason = "Concentrated natural source of non-heme iron and copper to stimulate red blood cell synthesis."
        mm_target = "Hemoglobin Boost"
    elif has_kidney_flag:
        mm_food = "Crisp cucumber slices and red apple wedges with fresh mint water."
        mm_reason = "High moisture content supports gentle renal flushing while keeping sodium and potassium in optimal balance."
        mm_target = "Hydration & Renal Ease"
    elif has_glucose_flag:
        mm_food = "Roasted pumpkin seeds or a small handful of raw walnuts with green tea."
        mm_reason = "Healthy fats and magnesium support cellular insulin sensitivity without carbohydrate load."
        mm_target = "Insulin Sensitivity"
    elif has_lipid_flag:
        mm_food = "A small ripe pear with 8-10 raw almonds and unsweetened green tea."
        mm_reason = "Pectin fruit fiber and monounsaturated almond fats protect vascular walls and support HDL production."
        mm_target = "Vascular Protection"
    else:
        mm_food = "Fresh seasonal fruit (pear/apple) with 10-12 raw almonds."
        mm_reason = "Gentle fiber and natural vitamins keep energy steady until lunch."
        mm_target = "Metabolic Balance"

    meals.append({
        "time": "11:00 AM",
        "meal_name": "🌤️ Mid-Morning Snack",
        "food": mm_food,
        "reason": mm_reason,
        "target_biomarker": mm_target,
        "portion": "1 Small Handful (approx. 150-180 kcal)"
    })

    # 3. Wholesome Lunch (01:00 PM)
    if has_glucose_flag and has_lipid_flag:
        l_food = "Large bowl of mixed garden greens (spinach, cucumber, tomatoes) dressed in extra virgin olive oil, paired with brown lentils (dal), grilled tofu or skinless chicken, and half cup quinoa or whole wheat roti."
        l_reason = "Plant protein and low-GI legumes provide a steady, flat glycemic response while plant sterols block cholesterol reabsorption."
        l_target = "Glucose & Lipid Balance"
    elif has_glucose_flag:
        l_food = "Steamed quinoa or brown rice with spiced lentil curry (dal), abundant steamed broccoli, and fresh cucumber slices."
        l_reason = "High volume of green fiber buffers carbohydrate breakdown, preventing post-meal sleepiness and glucose spikes."
        l_target = "Blood Sugar Control"
    elif has_lipid_flag:
        l_food = "Grilled wild salmon or baked tofu over a rainbow quinoa bowl with steamed asparagus, chickpeas, and a drizzle of cold-pressed olive oil."
        l_reason = "Omega-3 fatty acids lower triglycerides and boost protective HDL cholesterol."
        l_target = "Heart & Blood Fat Clearance"
    elif has_hb_flag:
        l_food = "Steamed brown rice with iron-rich spinach dal (palak dal), roasted bell peppers, and grilled tofu or chicken breast dressed in lemon juice."
        l_reason = "Combines dietary iron with bioflavonoids and Vitamin C to replenish depleted iron stores."
        l_target = "Cellular Oxygenation"
    elif has_kidney_flag:
        l_food = "Steamed white basmati rice with light yellow moong dal, sautéed zucchini, and steamed cauliflower."
        l_reason = "Easily digestible, controlled-protein meal that minimizes nitrogenous waste accumulation."
        l_target = "Renal Filtration Support"
    else:
        l_food = "Balanced plate: 50% colorful vegetables, 25% lean protein (lentils/beans/fish), and 25% whole complex grains."
        l_reason = "Balanced macronutrient distribution prevents metabolic fatigue and maintains healthy cellular function."
        l_target = "Metabolic Maintenance"

    meals.append({
        "time": "01:00 PM",
        "meal_name": "🥗 Wholesome Lunch",
        "food": l_food,
        "reason": l_reason,
        "target_biomarker": l_target,
        "portion": "1 Standard Balanced Plate (approx. 550-650 kcal)"
    })

    # 4. Afternoon Refreshment (04:30 PM)
    if has_hb_flag:
        af_food = "Warm ginger-lemon herbal infusion with roasted makhana (fox nuts) and roasted pumpkin seeds."
        af_reason = "Provides magnesium and zinc without dairy calcium or black tea tannins which hinder iron absorption."
        af_target = "Micronutrient Synergy"
    elif has_lipid_flag:
        af_food = "Freshly brewed hibiscus or green tea with a handful of raw walnut halves."
        af_reason = "Hibiscus anthocyanins and green tea EGCG promote healthy arterial elasticity and reduce LDL oxidation."
        af_target = "Arterial Health"
    elif has_kidney_flag:
        af_food = "Warm herbal nettle or coriander seed water with roasted puffed rice (bhel) without added salt."
        af_reason = "Gentle natural diuretic herbs support clean urinary clearance without potassium retention."
        af_target = "Electrolyte Balance"
    else:
        af_food = "Warm chamomile or green tea with a handful of roasted spiced chickpeas or cucumber sticks with hummus."
        af_reason = "Provides clean hydration, polyphenols, and fiber without added sugars or trans fats."
        af_target = "Hydration & Antioxidants"

    meals.append({
        "time": "04:30 PM",
        "meal_name": "🍵 Afternoon Refreshment",
        "food": af_food,
        "reason": af_reason,
        "target_biomarker": af_target,
        "portion": "1 Cup Tea + Small Snack (approx. 100-140 kcal)"
    })

    # 5. Light Restorative Dinner (07:30 PM)
    if has_glucose_flag:
        d_food = "Hearty vegetable and moong dal soup with sautéed mushrooms, tofu, and steamed greens. Kept light on heavy carbs."
        d_reason = "Eating light on evening carbohydrates keeps fasting blood sugar steady throughout the night."
        d_target = "Overnight Fasting Glucose"
    elif has_lipid_flag:
        d_food = "Warm lentil and vegetable stew with a side of steamed spinach and baked sweet potato."
        d_reason = "Easy-to-digest fiber supports nighttime liver lipid processing."
        d_target = "Nighttime Lipid Clearance"
    elif has_hb_flag:
        d_food = "Warm black chana and vegetable soup with steamed broccoli, beetroot slices, and sprouted grain toast."
        d_reason = "Nourishing, easily digestible iron-rich dinner to support nocturnal hemoglobin synthesis."
        d_target = "Nocturnal Blood Building"
    elif has_kidney_flag:
        d_food = "Clear vegetable broth with diced carrots, bottle gourd (lauki), and a small cup of steamed rice."
        d_reason = "Very gentle on the kidneys, promoting restful sleep without nocturnal electrolyte imbalances."
        d_target = "Nocturnal Kidney Rest"
    else:
        d_food = "Light vegetable stir-fry with tofu/paneer and a small cup of brown rice or vegetable soup."
        d_reason = "Promotes easy digestion and supports deep, restorative sleep."
        d_target = "Digestive Rest"

    meals.append({
        "time": "07:30 PM",
        "meal_name": "🍲 Light Dinner",
        "food": d_food,
        "reason": d_reason,
        "target_biomarker": d_target,
        "portion": "1 Bowl (approx. 400-480 kcal)"
    })

    # Foods to enjoy and limit based on clinical flags
    foods_to_enjoy = []
    foods_to_limit = []

    if has_glucose_flag:
        foods_to_enjoy.append({"food": "Ceylon Cinnamon & Fenugreek Seeds", "reason": "Naturally improves insulin receptor sensitivity and smooths glucose uptake."})
        foods_to_enjoy.append({"food": "Non-Starchy Vegetables (Spinach, Broccoli, Bitter Gourd)", "reason": "Packed with dietary fiber, minerals, and zero glycemic spike."})
        foods_to_limit.append({"food": "White Bread, Refined Rice & Sugary Sweets", "reason": "Fast-digesting carbohydrates that rapidly spike blood glucose and elevate HbA1c."})

    if has_lipid_flag:
        foods_to_enjoy.append({"food": "Soluble Fiber (Oats, Chia, Flax, Beans, Apples)", "reason": "Binds to dietary cholesterol and bile acids, facilitating gentle clearance."})
        foods_to_enjoy.append({"food": "Heart-Friendly Fats (Extra Virgin Olive Oil, Avocados, Walnuts)", "reason": "Elevates protective 'Good' HDL cholesterol and maintains arterial flexibility."})
        foods_to_limit.append({"food": "Deep-Fried Foods, Palm Oil & Trans Fats", "reason": "Directly raises 'Bad' LDL cholesterol and increases circulating blood fats."})

    if has_vit_d_flag:
        foods_to_enjoy.append({"food": "Fortified Dairy/Plant Milk, Eggs & Button Mushrooms", "reason": "Provides bioavailable Vitamin D to synergize with safe sunlight."})

    if has_hb_flag:
        foods_to_enjoy.append({"food": "Dark Leafy Greens, Black Lentils, Pomegranate & Lemon", "reason": "Provides elemental iron and Vitamin C to support hemoglobin synthesis."})
        foods_to_limit.append({"food": "Black Tea or Coffee with Meals", "reason": "Tannins and polyphenols bind to iron in the digestive tract, blocking absorption."})

    if has_kidney_flag:
        foods_to_enjoy.append({"food": "High-Moisture Veggies (Cucumbers, Bottle Gourd, Zucchini)", "reason": "Assists gentle renal flushing with low potassium and phosphorus burden."})
        foods_to_limit.append({"food": "Excessive Salt, Processed Meat & High-Sodium Pickles", "reason": "Causes fluid retention and elevates pressure inside delicate kidney filters."})

    if not foods_to_enjoy:
        foods_to_enjoy = [
            {"food": "Soluble Fiber (Oats, Chia, Flax, Beans)", "reason": "Binds to excess cholesterol and smooths out blood sugar absorption."},
            {"food": "Heart-Friendly Fats (Olive Oil, Walnuts, Avocados)", "reason": "Protects blood vessels and supports cell membrane integrity."},
            {"food": "Non-Starchy Veggies (Spinach, Broccoli, Cucumbers)", "reason": "Loaded with micronutrients, potassium, and hydration."}
        ]

    if not foods_to_limit:
        foods_to_limit = [
            {"food": "Sugary Drinks, Sodas & Fruit Juices", "reason": "Rapidly spikes blood sugar and triggers liver fat storage."},
            {"food": "Deep-Fried Snacks & Bakery Items", "reason": "Contains trans fats and refined flours that elevate LDL cholesterol."},
            {"food": "Ultra-Processed Prepackaged Meals", "reason": "High in hidden sodium and preservatives that strain blood pressure."}
        ]

    meal_structure = {
        "breakfast": meals[0]["food"],
        "morning_snack": meals[1]["food"],
        "lunch": meals[2]["food"],
        "evening_snack": meals[3]["food"],
        "dinner": meals[4]["food"]
    }

    return {
        "title": f"Personalized Meal Guide adapted from {report_title}" if has_data else "Healthy Meal Guide (Personalized)",
        "has_data": has_data,
        "report_title": report_title if has_data else None,
        "report_date": report_date if has_data else None,
        "report_title_linked": f"{report_title} ({report_date})" if report_date else report_title,
        "target_calories_kcal": tdee,
        "target_water_liters": target_water,
        "clinical_focus": clinical_focus,
        "clinical_focus_areas": clinical_focus,
        "abnormal_biomarkers_addressed": abnormal_biomarkers,
        "normal_biomarkers_maintained": normal_biomarkers,
        "meal_structure": meal_structure,
        "daily_schedule": meals,
        "foods_to_enjoy": foods_to_enjoy,
        "foods_to_limit": foods_to_limit,
        "guidance_note": "This meal guide is personalized to address the blood tests in your medical report. Always consult your doctor or registered dietitian before making drastic dietary changes."
    }
