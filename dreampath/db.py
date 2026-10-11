"""SQLite access, schema creation and command-line helpers."""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

from .security import password_problem, valid_email
from .seed import seed_streams_and_steps


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")  # readers and a writer can work together
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    """Create tables (idempotent) and load seed data on first run."""
    Path(current_app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    migrate(conn)
    seed_streams_and_steps(conn)
    conn.commit()


def migrate(conn) -> None:
    """Add columns introduced after the first release to existing databases."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    if "daily_hours" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN daily_hours REAL NOT NULL DEFAULT 1.5")


def init_app(app) -> None:
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and seed streams and roadmap steps."""
        init_db()
        click.echo("Database ready.")

    @app.cli.command("create-faculty")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_faculty(name, email, password):
        """Create a faculty account (can verify and edit roadmap steps)."""
        email = email.strip().lower()
        if not valid_email(email):
            raise click.ClickException("That email address is not valid.")
        problem = password_problem(password, email, name)
        if problem:
            raise click.ClickException(problem)
        conn = get_db()
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise click.ClickException("An account with that email already exists.")
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'faculty')",
            (name.strip(), email, generate_password_hash(password)),
        )
        conn.commit()
        click.echo(f"Faculty account created for {email}.")

    @app.cli.command("reset-password")
    @click.option("--email", prompt=True)
    @click.password_option()
    def reset_password(email, password):
        """Set a new password for any account (use when someone is locked out)."""
        email = email.strip().lower()
        conn = get_db()
        user = conn.execute("SELECT name FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            raise click.ClickException("No account with that email.")
        problem = password_problem(password, email, user["name"])
        if problem:
            raise click.ClickException(problem)
        conn.execute(
            "UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL WHERE email = ?",
            (generate_password_hash(password), email),
        )
        conn.commit()
        click.echo(f"Password updated for {email}.")
