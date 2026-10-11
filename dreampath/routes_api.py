"""Routes: JSON API used by the front-end scripts."""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, abort, current_app, g, jsonify, request

from . import ai
from .catalog import streams_with_stats
from .db import get_db
from .meter import PHASES, TIERS, dream_meter, estimate_finish, streak_days, tier_for_lpa
from .routes_auth import faculty_required, login_required
from .security import rate_limit, valid_http_url

bp = Blueprint("api", __name__, url_prefix="/api")


# ------------------------------------------------------------------ helpers

def json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "Expected a JSON object.")
    return data


def streams_list(db) -> list:
    return [dict(r) for r in db.execute("SELECT id, slug, name, tagline, description FROM streams ORDER BY id")]


def local_now() -> datetime:
    """Current time shifted by the configured offset (India by default)."""
    return datetime.now(timezone.utc) + timedelta(minutes=current_app.config["UTC_OFFSET_MINUTES"])


def to_local(stamp: str) -> datetime:
    """Convert a stored UTC timestamp ("YYYY-MM-DD HH:MM:SS") to local time."""
    utc = datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)
    return utc + timedelta(minutes=current_app.config["UTC_OFFSET_MINUTES"])


def user_steps(db, user) -> list:
    """Steps for the user's stream that fit their package tier, with done flags."""
    tier = tier_for_lpa(user["target_lpa"])["level"]
    rows = db.execute(
        "SELECT s.id, s.phase, s.position, s.title, s.url, s.duration_min, s.weight, s.verified, "
        "       (p.user_id IS NOT NULL) AS done "
        "FROM steps s LEFT JOIN progress p ON p.step_id = s.id AND p.user_id = ? "
        "WHERE s.stream_id = ? AND s.min_tier <= ? ORDER BY s.phase, s.position, s.id",
        (user["id"], user["stream_id"], tier),
    ).fetchall()
    return [{**dict(r), "done": bool(r["done"]), "verified": bool(r["verified"])} for r in rows]


def require_profile():
    if g.user["stream_id"] is None or g.user["target_lpa"] is None:
        abort(409, "Choose a stream and a target package first.")


def ai_context(db) -> dict:
    steps = user_steps(db, g.user)
    stream = db.execute("SELECT name FROM streams WHERE id = ?", (g.user["stream_id"],)).fetchone()
    return {
        "first_name": g.user["name"].split()[0],
        "stream": stream["name"],
        "lpa": g.user["target_lpa"],
        "tier": tier_for_lpa(g.user["target_lpa"])["name"],
        "meter": dream_meter(steps),
        "steps": steps,
    }


# ------------------------------------------------------------------ catalogue & profile

@bp.get("/streams")
def streams():
    db = get_db()
    current = None
    if g.user is not None and g.user["stream_id"] is not None:
        row = db.execute("SELECT slug FROM streams WHERE id = ?", (g.user["stream_id"],)).fetchone()
        current = {"stream": row["slug"] if row else None, "target_lpa": g.user["target_lpa"],
                   "daily_hours": g.user["daily_hours"]}
    return jsonify(streams=streams_with_stats(db), tiers=TIERS, current=current)


@bp.post("/profile")
@login_required
@rate_limit(60, 600)
def set_profile():
    """Create or update the learning profile. Every field is optional once a profile exists."""
    data = json_body()
    db = get_db()

    stream_id = g.user["stream_id"]
    if "stream" in data:
        stream = db.execute("SELECT id FROM streams WHERE slug = ?", (str(data["stream"]),)).fetchone()
        if not stream:
            abort(400, "Please choose a valid stream.")
        stream_id = stream["id"]

    lpa = g.user["target_lpa"]
    if "target_lpa" in data:
        raw = data["target_lpa"]
        try:
            lpa = float(raw)
        except (TypeError, ValueError):
            abort(400, "Target package must be a number.")
        if isinstance(raw, bool) or not 1 <= lpa <= 100:
            abort(400, "Target package must be between 1 and 100 LPA.")
        lpa = round(lpa, 1)

    daily = g.user["daily_hours"]
    if "daily_hours" in data:
        raw = data["daily_hours"]
        try:
            daily = float(raw)
        except (TypeError, ValueError):
            abort(400, "Study hours per day must be a number.")
        if isinstance(raw, bool) or not 0.5 <= daily <= 8:
            abort(400, "Study hours per day must be between 0.5 and 8.")

    if stream_id is None or lpa is None:
        abort(400, "Choose a stream and a target package.")
    db.execute("UPDATE users SET stream_id = ?, target_lpa = ?, daily_hours = ? WHERE id = ?",
               (stream_id, lpa, daily, g.user["id"]))
    db.commit()
    return jsonify(ok=True, tier=tier_for_lpa(lpa))


