# DreamPath AI - Design Specification

**Project:** DreamPath AI — AI-powered student skill and career intelligence platform
**Mini Project (BCC-351) · Group G1, CSE-1 · IMS Engineering College, Ghaziabad**
**Supervisor:** Dr. Sonali Mathur

---

## 1. Design intent

DreamPath AI is a **professional, interactive learning platform for engineering students**, inspired by the polish and clarity of platforms like Udemy — but it is **not a copy**. It is an original product built around one idea: *every student picks a stream, sets a dream salary target (LPA), follows an ordered video roadmap, and watches a weighted Dream Meter move as they complete lessons.*

The design must feel trustworthy, focused on outcomes, and easy to use on a phone in a college lab or on a laptop at home.

### Non-goals
- Do not clone Udemy's visual identity, colour palette, or layout wholesale.
- Do not add bloated frameworks, build steps, CDNs, or external fonts.
- Do not let AI override anything that matters (the Dream Meter is plain arithmetic; AI only recommends).

---

## 2. Design principles

| Principle | What it means in practice |
|---|---|
| **Outcome first** | The Dream Meter and target package (LPA) are the most visible numbers on every student page. Progress is the hero, not decoration. |
| **Clarity over flash** | One clear action per screen. High contrast, generous whitespace, obvious buttons. |
| **Mobile-first** | Students browse on phones. Stack on mobile, grid on desktop, touch-friendly targets (44px+). |
| **Fast, no dependencies** | Vanilla HTML/CSS/JS. No CDNs, no external fonts, no build step. Loads instantly on slow college Wi-Fi. |
| **Accessible** | Keyboard navigable, screen-reader friendly, `prefers-reduced-motion` respected, high-contrast dark mode. |
| **AI as assistant, not authority** | The AI mentor suggests; the student decides. AI never changes scores or grades. |

---

## 3. Visual identity

### 3.1 Logo / brand mark
A **DP monogram** inside a rounded-square tile, with a small "path" line suggesting a roadmap and a dot for the destination/target package.

- File: `dreampath/static/img/logo.svg` (full wordmark + mark) and `dreampath/static/img/favicon.svg` (mark only).
- Used in: header, footer, auth pages, browser tab, meta theme-color.
- The wordmark "DreamPath" in a bold, geometric sans; "AI" accented in the brand colour.

### 3.2 Colour palette

Token | Light | Dark | Role
---|---|---|---
`--brand` | `#0ea5e9` | `#38bdf8` | Primary actions (bg, white text)
`--brand-hover` | `#0284c7` | `#7dd3fc` | Hover on brand elements
`--brand-soft` | `#e0f2fe` | `#0c4a6e` | Subtle brand backgrounds
`--on-brand` | `#ffffff` | `#0f172a` | Text on brand
`--brand-text` | `#0369a1` | `#60a5fa` | Brand used as text color
`--ink` | `#0f172a` | `#f8fafc` | Body text (primary)
`--muted` | `#64748b` | `#94a3b8` | Secondary text
`--ink-soft` | `#334155` | `#cbd5e1` | Tertiary text
`--surface` | `#ffffff` | `#1e293b` | Card backgrounds
`--surface-2` | `#f1f5f9` | `#334155` | Muted card/section backgrounds
`--bg` | `#f8fafc` | `#0f172a` | Page background
`--line` | `#cbd5e1` | `#334155` | Borders
`--line-strong` | `#94a3b8` | `#475569` | Stronger borders
`--accent` | `#f59e0b` | `#fbbf24` | Attention / pace
`--accent-text` | `#92400e` | `#fcd34d` | Accent text
`--accent-soft` | `#fef3c7` | `#451a03` | Accent backgrounds
`--success` | `#15803d` | `#4ade80` | Done / complete
`--success-soft` | `#dcfce7` | `#064e3b` | Done backgrounds
`--danger` | `#dc2626` | `#f87171` | Destructive actions
`--danger-soft` | `#fee2e2` | `#450a0a` | Danger backgrounds
`--info` | `#2563eb` | `#93c5fd` | Informational
`--info-soft` | `#dbeafe` | `#1e3a8a` | Info backgrounds

