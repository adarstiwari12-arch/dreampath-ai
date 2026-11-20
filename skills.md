# DreamPath AI — Skills & Tech Docs Reference

Compact skills matrix and up-to-date documentation references for AI agents working on DreamPath AI (Flask + vanilla frontend, SQLite).

## 1. Core skills required

| Skill area | What's needed | Used in |
|---|---|---|
| Python 3.10+ | venv, pip, packaging, stdlib | app.py, dreampath/ |
| Flask 3.x | app factory, routing, templates, CLI commands, sessions | dreampath/__init__.py, routes_*.py |
| HTML5 | semantic markup, forms, CSP-compatible templates | dreampath/templates/*.html |
| CSS3 | custom properties (design tokens), responsive grid/flex, dark mode, no build step | dreampath/static/css/app.css |
| Vanilla JavaScript ES6+ | DOM manipulation, fetch API, event handling, no frameworks | dreampath/static/js/*.js |
| SQLite | schema design, parameterised queries, migrations | dreampath/db.py, schema.sql |
| Web security | CSRF tokens, XSS prevention (textContent only), password hashing (scrypt), rate limiting, CSP headers | dreampath/security.py, routes_*.py |
| Accessibility | WCAG 2.1 AA, ARIA, keyboard navigation, focus management, reduced motion | core.js, app.css, templates |
| OpenAI-compatible LLM API (optional) | LLM integration with fallback rules; any provider (OpenRouter, Open Code, Together, Groq) | dreampath/ai.py |

## 2. Official tech documentation

- **Flask:** https://flask.palletsprojects.com/en/latest/ — routing, templates, CLI, sessions, testing
- **Werkzeug:** https://werkzeug.palletsprojects.com/en/latest/ — password hashing (`generate_password_hash`/`check_password_hash`), security
- **Jinja2:** https://jinja.palletsprojects.com/en/latest/ — template syntax, auto-escaping
- **Python:** https://docs.python.org/3/ — venv, stdlib, sqlite3 module
- **SQLite:** https://www.sqlite.org/docs.html — SQL syntax, parameterised queries
- **MDN Web Docs (HTML/CSS/JS):** https://developer.mozilla.org/ — reference for all web standards
- **Anthropic Messages API:** https://docs.anthropic.com/ — Messages API, model names, system prompts
- **OpenAI-compatible API providers:** OpenRouter (https://openrouter.ai), Open Code, Together, Groq — all use the `/chat/completions` endpoint with `Authorization: Bearer` header
- **WCAG 2.1:** https://www.w3.org/WAI/WCAG21/quickref/ — accessibility quick reference
- **CSP (Content Security Policy):** https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/ — web security baseline

## 3. Latest web design standards & practices (2026)

### Design tokens & CSS
- Use CSS custom properties (`--brand`, `--ink`, `--surface`, etc.) for theming — one variable set per color scheme (`[data-color-scheme="light"]` / `[data-color-scheme="dark"]`)
- No build step, no CDN, no external fonts — system font stack: `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- Fluid typography with `clamp()`; line-height ≥ 1.5; max-width container `min(1180px, 100% - 40px)`
- Breakpoints: 1040px (tablet), 820px (mobile nav), 560px (single column); mobile-first media queries
- `prefers-reduced-motion: reduce` disables animations; `min-width: 0` on grid children to prevent sideways scroll
- Tailwind-inspired utility classes compose directly in HTML (`.flex`, `.grid`, `.gap-4`, `.text-xs`, etc.)

### Accessibility (WCAG 2.1 AA)
- Skip-to-content link; visible `:focus-visible` rings; logical tab order
- `aria-label`, `aria-pressed`, `aria-current`, `aria-live="polite"` regions on dynamic content
- Decorative icons `aria-hidden`; screen-reader labels on icon-only buttons
- Contrast ≥ 4.5:1 normal text, ≥ 3:1 large text (AA); brand text uses readable token, not raw brand color
- `prefers-color-scheme` honored as default; toggle persisted to `localStorage` under `color-scheme`
- All dynamic text via `textContent` (never `innerHTML`) — XSS safe by design

### Responsive / mobile
- Touch targets ≥ 44px; stacked layout on mobile, grid on desktop
- `viewport` meta: `width=device-width, initial-scale=1`
- `scroll-padding-top` for sticky header; fixed aspect ratios on media

## 4. Security practices (built into project)

- Passwords hashed with Werkzeug scrypt; minimum 8 chars, letter + number
- Constant-time dummy hash for unknown emails; lockout after 5 failures for 15 min
- Session regenerated on login (fixation prevention); `HttpOnly`, `SameSite=Lax`, `Secure` in production
- CSRF token on every state-changing request (forms + JSON API)
- CSP: `script-src 'self'`; no inline scripts or styles; `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS over HTTPS
- Parameterised SQL everywhere; server-side validation of all inputs; request size limits; open-redirect protection on `next`; http(s)-only video links
- Rate limits on login, registration, AI, and write endpoints (in-memory, per IP)
- Secrets from environment only; app refuses to start in production without `SECRET_KEY`; `.env` and `instance/` git-ignored

## 5. Flask project structure skills

- App factory pattern (`create_app()` in `dreampath/__init__.py`)
- Blueprints / route modules: `routes_pages.py`, `routes_auth.py`, `routes_api.py`
- CLI commands: `create-faculty`, `reset-password`
- Template helpers and error pages in `__init__.py`
- Config from `.env` + environment via `config.py`
- Database: `db.py` connection + schema.sql + seed.py (5 streams, 83 lessons on first run)

## 6. AI mentor skills (optional)

- Provider: Any OpenAI-compatible endpoint (OpenRouter, Open Code, Together, Groq, …). Set `LLM_API_KEY`, `LLM_BASE_URL` (e.g. `https://openrouter.ai/api/v1`), `LLM_API_PATH` (`/chat/completions`), and `LLM_MODEL` in `.env`.
- Request: `POST {base_url}/chat/completions` with `Authorization: Bearer <key>`, JSON body `{model, messages, max_tokens, temperature}`.
- Response: `choices[0].message.content`.
- Guardrails: system prompt constrains to learning/career topics; user text as data only; input capped at 600 chars; key never logged.
- Rule-based fallback when no key or call fails — everything works without AI.

## 7. Running & testing skills

- Start: `run.bat` (Windows) / `bash run.sh` (macOS/Linux) / `flask --app app run --debug`
- Tests: `python -m unittest discover -s tests -v` (66 tests)
- Port 5000 default; use `--port 5001` if in use
- Debug mode prints full errors; debugger PIN shown on startup
