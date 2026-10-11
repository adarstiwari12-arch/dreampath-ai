"""Configuration, loaded from environment variables (and an optional .env file)."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path = BASE_DIR / ".env") -> None:
    """Minimal .env reader so the project needs no extra dependency."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _secret_key(production: bool, instance_dir: Path) -> str:
    key = os.environ.get("SECRET_KEY", "").strip()
    if key:
        return key
    if production:
        raise RuntimeError("SECRET_KEY must be set when FLASK_ENV=production.")
    # Development: generate once and reuse so logins survive auto-reloads.
    instance_dir.mkdir(parents=True, exist_ok=True)
    key_file = instance_dir / ".secret_key"
    if not key_file.exists():
        key_file.write_text(secrets.token_hex(32), encoding="utf-8")
    return key_file.read_text(encoding="utf-8").strip()


def build_config() -> dict:
    load_dotenv()
    env = os.environ.get("FLASK_ENV", "development").lower()
    production = env == "production"
    instance_dir = BASE_DIR / "instance"
    db_path = Path(os.environ.get("DATABASE_PATH", "instance/dreampath.db"))
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path
    secure_cookie = os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true" or production
    return {
        "DEBUG": env == "development",
        "SECRET_KEY": _secret_key(production, instance_dir),
        "DATABASE": str(db_path),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": secure_cookie,
        "PERMANENT_SESSION_LIFETIME": 60 * 60 * 24 * 7,  # 7 days
        "MAX_CONTENT_LENGTH": 64 * 1024,  # 64 KB request bodies are plenty
        "RATELIMIT_ENABLED": True,
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        "LLM_MODEL": os.environ.get("LLM_MODEL", "claude-sonnet-5-5").strip(),
        # Set TRUST_PROXY=true only when running behind a reverse proxy you control
        # (nginx, a platform router). It makes rate limits use the real client IP.
        "TRUST_PROXY": os.environ.get("TRUST_PROXY", "").lower() == "true",
        # Minutes ahead of UTC used for "today" in streaks and finish dates (330 = India).
        "UTC_OFFSET_MINUTES": int(os.environ.get("UTC_OFFSET_MINUTES", "330")),
        "MAX_FAILED_LOGINS": 5,
        "LOCKOUT_MINUTES": 15,
    }