All primary text meets WCAG AA (4.5:1) or AAA (7:1) contrast against its background. Brand as a background color is always paired with white text; brand as text uses `--brand-text` for readability.

### 3.3 Per-stream colours
Each stream keeps a distinct accent so students can recognise their branch at a glance:

- CSE: `#3b4fd1` (indigo)
- ECE: `#0b7285` (teal)
- EEE: `#a8480a` (amber)
- MECH: `#6d3fc4` (purple)
- CIVIL: `#2b7a3b` (green)

### 3.4 Typography
System font stack only (no external fonts, no CDN, no build step): `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Noto Sans Devanagari", sans-serif`.

- Headings: bold, tight letter-spacing, `clamp()` fluid sizing.
- Body: 16px, line-height 1.625 (relaxed for readability).
- Type scale: `text-xs` through `text-3xl` utility classes.

---

## 4. Layout system

- Max-width container: `min(1180px, 100% - 40px)`.
- Header height: `64px`, sticky, with scroll padding.
- Breakpoints: `1040px` (tablet), `820px` (mobile nav), `560px` (single column).
- All grid children get `min-width: 0` to prevent sideways scroll on small screens.
- `prefers-reduced-motion: reduce` disables animations/transitions.

---

## 5. Page-by-page design

### 5.1 Landing page (public)
**Goal:** Convert a visitor into a registered student.

Sections (top to bottom):
1. **Hero** — eyebrow tag ("Free for engineering students"), H1 outcome headline, lead paragraph, two CTAs (primary "Start free", ghost "Browse streams"), three benefit ticks, live Dream Meter demo card on the right.
2. **Stat strip** — four big numbers: streams, lessons, hours, tiers.
3. **Choose your stream** — 5 stream cards (banner icon + name + tagline + lesson/hour badges), hover lift.
4. **How it works** — 5 numbered steps with icons.
5. **Dream Meter** — explanation + formula + tier table (Target / LPA range / Focus).
6. **Features** — 3 tiles: AI mentor & gap analysis, study plan & streaks, faculty verified & privacy first.
7. **FAQ** — accordion details.
8. **CTA band** — brand-coloured final call to action.

### 5.2 Auth pages (login / register)
Split layout: brand-coloured aside with value props + mini-ring preview; centred card with form. Password strength meter, clear inline errors, "Log in" / "Sign up free" toggle.

### 5.3 Setup (onboarding)
Three-step stepper (Stream → Package → Pace):
1. Stream pick grid (5 cards, AI "suggest a stream" assist box).
2. Package slider (3–60 LPA) with live tier pill highlight and value readout.
3. Pace chips (0.5–4 h/day).
Sticky summary bar at bottom with primary save button. Live plan summary updates as choices change.

### 5.4 Dashboard ("My learning")
- Welcome header + "Change plan" action.
- Continue card (stream banner + resume CTA).
- Stat grid: Dream Meter ring, lessons done, video hours left, estimated finish date.
- Two columns: "Your path" (phase list) + "AI gap analysis" (button triggers analysis).
- Aside: Study plan chips, streak, suggested mentor questions, recently completed list.

### 5.5 Curriculum / roadmap
- Collapsible phase sections (Udemy-style accordions), tick-able lessons.
- Toolbar: search, filter (All / To do / Done), sort (Learning path / Best value), Expand all.
- Sticky right sidebar: meter ring + "Up next" lesson card with watch link.
- Lesson rows: checkbox, title, weight, duration, verified badge.

### 5.6 AI Mentor
- Chat layout: conversation log (left, scrollable) + context panel (right, sticky-ish).
- Assistant bubbles vs user bubbles, typing state.
- "What your mentor sees" context list (stream, tier, meter, phases, hours left).
- Suggested question chips. Mode note shows LLM vs rules source.