# ------------------------------------------------------------------ roadmap & progress

@bp.get("/roadmap")
@login_required
def roadmap():
    require_profile()
    db = get_db()
    steps = user_steps(db, g.user)
    stream = db.execute("SELECT slug, name FROM streams WHERE id = ?", (g.user["stream_id"],)).fetchone()
    phases = []
    for number, name in PHASES.items():
        group = [s for s in steps if s["phase"] == number]
        if group:
            phases.append({"phase": number, "name": name, "steps": group})
    meter = dream_meter(steps)
    return jsonify(
        stream=dict(stream),
        target_lpa=g.user["target_lpa"],
        tier=tier_for_lpa(g.user["target_lpa"]),
        phases=phases,
        meter=meter,
        **activity(db, meter),
    )


def activity(db, meter: dict) -> dict:
    """Study plan, streak and recently completed lessons for the signed-in student."""
    today = local_now().date()
    stamps = [r["completed_at"] for r in db.execute(
        "SELECT completed_at FROM progress WHERE user_id = ?", (g.user["id"],))]
    days = {to_local(s).date() for s in stamps}
    recent = [{"id": r["id"], "title": r["title"], "phase": r["phase"],
               "completed_on": to_local(r["completed_at"]).date().isoformat()}
              for r in db.execute(
        "SELECT s.id, s.title, s.phase, p.completed_at FROM progress p JOIN steps s ON s.id = p.step_id "
        "WHERE p.user_id = ? AND s.stream_id = ? ORDER BY p.completed_at DESC, p.rowid DESC LIMIT 5",
        (g.user["id"], g.user["stream_id"]))]
    return {
        "plan": estimate_finish(meter["hours_left"], g.user["daily_hours"], today),
        "streak": streak_days(days, today),
        "active_today": today in days,
        "recent": recent,
    }


@bp.post("/progress/<int:step_id>")
@login_required
@rate_limit(240, 600)
def set_progress(step_id: int):
    require_profile()
    done = json_body().get("done")
    if not isinstance(done, bool):
        abort(400, "`done` must be true or false.")
    db = get_db()
    allowed = {s["id"] for s in user_steps(db, g.user)}
    if step_id not in allowed:  # blocks ticking steps from other streams or higher tiers
        abort(404, "That step is not part of your roadmap.")
    if done:
        db.execute("INSERT OR IGNORE INTO progress (user_id, step_id) VALUES (?, ?)", (g.user["id"], step_id))
    else:
        db.execute("DELETE FROM progress WHERE user_id = ? AND step_id = ?", (g.user["id"], step_id))
    db.commit()
    meter = dream_meter(user_steps(db, g.user))
    return jsonify(meter=meter, **activity(db, meter))


# ------------------------------------------------------------------ AI

@bp.post("/ai/recommend-stream")
@login_required
@rate_limit(15, 600, scope="ai")
def ai_recommend():
    text = str(json_body().get("interests", "")).strip()
    if len(text) < 10:
        abort(400, "Tell us a little more (at least 10 characters) about what you enjoy.")
    if len(text) > 800:
        abort(400, "Please keep it under 800 characters.")
    return jsonify(ai.recommend_stream(text, streams_list(get_db())))


@bp.post("/ai/gap")
@login_required
@rate_limit(15, 600, scope="ai")
def ai_gap():
    require_profile()
    ctx = ai_context(get_db())
    pending = sorted((s for s in ctx["steps"] if not s["done"]), key=lambda s: (-s["weight"], s["phase"]))
    return jsonify(ai.gap_analysis(ctx, [f"{s['title']} ({s['weight']} pts)" for s in pending[:3]]))


@bp.get("/ai/mentor")
@login_required
def mentor_history():
    rows = get_db().execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 40", (g.user["id"],)
    ).fetchall()
    return jsonify(messages=[dict(r) for r in reversed(rows)], llm=ai.llm_enabled())


@bp.post("/ai/mentor")
@login_required
@rate_limit(30, 600, scope="ai")
def mentor_send():
    require_profile()
    message = str(json_body().get("message", "")).strip()
    if not message:
        abort(400, "Type a question first.")
    if len(message) > 600:
        abort(400, "Please keep your question under 600 characters.")
    db = get_db()
    history = [dict(r) for r in db.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 8", (g.user["id"],)
    ).fetchall()][::-1]
    result = ai.mentor_reply(ai_context(db), history, message)
    db.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (g.user["id"], message))
    db.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'assistant', ?)", (g.user["id"], result["reply"]))
    # keep the stored history small
    db.execute("DELETE FROM chat_messages WHERE user_id = ? AND id NOT IN "
               "(SELECT id FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 60)", (g.user["id"], g.user["id"]))
    db.commit()
    return jsonify(result)


