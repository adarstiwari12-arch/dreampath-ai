PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS streams (
    id          INTEGER PRIMARY KEY,
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    tagline     TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'faculty')),
    stream_id       INTEGER REFERENCES streams(id) ON DELETE SET NULL,
    target_lpa      REAL CHECK (target_lpa IS NULL OR (target_lpa >= 1 AND target_lpa <= 100)),
    daily_hours     REAL NOT NULL DEFAULT 1.5,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS steps (
    id           INTEGER PRIMARY KEY,
    stream_id    INTEGER NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    phase        INTEGER NOT NULL CHECK (phase BETWEEN 1 AND 5),
    position     INTEGER NOT NULL DEFAULT 0,
    title        TEXT NOT NULL,
    url          TEXT NOT NULL,
    duration_min INTEGER NOT NULL CHECK (duration_min > 0),
    weight       INTEGER NOT NULL CHECK (weight BETWEEN 1 AND 10),
    min_tier     INTEGER NOT NULL DEFAULT 0 CHECK (min_tier BETWEEN 0 AND 3),
    verified     INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0, 1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_steps_stream ON steps(stream_id, phase, position);

CREATE TABLE IF NOT EXISTS progress (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    step_id      INTEGER NOT NULL REFERENCES steps(id) ON DELETE CASCADE,
    completed_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, step_id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id, id);