### 5.7 Faculty console
- Lesson list table (verify/add/edit/delete), student counts per stream, action dialogs.

### 5.8 Account / error / footer
- Account: avatar, email, password change, delete account.
- Error: big code, friendly message, recovery actions.
- Footer: brand, stream links, platform links, project credits.

---

## 6. Interactive behaviour (JavaScript)

All interactivity is vanilla JS via `core.js` and per-page modules:

- **Dream Meter ring**: SVG circle that animates `stroke-dashoffset` as lessons are ticked.
- **Landing demo**: live checkbox list that updates the ring and percentage text in real time.
- **Setup**: stream select highlight, package slider updates tier pill + LPA value + summary text, pace chips update estimated finish date.
- **Dashboard**: gap-analysis button fetches AI analysis (LLM if key set, rules otherwise) and renders it; pace chips update finish estimate; streak flame animates.
- **Roadmap**: search filters lessons in place; filter segments toggle done/todo/all; sort reorders; expand all opens phases; ticking a lesson updates the sidebar meter instantly.
- **Mentor**: send/receive messages, auto-scroll, clear chat, suggested chips insert text.
- **Accessibility**: skip link, focus-visible rings, `aria-current`, `aria-pressed`, `aria-live` regions, `textContent` only (no `innerHTML`).

---

## 7. AI integration

- **Provider:** Any OpenAI-compatible endpoint (OpenRouter, Open Code, Together, Groq, …). Set `LLM_API_KEY`, `LLM_BASE_URL` (e.g. `https://openrouter.ai/api/v1`), `LLM_API_PATH` (`/chat/completions`), and `LLM_MODEL` in `.env`. `LLM_MODEL` defaults to `openrouter/auto`.
- **Fallback:** If no key is set or the call fails, deterministic rule-based answers are used from the student's own roadmap data. Everything works without a key.
- **Guardrails:** system prompt constrains the model to learning/career topics; user text is sent as data only; responses rendered with `textContent` (no HTML injection); input capped at 600 chars; key never logged.

To connect a free key: add `LLM_API_KEY=...`, `LLM_BASE_URL=...`, and `LLM_MODEL=...` to `.env` and restart the server. See `.env.example`.

---

## 8. Accessibility & performance targets

- Keyboard navigable everywhere; visible focus rings (`:focus-visible`).
- Screen-reader labels on icon-only buttons; `aria-live` on meter and flash areas.
- `prefers-color-scheme: dark` and `prefers-reduced-motion: reduce` supported.
- No external resources: zero CDN, zero external fonts, zero third-party scripts.
- Lighthouse-friendly: fast first paint, minimal CSS/JS, SVG icons inline.

---

## 9. File map (design-relevant)

| File | Purpose |
|---|---|
| `dreampath/static/img/logo.svg` | Full brand wordmark + mark |
| `dreampath/static/img/favicon.svg` | Browser tab / icon mark |
| `dreampath/templates/base.html` | Shell: header, footer, brand, theme-color |
| `dreampath/static/css/app.css` | Design tokens, layout, components, responsive |
| `dreampath/templates/landing.html` | Public home page |
| `dreampath/static/js/core.js` | Shared JS: API, DOM builder, meter ring, toasts |
| `dreampath/static/js/page-landing.js` | Landing Dream Meter demo |
| `.env` / `.env.example` | AI key configuration (`LLM_API_KEY`, `LLM_BASE_URL`) |

---

## 10. What "more than AI-generated" means here

- **Hand-written design system** with named tokens, not a framework output.
- **Original visual identity** (DP monogram, per-stream colours, outcome-led layout) — inspired by Udemy's clarity, not copied.
- **Real interactivity**: live meters, sliders that update tiers, collapsing curricula, sticky sidebars, chat with context.
- **College-project appropriate**: security (CSRF, hashed passwords, rate limits), accessibility, and honest AI fallbacks are built in, not bolted on.

