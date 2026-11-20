# DreamPath AI — Project Description

## Overview
DreamPath AI is an AI-powered student skill & career intelligence platform (Flask backend, vanilla HTML/CSS/JS frontend, SQLite DB). It is a college mini project (BCC-351 · Group G1 · IMS Engineering College, Ghaziabad). No build step, no CDNs, no external fonts.

## Core idea
A student picks an engineering stream, sets a dream salary target (LPA), follows an ordered video roadmap, and watches a weighted Dream Meter move as they tick lessons complete. AI only recommends — it never decides scores/grades.

## Tech stack
- **Backend:** Python 3.10+, Flask (entry: `app.py`, factory in `dreampath/__init__.py`)
- **Database:** SQLite (`instance/dreampath.db`, schema in `dreampath/schema.sql`)
- **Frontend:** HTML + CSS + vanilla JS (no build step/CDN/external fonts), system font stack
- **AI:** Optional OpenAI-compatible LLM provider (OpenRouter, Open Code, Together, Groq, …) via `.env` `LLM_API_KEY` + `LLM_BASE_URL`; deterministic rule-based fallback if no key
- **Config:** `.env` (copied from `.env.example`); never committed
- **Deploy:** Flask dev server `flask --app app run --debug` (port 5000) or waitress for production

## Quick start (Windows)
```
run.bat
```
then open `http://127.0.0.1:5000`

Manual:
```
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
flask --app app run --debug
```

## Directory layout
```
dreampath/             # application package
  __init__.py          # app factory, error pages, template helpers
  config.py            # settings from .env / environment
  db.py                # SQLite connection, setup, CLI tools (create-faculty, reset-password)
  schema.sql           # database tables
  seed.py              # 5 streams + 83 lessons (seeded on first run)
  catalog.py           # lesson counts & curriculum queries
  meter.py             # Dream Meter, tiers, finish-date, streak math
  ai.py                # AI mentor, gap analysis, stream suggestion (+ fallback rules)
  security.py          # CSRF, security headers, rate limiting, validation
  icons.py             # inline SVG icons
  routes_pages.py      # page URLs (/, /dashboard, /roadmap, ...)
  routes_auth.py       # register, login, logout, account
  routes_api.py        # JSON API (/api/...)
  templates/           # one HTML per page + base.html
  static/
    css/app.css        # design tokens + Tailwind-inspired utilities
    img/logo.svg, favicon.svg
    js/core.js, page-landing.js, page-auth.js, page-setup.js,
       page-dashboard.js, page-roadmap.js, page-mentor.js, page-faculty.js
app.py                 # Flask entry point
run.bat / run.sh       # one-command start
requirements.txt       # Flask>=3, gunicorn, setuptools
.env.example           # settings template
tests/test_app.py      # 66 unit tests
instance/              # created on first run: SQLite DB (git-ignored)
```

## Key features
- Landing page with live Dream Meter demo, 5 stream cards (CSE/ECE/EEE/MECH/CIVIL), tier table
- Auth: register/login/logout/account (scrypt-hashed passwords, lockout after 5 failures, CSRF)
- Setup: stream pick → package slider (3–60 LPA → 4 tiers) → pace chips (0.5–4 h/day)
- Dashboard: Dream Meter ring, lessons done, hours left, finish date, streak, AI gap analysis
- Curriculum: Udemy-style collapsible phases, tick-able lessons, search/filter/sort, sticky sidebar
- AI Mentor: chat with context panel; LLM when key set, rules otherwise
- Faculty console: verify/add/edit/delete lessons, student counts per stream
- Dark/light mode toggle (persisted in `localStorage`)
- Security: parameterised SQL, Jinja auto-escape, CSP, HSTS, rate limits, open-redirect protection

## Running tests
```
python -m unittest discover -s tests -v   # 66 tests
```

## Env vars (`.env`)
`FLASK_ENV`, `SECRET_KEY`, `DATABASE_PATH`, `SESSION_COOKIE_SECURE`, `UTC_OFFSET_MINUTES` (330 = IST), `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_API_PATH`, `LLM_MODEL`

## Notes for AI agents
- Dream Meter = sum of weight of ticked lessons / sum of all lesson weights × 100 (plain arithmetic, not AI)
- CSP `script-src 'self'` + no inline styles — all styling via classes, text via `textContent`
- All state-changing requests carry CSRF tokens
- Port 5000 default; change via `--port` if in use
- `.env` and `instance/` are git-ignored; never commit them
