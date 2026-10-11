"""Read-only catalogue queries shared by the page routes and the JSON API."""
from .meter import PHASES, TIERS


def streams_with_stats(db) -> list:
    """All streams with lesson counts and minutes, cumulative per tier.

    `lessons[t]` and `minutes[t]` are the totals a student on tier `t` gets,
    because a tier includes every step whose minimum tier is at or below it.
    """
    streams = [dict(r) for r in db.execute("SELECT id, slug, name, tagline, description FROM streams ORDER BY id")]
    by_stream = {s["id"]: {"lessons": [0] * len(TIERS), "minutes": [0] * len(TIERS)} for s in streams}
    rows = db.execute(
        "SELECT stream_id, min_tier, COUNT(*) AS n, COALESCE(SUM(duration_min), 0) AS m "
        "FROM steps GROUP BY stream_id, min_tier").fetchall()
    for row in rows:
        stats = by_stream.get(row["stream_id"])
        if stats is None:
            continue
        for tier in range(row["min_tier"], len(TIERS)):  # cumulative
            stats["lessons"][tier] += row["n"]
            stats["minutes"][tier] += row["m"]
    for s in streams:
        stats = by_stream[s["id"]]
        s["lessons"], s["minutes"] = stats["lessons"], stats["minutes"]
        s["total_lessons"] = stats["lessons"][-1]
        s["total_hours"] = round(stats["minutes"][-1] / 60)
    return streams


def stream_by_slug(db, slug: str):
    return next((s for s in streams_with_stats(db) if s["slug"] == slug), None)


def stream_curriculum(db, stream_id: int) -> list:
    """Every step of a stream grouped by phase (used by the public preview page)."""
    rows = db.execute(
        "SELECT id, phase, title, url, duration_min, weight, min_tier, verified FROM steps "
        "WHERE stream_id = ? ORDER BY phase, position, id", (stream_id,)).fetchall()
    phases = []
    for number, name in PHASES.items():
        steps = [dict(r) for r in rows if r["phase"] == number]
        if steps:
            phases.append({"phase": number, "name": name, "steps": steps,
                           "minutes": sum(s["duration_min"] for s in steps)})
    return phases
