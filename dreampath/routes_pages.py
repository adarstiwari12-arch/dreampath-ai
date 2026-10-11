"""Routes: server-rendered pages. Interactive data is loaded by page scripts from /api."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .catalog import stream_by_slug, stream_curriculum, streams_with_stats
from .db import get_db
from .meter import PHASES, TIERS
from .routes_auth import faculty_required, login_required
from .security import safe_next

bp = Blueprint("pages", __name__)


def _needs_setup() -> bool:
    return g.user["stream_id"] is None or g.user["target_lpa"] is None


def _setup_redirect():
    flash("Finish choosing your stream and package to unlock your roadmap.", "info")
    return redirect(url_for("pages.setup", next=request.path))


@bp.get("/")
def landing():
    return render_template("landing.html", streams=streams_with_stats(get_db()), tiers=TIERS)


@bp.get("/streams/<slug>")
def stream_detail(slug: str):
    db = get_db()
    stream = stream_by_slug(db, slug)
    if stream is None:
        abort(404, "We could not find that stream.")
    return render_template("stream_detail.html", stream=stream, phases=stream_curriculum(db, stream["id"]),
                           tiers=TIERS, others=[s for s in streams_with_stats(db) if s["slug"] != slug])


@bp.get("/setup")
@login_required
def setup():
    if g.user["role"] == "faculty":
        return redirect(url_for("pages.faculty"))
    streams = streams_with_stats(get_db())
    current = {
        "slug": next((s["slug"] for s in streams if s["id"] == g.user["stream_id"]), ""),
        "lpa": g.user["target_lpa"],
        "pace": g.user["daily_hours"],
    }
    return render_template("setup.html", streams=streams, tiers=TIERS, current=current,
                           preselect=request.args.get("stream", ""),
                           next_url=safe_next(request.args.get("next"), "/dashboard"))


@bp.get("/dashboard")
@login_required
def dashboard():
    if g.user["role"] == "faculty":
        return redirect(url_for("pages.faculty"))
    if _needs_setup():
        return _setup_redirect()
    row = get_db().execute("SELECT slug FROM streams WHERE id = ?", (g.user["stream_id"],)).fetchone()
    return render_template("dashboard.html", stream_slug=row["slug"])


@bp.get("/roadmap")
@login_required
def roadmap():
    if g.user["role"] == "faculty":
        return redirect(url_for("pages.faculty"))
    if _needs_setup():
        return _setup_redirect()
    return render_template("roadmap.html", phases=PHASES)


@bp.get("/mentor")
@login_required
def mentor():
    if g.user["role"] == "faculty":
        return redirect(url_for("pages.faculty"))
    if _needs_setup():
        return _setup_redirect()
    return render_template("mentor.html")


@bp.get("/faculty")
@faculty_required
def faculty():
    return render_template("faculty.html", phases=PHASES)
