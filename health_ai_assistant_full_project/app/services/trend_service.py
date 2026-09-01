"""
Dynamic Longitudinal Biomarker Trend and Report Comparison Engine.
Computes real previous vs current values, deltas, and trajectory directions strictly from uploaded patient data.
"""
from typing import Dict, List, Any


def build_biomarker_trendlines(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Group biomarker values by canonical code/name across dates with real deltas."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for r in results:
        code = r.get("canonical_code") or r.get("biomarker_name", "UNKNOWN")
        if code not in grouped:
            grouped[code] = []
        
        grouped[code].append({
            "date": str(r.get("recorded_date")),
            "biomarker_name": r.get("biomarker_name", code),
            "value": r.get("numeric_value"),
            "string_value": r.get("string_value"),
            "unit": r.get("unit", ""),
            "status_flag": r.get("status_flag", "within_range"),
            "ref_min": r.get("ref_min"),
            "ref_max": r.get("ref_max"),
            "ref_range_raw": r.get("ref_range_raw", "")
        })

    trend_summaries = []
    comparisons = []

    for code, points in grouped.items():
        points.sort(key=lambda p: p["date"])
        b_name = points[0]["biomarker_name"]
        unit = points[0]["unit"]
        
        if len(points) == 0:
            continue
        elif len(points) == 1:
            trend_summaries.append({
                "biomarker_code": code,
                "biomarker_name": b_name,
                "unit": unit,
                "data_points": points,
                "status": "baseline",
                "trend_direction": "Baseline",
                "delta_value": 0.0,
                "percent_change": 0.0,
                "trend_summary": "This is the first available result for this parameter."
            })
        else:
            prev_pt = points[-2]
            curr_pt = points[-1]
            prev_val = prev_pt["value"]
            curr_val = curr_pt["value"]
            
            delta_val = 0.0
            pct_change = 0.0
            direction = "Stable"

            if prev_val is not None and curr_val is not None:
                delta_val = round(curr_val - prev_val, 2)
                if prev_val != 0:
                    pct_change = round(((curr_val - prev_val) / abs(prev_val)) * 100.0, 1)
                
                if delta_val > 0:
                    direction = "Increasing"
                elif delta_val < 0:
                    direction = "Decreasing"
                else:
                    direction = "Stable"

            trend_msg = f"Changed from {prev_val} {unit} ({prev_pt['date']}) to {curr_val} {unit} ({curr_pt['date']}) [Δ {delta_val:+g} {unit}, {pct_change:+g}%]"

            trend_summaries.append({
                "biomarker_code": code,
                "biomarker_name": b_name,
                "unit": unit,
                "data_points": points,
                "status": "multi_point",
                "trend_direction": direction,
                "previous_value": prev_val,
                "previous_date": prev_pt["date"],
                "current_value": curr_val,
                "current_date": curr_pt["date"],
                "delta_value": delta_val,
                "percent_change": pct_change,
                "trend_summary": trend_msg
            })

            comparisons.append({
                "biomarker_name": b_name,
                "unit": unit,
                "previous_value": prev_val,
                "previous_date": prev_pt["date"],
                "current_value": curr_val,
                "current_date": curr_pt["date"],
                "delta_value": delta_val,
                "percent_change": pct_change,
                "direction": direction,
                "current_status": curr_pt["status_flag"]
            })

    total_pts = len(results)
    has_insufficient = total_pts < 2 or all(len(g) < 2 for g in grouped.values())

    return {
        "total_biomarkers_tracked": len(trend_summaries),
        "has_sufficient_data": not has_insufficient,
        "insufficient_data_message": "More reports are needed to generate comparative health trends." if has_insufficient else None,
        "trends": trend_summaries,
        "recent_comparisons": comparisons
    }
