"""Security helpers: CSRF protection, response headers, rate limiting, validation."""
import hmac
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from functools import wraps
from urllib.parse import urlparse

from flask import abort, current_app, request, session

# ---------------------------------------------------------------- CSRF

def csrf_token() -> str:
    token = session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token
    return token


def init_security(app) -> None:
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def _verify_csrf():
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return
        sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
        expected = session.get("csrf", "")
        if not expected or not hmac.compare_digest(sent.encode(), expected.encode()):
            abort(400, "Your session expired or the request was invalid. Please refresh and try again.")

    @app.after_request
    def _security_headers(resp):
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; "
            "form-action 'self'; frame-ancestors 'none'",
        )
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if current_app.config.get("SESSION_COOKIE_SECURE"):
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if not request.path.startswith("/static/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

# ---------------------------------------------------------------- rate limiting


class RateLimiter:
    """Sliding-window limiter kept in memory.

    Good enough for a single server process. Behind several workers or servers,
    swap this for Redis (or Flask-Limiter with a Redis backend).
    """

    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > 5000:  # drop idle keys so memory cannot grow unbounded
                self._hits = defaultdict(deque, {k: v for k, v in self._hits.items() if v and now - v[-1] <= 3600})
            hits = self._hits[key]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def rate_limit(limit: int, window: int, scope: str | None = None, methods=("POST", "PUT", "DELETE")):
    """Limit `limit` requests per `window` seconds per client IP and scope."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_app.config.get("RATELIMIT_ENABLED", True) and request.method in methods:
                key = f"{scope or request.endpoint}:{request.remote_addr}"
                if not limiter.allow(key, limit, window):
                    abort(429, "Too many requests. Please wait a moment and try again.")
            return view(*args, **kwargs)

        return wrapped

    return decorator

# ---------------------------------------------------------------- validation

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")
_COMMON_PASSWORDS = {
    "password", "password1", "password123", "12345678", "123456789", "qwerty123",
    "iloveyou1", "admin123", "welcome1", "letmein123", "abc12345",
}


def valid_email(email: str) -> bool:
    return bool(email) and len(email) <= 254 and bool(_EMAIL_RE.match(email))


def valid_name(name: str) -> bool:
    """2-80 printable characters starting with a letter; any script is allowed.

    Combining marks (for example Devanagari vowel signs) are not alphanumeric in
    Python, so a strict word-character pattern would reject names like "आयुष". Instead we
    block markup and control characters, and Jinja escapes the name on output.
    """
    if not 2 <= len(name) <= 80 or not name[0].isalpha():
        return False
    return name.isprintable() and not re.search(r"[<>{}\\/\"`$]", name)


def password_problem(password: str, email: str = "", name: str = "") -> str | None:
    """Return a human-readable problem with the password, or None if it is fine."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must be 128 characters or fewer."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must contain at least one letter and one number."
    lowered = password.lower()
    if lowered in _COMMON_PASSWORDS:
        return "That password is too common. Please choose another."
    if email and lowered == email.lower():
        return "Password must not be the same as your email."
    if name and len(name) >= 4 and name.lower().replace(" ", "") in lowered.replace(" ", ""):
        return "Password must not contain your name."
    return None


def safe_next(target: str | None, default: str = "/dashboard") -> str:
    """Only allow same-site relative redirects (prevents open redirects)."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return default
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return default
    return target


def valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc) and len(url) <= 500