@bp.delete("/ai/mentor")
@login_required
def mentor_clear():
    db = get_db()
    db.execute("DELETE FROM chat_messages WHERE user_id = ?", (g.user["id"],))
    db.commit()
    return jsonify(ok=True)


# ------------------------------------------------------------------ faculty

def clean_step(data: dict) -> dict:
    """Validate a step payload from the faculty form."""
    title = " ".join(str(data.get("title", "")).split())
    url = str(data.get("url", "")).strip()
    if not 3 <= len(title) <= 160:
        abort(400, "Title must be 3 to 160 characters.")
    if not valid_http_url(url):
        abort(400, "Video link must be a valid http(s) URL.")
    try:
        step = {
            "title": title, "url": url,
            "phase": int(data.get("phase")), "duration_min": int(data.get("duration_min")),
            "weight": int(data.get("weight")), "min_tier": int(data.get("min_tier")),
            "verified": 1 if data.get("verified") is True else 0,
        }
    except (TypeError, ValueError):
        abort(400, "Phase, duration, weight and tier must be whole numbers.")
    if not 1 <= step["phase"] <= 5:
        abort(400, "Phase must be between 1 and 5.")
    if not 1 <= step["duration_min"] <= 3000:
        abort(400, "Duration must be between 1 and 3000 minutes.")
    if not 1 <= step["weight"] <= 10:
        abort(400, "Weight must be between 1 and 10.")
    if not 0 <= step["min_tier"] <= 3:
        abort(400, "Tier must be between 0 and 3.")
    return step


@bp.get("/faculty/overview")
@faculty_required
def faculty_overview():
    db = get_db()
    stats = [dict(r) for r in db.execute(
        "SELECT st.slug, st.name, "
        "  (SELECT COUNT(*) FROM users u WHERE u.stream_id = st.id AND u.role = 'student') AS students, "
        "  (SELECT COUNT(*) FROM steps s WHERE s.stream_id = st.id) AS steps, "
        "  (SELECT COUNT(*) FROM steps s WHERE s.stream_id = st.id AND s.verified = 1) AS verified "
        "FROM streams st ORDER BY st.id")]
    total = db.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    return jsonify(streams=stats, students=total)


@bp.get("/faculty/steps")
@faculty_required
def faculty_steps():
    stream = get_db().execute("SELECT id FROM streams WHERE slug = ?", (request.args.get("stream", ""),)).fetchone()
    if not stream:
        abort(404, "Unknown stream.")
    rows = get_db().execute(
        "SELECT id, phase, position, title, url, duration_min, weight, min_tier, verified "
        "FROM steps WHERE stream_id = ? ORDER BY phase, position, id", (stream["id"],)).fetchall()
    return jsonify(steps=[{**dict(r), "verified": bool(r["verified"])} for r in rows])


@bp.post("/faculty/steps")
@faculty_required
@rate_limit(120, 600, scope="faculty")
def faculty_create():
    data = json_body()
    step = clean_step(data)
    db = get_db()
    stream = db.execute("SELECT id FROM streams WHERE slug = ?", (str(data.get("stream", "")),)).fetchone()
    if not stream:
        abort(400, "Unknown stream.")
    pos = db.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM steps WHERE stream_id = ?", (stream["id"],)).fetchone()[0]
    cur = db.execute(
        "INSERT INTO steps (stream_id, phase, position, title, url, duration_min, weight, min_tier, verified) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (stream["id"], step["phase"], pos, step["title"], step["url"], step["duration_min"],
         step["weight"], step["min_tier"], step["verified"]))
    db.commit()
    return jsonify(id=cur.lastrowid), 201


@bp.put("/faculty/steps/<int:step_id>")
@faculty_required
@rate_limit(240, 600, scope="faculty")
def faculty_update(step_id: int):
    step = clean_step(json_body())
    db = get_db()
    cur = db.execute(
        "UPDATE steps SET phase = ?, title = ?, url = ?, duration_min = ?, weight = ?, min_tier = ?, verified = ? "
        "WHERE id = ?",
        (step["phase"], step["title"], step["url"], step["duration_min"], step["weight"],
         step["min_tier"], step["verified"], step_id))
    db.commit()
    if cur.rowcount == 0:
        abort(404, "Step not found.")
    return jsonify(ok=True)


@bp.delete("/faculty/steps/<int:step_id>")
@faculty_required
@rate_limit(120, 600, scope="faculty")
def faculty_delete(step_id: int):
    db = get_db()
    cur = db.execute("DELETE FROM steps WHERE id = ?", (step_id,))
    db.commit()
    if cur.rowcount == 0:
        abort(404, "Step not found.")
    return jsonify(ok=True)