---

## 11. Dark / light mode

The site supports a manual dark/light mode toggle in the header (sun/moon icon), persisted to `localStorage` under the key `color-scheme`.

**Implementation:**
- Theme is stored as `data-color-scheme="light"` or `data-color-scheme="dark"` on `<html>`.
- All colours are CSS variables that change per scheme — no duplicate stylesheets.
- On load, the saved preference is honoured; otherwise it follows `prefers-color-scheme`.
- No flash of wrong theme: the theme script runs at the top of `core.js` before the page paints.
- Toggle updates the attribute and `localStorage` instantly.

**Files:** `dreampath/static/css/app.css` (`[data-color-scheme="dark"]` overrides), `dreampath/static/js/core.js` (`initTheme`), `dreampath/templates/base.html` (theme-toggle button).

---

## 12. Tailwind-inspired utility class system

Because the project has **no build step and no CDN** (a deliberate choice for zero-dependency college deployment), `app.css` includes a hand-written utility layer that mirrors Tailwind's approach. Classes compose directly in HTML:

| Category | Example utilities |
|---|---|
| Display | `.flex`, `.flex-col`, `.grid`, `.hidden`, `.block`, `.inline-flex` |
| Layout | `.flex-1`, `.items-center`, `.justify-between`, `.gap-2/4/6`, `.min-w-0` |
| Spacing | `.p-2/4/6`, `.px-4`, `.py-2`, `.m-0`, `.mx-auto`, `.mb-4` |
| Sizing | `.w-full`, `.h-full` |
| Typography | `.text-xs`…`.text-3xl`, `.font-semibold/bold/extrabold`, `.leading-relaxed/tight`, `.tracking-wide`, `.uppercase`, `.italic`, `.text-left/center/right` |
| Colour | `.text-ink/muted/brand/success/danger/accent`, `.bg-brand/success-soft/danger-soft/accent-soft` |
| Borders | `.border`, `.border-brand`, `.rounded`, `.rounded-lg`, `.rounded-full` |
| Shadows | `.shadow`, `.shadow-lg`, `.shadow-card`, `.shadow-none` |
| Position | `.relative`, `.absolute`, `.sticky`, `.inset-0`, `.z-10/z-50` |

These utilities are used throughout templates alongside component classes, keeping markup readable and styling consistent without a build pipeline.

---

## 13. Web design guidelines followed

1. **Contrast first.** Every text/background pair meets WCAG AA (4.5:1) or AAA. Brand text uses `--brand-text` (not `--brand`) so it stays readable on light surfaces.
2. **One clear action per screen.** CTAs are primary (brand) or secondary (ghost); destructive actions use `--danger`.
3. **Mobile-first.** Stacks on mobile, grids on desktop; all touch targets ≥ 44px; responsive breakpoints at 1040px / 820px / 560px.
4. **No layout shift.** `min-width: 0` on grid children; fixed aspect ratios on media; `scroll-padding-top` for the sticky header.
5. **Reduced motion.** `prefers-reduced-motion` disables all animations/transitions.
6. **Keyboard first.** Visible `:focus-visible` rings, `aria-current`, `aria-pressed`, skip link, logical tab order.
7. **No inline styles.** All styling via classes (satisfies the site's CSP `style-src 'self'` and the security test).
8. **Progressive enhancement.** AI mentor falls back to rules without an API key; site is fully usable with JS disabled for core navigation.

---

## 14. Accessibility standards

- Skip-to-content link (`#main`) for keyboard users.
- Screen-reader labels on all icon-only buttons; `aria-hidden` on decorative icons.
- `aria-live="polite"` regions for meter updates and flash messages.
- `prefers-color-scheme` respected as default theme source.
- High-contrast mode tokens for both light and dark schemes.
- Focus-visible rings on every interactive element.
- All dynamic text inserted via `textContent` (no `innerHTML`) — XSS safe by design.

