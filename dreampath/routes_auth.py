"""Routes: registration, login, logout and account management."""
import re
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .security import password_problem, rate_limit, safe_next, valid_email, valid_name

_STREAM_SLUG = re.compile(r"^[a-z]{2,12}$")

bp = Blueprint("auth", __name__)

# Used to burn the same CPU time when an email is unknown, so response timing
# does not reveal which emails have accounts.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@bp.before_app_request
def load_user():
    g.user = None
    if request.endpoint == "static":  # no database work for css/js/images
        return
    uid = session.get("uid")
    if uid is not None:
        row = get_db().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        if row:
            g.user = row
        else:
            session.clear()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if request.path.startswith("/api/"):
                return jsonify(error="Please log in to continue."), 401
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def faculty_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user["role"] != "faculty":
            abort(403, "This area is for faculty accounts only.")
        return view(*args, **kwargs)

    return wrapped


def _start_session(user_id: int) -> None:
    session.clear()  # new session on login prevents session fixation
    session["uid"] = user_id
    session.permanent = True


@bp.route("/register", methods=["GET", "POST"])
@rate_limit(10, 3600, scope="register")
def register():
    raw_next = request.values.get("next", "")
    next_url = safe_next(raw_next, "") if raw_next else ""
    stream = request.values.get("stream", "")
    stream = stream if _STREAM_SLUG.match(stream) else ""
    if g.user:
        return redirect(next_url or url_for("pages.dashboard"))
    form = {"name": "", "email": ""}
    if request.method == "POST":
        name = " ".join(request.form.get("name", "").split())
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        form = {"name": name, "email": email}

        error = None
        if not valid_name(name):
            error = "Please enter your name (2 to 80 characters, letters first)."
        elif not valid_email(email):
            error = "Please enter a valid email address."
        elif password != confirm:
            error = "The two passwords do not match."
        else:
            error = password_problem(password, email, name)

        if not error:
            db = get_db()
            if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
                error = "An account with this email already exists. Try logging in instead."
            else:
                cur = db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                db.commit()
                _start_session(cur.lastrowid)
                flash("Welcome to DreamPath. Let's set up your roadmap.", "success")
                return redirect(url_for("pages.setup", stream=stream or None, next=next_url or None))
        flash(error, "error")
    stream_row = get_db().execute("SELECT name FROM streams WHERE slug = ?", (stream,)).fetchone() if stream else None
    return render_template("register.html", form=form, next_url=next_url, stream=stream if stream_row else "",
                           stream_name=stream_row["name"] if stream_row else "")


@bp.route("/login", methods=["GET", "POST"])
@rate_limit(20, 600, scope="login")
def login():
    raw_next = request.values.get("next", "")
    next_url = safe_next(raw_next, "") if raw_next else ""
    if g.user:
        return redirect(next_url or url_for("pages.dashboard"))
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")[:128]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        error = "Incorrect email or password."

        locked = False
        if user and user["locked_until"]:
            locked = datetime.fromisoformat(user["locked_until"]) > _now()

        if locked:
            error = "Too many failed attempts. Please try again in a few minutes."
        elif user and check_password_hash(user["password_hash"], password):
            db.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
            db.commit()
            _start_session(user["id"])
            if user["role"] == "faculty":
                return redirect(next_url or url_for("pages.faculty"))
            if user["stream_id"] is None or user["target_lpa"] is None:
                return redirect(url_for("pages.setup", next=next_url or None))
            return redirect(next_url or url_for("pages.dashboard"))
        else:
            if user:
                attempts = user["failed_attempts"] + 1
                locked_until = None
                if attempts >= current_app.config["MAX_FAILED_LOGINS"]:
                    locked_until = (_now() + timedelta(minutes=current_app.config["LOCKOUT_MINUTES"])).isoformat()
                    attempts = 0
                db.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                           (attempts, locked_until, user["id"]))
                db.commit()
            else:
                check_password_hash(_DUMMY_HASH, password)
        flash(error, "error")
    return render_template("login.html", email=email, next_url=next_url)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("pages.landing"))


@bp.route("/account", methods=["GET", "POST"])
@login_required
@rate_limit(15, 3600, scope="account")
def account():
    if request.method == "POST":
        action = request.form.get("action")
        current = request.form.get("current_password", "")[:128]
        db = get_db()
        if not check_password_hash(g.user["password_hash"], current):
            flash("Your current password is incorrect.", "error")
        elif action == "change_password":
            new = request.form.get("new_password", "")
            problem = password_problem(new, g.user["email"], g.user["name"])
            if new != request.form.get("confirm_password", ""):
                flash("The new passwords do not match.", "error")
            elif problem:
                flash(problem, "error")
            else:
                db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                           (generate_password_hash(new), g.user["id"]))
                db.commit()
                flash("Password updated.", "success")
        elif action == "reset_progress":
            db.execute("DELETE FROM progress WHERE user_id = ?", (g.user["id"],))
            db.commit()
            flash("Your progress has been reset.", "success")
        elif action == "delete_account":
            db.execute("DELETE FROM users WHERE id = ?", (g.user["id"],))
            db.commit()
            session.clear()
            flash("Your account and all its data were deleted.", "success")
            return redirect(url_for("pages.landing"))
        return redirect(url_for("auth.account"))
    return render_template("account.html")
