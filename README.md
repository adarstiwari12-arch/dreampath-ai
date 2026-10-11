# DreamPath AI

AI-powered student skill and career intelligence platform. A student picks an engineering stream and a dream package (LPA), follows an ordered video curriculum, ticks lessons as they finish them, and the **Dream Meter** shows how close they are, with an AI mentor for what to do next.

Mini Project (BCC-351) · Group G1, CSE-1 · IMS Engineering College, Ghaziabad · Supervisor: Dr. Sonali Mathur

> **New here? Open [HOW_TO_RUN.md](HOW_TO_RUN.md)** for the full step-by-step guide. Quick start: `run.bat` (Windows) or `bash run.sh` (macOS / Linux), then open http://127.0.0.1:5000.

## Features

| Area | What it does |
| --- | --- |
| Landing page | Hero with a live Dream Meter demo, stream cards, how it works, tier table, FAQ |
| Stream previews | Public curriculum for each stream (`/streams/cse`) with depth-by-package, so visitors can look before signing up |
| Accounts | Register, log in, log out, change password, reset progress, delete account. Smooth redirects: sign-up from a stream page carries the stream into setup, and login returns you to the page you asked for |
| Setup | Three choices: stream, package slider mapped to four tiers, study pace. AI stream suggestion. Live plan summary with lessons, hours and finish date |
| My learning | "Continue learning" card, Dream Meter, lessons done, hours left, estimated finish date, phase progress, study-plan pace, streak, recently completed, AI gap analysis |
| Curriculum | Udemy-style collapsible sections, tick-able lessons, search, filter (all / to do / done), sort by learning path or points per hour, sticky progress sidebar |
| AI mentor | Chat with a context panel showing what the mentor sees. LLM when a key is set, otherwise deterministic rules from the student's own data |
| Faculty console | Verify, add, edit and delete lessons; student counts per stream |

Dream Meter % = (sum of weight of ticked lessons / sum of weight of all lessons) x 100. The score is plain arithmetic; AI never decides it.

## Tech stack

- **Backend:** Python 3.10+, Flask
- **Database:** SQLite (zero setup; the schema is plain SQL and ports to MySQL)
- **Frontend:** HTML, CSS and vanilla JavaScript. No build step, no CDNs, no external fonts. Responsive, light and dark themes, keyboard and screen-reader friendly
- **AI layer:** Anthropic Messages API over HTTPS (optional, with built-in fallback)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
flask --app app run --debug
```

Open http://127.0.0.1:5000. The database, 5 streams and 83 lessons are created on first start.

| Task | Command |
| --- | --- |
| Create a faculty account | `flask --app app create-faculty` |
| Reset a password / clear a lockout | `flask --app app reset-password` |
| Run the tests (66) | `python -m unittest discover -s tests -v` |
| Enable the AI mentor | put `ANTHROPIC_API_KEY=...` in `.env` and restart |

## Project structure

See the annotated file map in [HOW_TO_RUN.md](HOW_TO_RUN.md#part-6-what-each-file-does). In short: `dreampath/` holds the backend (`routes_*.py`, `meter.py`, `ai.py`, `security.py`, `db.py`, `catalog.py`, `seed.py`), `dreampath/templates/` one HTML file per page, and `dreampath/static/` the CSS and one JavaScript file per page.

## Security measures

- Passwords hashed with Werkzeug (scrypt); 8+ characters with a letter and a number
- Generic login errors, constant-time dummy hash for unknown emails, lockout after 5 failures for 15 minutes
- Session reset on login (prevents fixation); `HttpOnly`, `SameSite=Lax` and (in production) `Secure` cookies
- CSRF token on every state-changing request (forms and API)
- Content-Security-Policy with `script-src 'self'` and no inline scripts or styles, plus `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy` and HSTS over HTTPS
- Parameterised SQL everywhere; Jinja auto-escaping; JavaScript renders text with `textContent`
- Server-side validation of every input, request size limit, open-redirect protection on every `next` parameter, http(s)-only video links
- Role checks: students cannot reach faculty routes or tick lessons outside their stream or tier
- Rate limits on login, registration, AI and write endpoints (idle entries are evicted so memory stays bounded)
- Secrets only from the environment; the app refuses to start in production without `SECRET_KEY`; `.env` and the database are git-ignored
- AI: user text is sent as data with guard-rail prompts, input lengths are capped, the API key is never logged

## Known limits (be upfront about these in your viva)

- Rate limits are per client IP and kept in memory, so a whole lab behind one router shares a budget. They are generous (20 login attempts per 10 minutes); for several servers use Redis-backed limiting.
- SQLite is fine for a college deployment. Move to MySQL or PostgreSQL for heavy traffic. Schema changes are handled by a small migration step in `db.py`.
- Seeded lesson links are YouTube searches for each topic so they never break. Faculty can replace them with specific, verified videos.
- "Today" for streaks and finish dates uses India time by default. Change `UTC_OFFSET_MINUTES` in `.env` for another timezone.
- There is no email service, so password resets are done by an admin with `flask --app app reset-password`.
- Flask's built-in server is for development only.

## Deploying

```bash
pip install waitress
FLASK_ENV=production SECRET_KEY=<64 random hex chars> SESSION_COOKIE_SECURE=true \
  waitress-serve --port=8000 app:app
```

Serve it behind HTTPS (for example nginx or a managed platform). Generate a key with `python -c "import secrets; print(secrets.token_hex(32))"`. If a reverse proxy sits in front, also set `TRUST_PROXY=true` so rate limits use the real client IP (only when you control the proxy). `GET /healthz` is available for health checks.

## Push to GitHub

```bash
git init
git add .
git commit -m "DreamPath AI: full-stack learning platform"
git branch -M main
git remote add origin https://github.com/<your-username>/dreampath-ai.git
git push -u origin main
```

`.gitignore` already excludes `.env`, the database and `instance/`. A GitHub Actions workflow runs the tests on every push.
