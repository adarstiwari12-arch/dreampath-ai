"""Dream Meter logic. Pure functions, no Flask or database access.

Dream Meter % = (sum of weight of ticked steps / sum of weight of all steps) x 100
"""
import math
from datetime import date, timedelta

PHASES = {
    1: "Foundations",
    2: "Core Skills",
    3: "Projects & Practice",
    4: "Interview Preparation",
    5: "Placement Edge",
}

# A tier decides how deep the roadmap goes. Steps carry a minimum tier, so a
# higher package target unlocks the more advanced steps.
TIERS = [
    {"level": 0, "key": "starter", "name": "Starter", "min": 0, "max": 6,
     "blurb": "Solid fundamentals and a clean resume for core and service roles."},
    {"level": 1, "key": "growth", "name": "Growth", "min": 6, "max": 12,
     "blurb": "Stronger core subjects, tools and projects for product and mid-tier roles."},
    {"level": 2, "key": "pro", "name": "Pro", "min": 12, "max": 25,
     "blurb": "Depth, design thinking and specialisation for top product companies."},
    {"level": 3, "key": "elite", "name": "Elite", "min": 25, "max": 100,
     "blurb": "Advanced and research-grade skills for the most competitive offers."},
]


def estimate_finish(hours_left: float, daily_hours, today: date) -> dict:
    """When will the student finish at their chosen pace?"""
    try:
        daily = min(8.0, max(0.5, float(daily_hours)))
    except (TypeError, ValueError):
        daily = 1.5
    days = math.ceil(hours_left / daily) if hours_left > 0 else 0
    return {"daily_hours": daily, "days_left": days, "finish_date": (today + timedelta(days=days)).isoformat()}


def streak_days(active_days: set, today: date) -> int:
    """Consecutive days with at least one completed step, ending today.

    If nothing is done yet today the streak is still alive until the day ends,
    so it is counted from yesterday.
    """
    cursor = today if today in active_days else today - timedelta(days=1)
    count = 0
    while cursor in active_days:
        count += 1
        cursor -= timedelta(days=1)
    return count


def tier_for_lpa(lpa) -> dict:
    """Map a target package (LPA) to a preparation tier."""
    try:
        value = float(lpa)
    except (TypeError, ValueError):
        return TIERS[0]
    for tier in reversed(TIERS):
        if value >= tier["min"]:
            return tier
    return TIERS[0]


def readiness_label(percent: float) -> str:
    if percent >= 90:
        return "Interview ready"
    if percent >= 60:
        return "Closing in"
    if percent >= 30:
        return "Building momentum"
    if percent > 0:
        return "Just getting started"
    return "Ready to begin"


def dream_meter(steps: list) -> dict:
    """Compute the meter from a list of step dicts.

    Each step needs: id, phase, position, title, weight, duration_min, done.
    """
    total_weight = sum(s["weight"] for s in steps)
    done_weight = sum(s["weight"] for s in steps if s["done"])
    percent = round(done_weight / total_weight * 100, 1) if total_weight else 0.0

    phases = []
    for phase_no, name in PHASES.items():
        group = [s for s in steps if s["phase"] == phase_no]
        if not group:
            continue
        g_total = sum(s["weight"] for s in group)
        g_done = sum(s["weight"] for s in group if s["done"])
        phases.append({
            "phase": phase_no,
            "name": name,
            "percent": round(g_done / g_total * 100, 1) if g_total else 0.0,
            "done": sum(1 for s in group if s["done"]),
            "total": len(group),
        })

    pending = [s for s in steps if not s["done"]]
    next_step = None
    if pending:
        # Earliest phase first, then the heaviest step, then roadmap order.
        best = min(pending, key=lambda s: (s["phase"], -s["weight"], s["position"], s["id"]))
        next_step = {k: best[k] for k in ("id", "title", "url", "phase", "weight", "duration_min")}
        next_step["phase_name"] = PHASES[best["phase"]]

    return {
        "percent": percent,
        "label": readiness_label(percent),
        "done_weight": done_weight,
        "total_weight": total_weight,
        "done_count": len(steps) - len(pending),
        "total_count": len(steps),
        "hours_left": round(sum(s["duration_min"] for s in pending) / 60, 1),
        "phases": phases,
        "next_step": next_step,
    }
