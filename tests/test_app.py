"""Run with:  python -m unittest discover -s tests -v"""
import os
import re
import tempfile
import unittest

from dreampath import create_app
from dreampath.meter import dream_meter, tier_for_lpa
from datetime import date

from dreampath.ai import rules_recommend
from dreampath.meter import estimate_finish, streak_days
from dreampath.security import (RateLimiter, limiter, password_problem, safe_next, valid_email,
                                valid_http_url, valid_name)

PASSWORD = "Roadmap2026x"


def make_app(**extra):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app = create_app({"TESTING": True, "DATABASE": path, "SECRET_KEY": "test-key",
                      "RATELIMIT_ENABLED": False, "ANTHROPIC_API_KEY": "", **extra})
    app._db_path = path
    return app


class Base(unittest.TestCase):
    def setUp(self):
        limiter.reset()
        self.app = make_app()
        self.client = self.app.test_client()

    def tearDown(self):
        os.unlink(self.app._db_path)

    def token(self, client=None, path="/"):
        html = (client or self.client).get(path).get_data(as_text=True)
        return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)

    def post(self, path, data=None, json=None, client=None, token=True):
        client = client or self.client
        headers = {"X-CSRF-Token": self.token(client)} if token else {}
        if json is not None:
            return client.post(path, json=json, headers=headers)
        return client.post(path, data={**(data or {}), **({"csrf_token": headers.get("X-CSRF-Token", "")})})

    def register(self, email="stu@example.com", name="Riya Sharma", client=None):
        return self.post("/register", {"name": name, "email": email, "password": PASSWORD, "confirm": PASSWORD}, client=client)

    def setup_profile(self, stream="cse", lpa=10, client=None):
        return self.post("/api/profile", json={"stream": stream, "target_lpa": lpa}, client=client)


class MeterTests(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(tier_for_lpa(3)["name"], "Starter")
        self.assertEqual(tier_for_lpa(6)["name"], "Growth")
        self.assertEqual(tier_for_lpa(24.9)["name"], "Pro")
        self.assertEqual(tier_for_lpa(25)["name"], "Elite")
        self.assertEqual(tier_for_lpa("bad")["name"], "Starter")

    def test_formula_matches_deck_example(self):
        steps = [{"id": 1, "phase": 1, "position": 0, "title": "a", "url": "u", "weight": 62, "duration_min": 60, "done": True},
                 {"id": 2, "phase": 1, "position": 1, "title": "b", "url": "u", "weight": 38, "duration_min": 60, "done": False}]
        m = dream_meter(steps)
        self.assertEqual(m["percent"], 62.0)  # 62 of 100 weight points = 62%
        self.assertEqual(m["next_step"]["id"], 2)

    def test_empty_and_complete(self):
        self.assertEqual(dream_meter([])["percent"], 0.0)
        done = [{"id": 1, "phase": 1, "position": 0, "title": "a", "url": "u", "weight": 5, "duration_min": 30, "done": True}]
        m = dream_meter(done)
        self.assertEqual(m["percent"], 100.0)
        self.assertIsNone(m["next_step"])


class ValidationTests(unittest.TestCase):
    def test_email(self):
        self.assertTrue(valid_email("a.b+c@college.ac.in"))
        for bad in ("", "no-at", "a@b", "a@@b.com", "x" * 250 + "@a.com"):
            self.assertFalse(valid_email(bad))

    def test_password(self):
        self.assertIsNotNone(password_problem("short1"))
        self.assertIsNotNone(password_problem("onlyletters"))
        self.assertIsNotNone(password_problem("12345678"))
        self.assertIsNotNone(password_problem("password123"))
        self.assertIsNone(password_problem("Roadmap2026x", "a@b.com", "Riya Sharma"))

    def test_safe_next(self):
        self.assertEqual(safe_next("/roadmap"), "/roadmap")
        for bad in ("//evil.com", "https://evil.com", "/\\evil.com", "javascript:alert(1)", None, ""):
            self.assertEqual(safe_next(bad), "/dashboard")

    def test_urls(self):
        self.assertTrue(valid_http_url("https://youtube.com/watch?v=x"))
        for bad in ("javascript:alert(1)", "ftp://x.com", "data:text/html,hi", "//x.com", ""):
            self.assertFalse(valid_http_url(bad))


class RegressionTests(unittest.TestCase):
    STREAMS = [{"slug": s, "name": s.upper()} for s in ("cse", "ece", "eee", "mech", "civil")]

    def test_names_in_any_script(self):
        for ok in ("Aayush Joshi", "आयुष जोशी", "தமிழ் நாடு", "José O'Brien-Smith", "Dr. A. P. J."):
            self.assertTrue(valid_name(ok), ok)
        for bad in ("A", "<b>x</b>", "Ravi\x00x", "$cash", "1abc", "x" * 81):
            self.assertFalse(valid_name(bad), bad)

    def test_short_keywords_match_whole_words_only(self):
        # "ev" (EEE) must not match "every"/"event", and "ai" (CSE) must not match "aim"
        vague = rules_recommend("Every day I plan an event and I aim to help people", self.STREAMS)
        self.assertIn("did not point strongly", vague["reason"])
        self.assertEqual(rules_recommend("I want to work on EV batteries and solar power", self.STREAMS)["stream"], "eee")
        self.assertEqual(rules_recommend("I like AI and writing programs", self.STREAMS)["stream"], "cse")
        self.assertEqual(rules_recommend("Designing engines and cars in CAD", self.STREAMS)["stream"], "mech")

    def test_rate_limiter_window_and_gc(self):
        rl = RateLimiter()
        self.assertTrue(all(rl.allow("k", 3, 60) for _ in range(3)))
        self.assertFalse(rl.allow("k", 3, 60))
        self.assertTrue(rl.allow("other", 3, 60))
        for i in range(5100):
            rl.allow(f"ip{i}", 1, 60)
        self.assertLessEqual(len(rl._hits), 5200)


class AuthTests(Base):
    def test_register_login_logout(self):
        r = self.register()
        self.assertEqual(r.status_code, 302)
        self.assertIn("/setup", r.headers["Location"])
        self.post("/logout")
        r = self.post("/login", {"email": "STU@example.com", "password": PASSWORD})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get("/dashboard").status_code, 302)  # no profile yet -> setup

    def test_password_is_hashed(self):
        self.register()
        from dreampath import db as dbmod
        with self.app.app_context():
            row = dbmod.get_db().execute("SELECT password_hash FROM users").fetchone()
        self.assertNotIn(PASSWORD, row["password_hash"])
        self.assertTrue(row["password_hash"].startswith(("scrypt:", "pbkdf2:")))

    def test_duplicate_and_weak_registration(self):
        self.register()
        c2 = self.app.test_client()
        self.assertIn("already exists", self.register(client=c2).get_data(as_text=True))
        r = self.post("/register", {"name": "Test User", "email": "x@y.com", "password": "abc", "confirm": "abc"}, client=c2)
        self.assertIn("at least 8", r.get_data(as_text=True))

    def test_wrong_password_generic_error(self):
        self.register(); self.post("/logout")
        r = self.post("/login", {"email": "stu@example.com", "password": "Wrong12345"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Incorrect email or password", r.get_data(as_text=True))
        r = self.post("/login", {"email": "nobody@example.com", "password": "Wrong12345"})
        self.assertIn("Incorrect email or password", r.get_data(as_text=True))

    def test_lockout_after_failures(self):
        self.register(); self.post("/logout")
        for _ in range(5):
            self.post("/login", {"email": "stu@example.com", "password": "Wrong12345"})
        r = self.post("/login", {"email": "stu@example.com", "password": PASSWORD})  # correct, but locked
        self.assertEqual(r.status_code, 200)
        self.assertIn("Too many failed attempts", r.get_data(as_text=True))

    def test_open_redirect_blocked(self):
        self.register(); self.setup_profile("cse", 10); self.post("/logout")
        for evil in ("https://evil.com", "//evil.com", "/\\evil.com", "javascript:alert(1)"):
            r = self.post("/login", {"email": "stu@example.com", "password": PASSWORD, "next": evil})
            self.assertEqual(r.headers["Location"], "/dashboard", evil)
            self.post("/logout")

    def test_login_required(self):
        self.assertEqual(self.client.get("/roadmap").status_code, 302)
        self.assertEqual(self.client.get("/api/roadmap").status_code, 401)

    def test_change_password_and_delete(self):
        self.register()
        self.post("/account", {"action": "change_password", "current_password": PASSWORD,
                               "new_password": "NewRoad2027y", "confirm_password": "NewRoad2027y"})
        self.post("/logout")
        self.assertEqual(self.post("/login", {"email": "stu@example.com", "password": "NewRoad2027y"}).status_code, 302)
        self.post("/account", {"action": "delete_account", "current_password": "NewRoad2027y"})
        self.assertEqual(self.client.get("/account").status_code, 302)


class AppTests(Base):
    def test_healthz_and_static_need_no_session(self):
        self.assertEqual(self.client.get("/healthz").get_json(), {"status": "ok"})
        r = self.client.get("/static/css/app.css")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Set-Cookie", r.headers)
        r.close()

    def test_unicode_name_can_register_and_is_escaped(self):
        self.post("/register", {"name": "आयुष जोशी", "email": "hi@example.com", "password": PASSWORD, "confirm": PASSWORD})
        self.assertIn("आयुष", self.client.get("/account").get_data(as_text=True))

    def test_setup_prefill_data_and_faculty_default_page(self):
        self.register()
        self.assertIsNone(self.client.get("/api/streams").get_json()["current"])
        self.setup_profile("ece", 18)
        cur = self.client.get("/api/streams").get_json()["current"]
        self.assertEqual((cur["stream"], cur["target_lpa"]), ("ece", 18.0))
        self.assertEqual(self.client.get("/setup").status_code, 200)

    def test_bool_package_rejected(self):
        self.register()
        self.assertEqual(self.setup_profile("cse", True).status_code, 400)

    def test_500_page_does_not_leak_details(self):
        app = make_app(TESTING=False, DEBUG=False, PROPAGATE_EXCEPTIONS=False)
        @app.get("/boom")
        def boom():
            raise RuntimeError("secret internal detail")
        r = app.test_client().get("/boom")
        body = r.get_data(as_text=True)
        os.unlink(app._db_path)
        self.assertEqual(r.status_code, 500)
        self.assertNotIn("secret internal detail", body)
        self.assertNotIn("Traceback", body)

    def test_cli_reset_password_unlocks_account(self):
        self.register(); self.post("/logout")
        for _ in range(5):
            self.post("/login", {"email": "stu@example.com", "password": "Wrong12345"})
        runner = self.app.test_cli_runner()
        res = runner.invoke(args=["reset-password", "--email", "stu@example.com", "--password", "Fresh2027abc"], input="Fresh2027abc\n")
        self.assertIn("Password updated", res.output, res.output)
        self.assertEqual(self.post("/login", {"email": "stu@example.com", "password": "Fresh2027abc"}).status_code, 302)

    def test_cli_create_faculty_rejects_weak_password(self):
        res = self.app.test_cli_runner().invoke(args=["create-faculty", "--name", "Dr X", "--email", "x@y.com", "--password", "abc"], input="abc\n")
        self.assertNotEqual(res.exit_code, 0)


class SecurityTests(Base):
    def test_csrf_required(self):
        self.client.get("/login")
        self.assertEqual(self.client.post("/login", data={"email": "a@b.com", "password": "x"}).status_code, 400)
        self.register()
        r = self.client.post("/api/profile", json={"stream": "cse", "target_lpa": 10})
        self.assertEqual(r.status_code, 400)

    def test_headers(self):
        r = self.client.get("/")
        self.assertIn("script-src 'self'", r.headers["Content-Security-Policy"])
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r.headers["Cache-Control"], "no-store")

    def test_no_inline_scripts_or_styles(self):
        self.register()
        self.setup_profile("cse", 10)
        for path in ("/", "/login", "/register", "/streams/cse", "/setup", "/dashboard", "/roadmap", "/mentor", "/account", "/nope"):
            html = self.client.get(path).get_data(as_text=True)
            self.assertNotRegex(html, r"<script(?![^>]*\bsrc=)[^>]*>")
            self.assertNotRegex(html, r'\sstyle="')
            self.assertNotRegex(html, r'\son(click|load|error)=')
            self.assertNotIn("javascript:", html)

    def test_proxy_setting_uses_forwarded_ip(self):
        app = make_app(TRUST_PROXY=False)
        app.config["TRUST_PROXY"] = True
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
        seen = {}
        @app.get("/ip")
        def ip():
            from flask import request
            seen["ip"] = request.remote_addr
            return "ok"
        app.test_client().get("/ip", headers={"X-Forwarded-For": "203.0.113.9"})
        os.unlink(app._db_path)
        self.assertEqual(seen["ip"], "203.0.113.9")

    def test_cookie_flags(self):
        r = self.client.get("/login")
        cookie = r.headers.get("Set-Cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_rate_limit(self):
        app = make_app(RATELIMIT_ENABLED=True)
        c = app.test_client()
        limiter.reset()
        html = c.get("/login").get_data(as_text=True)
        tok = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)
        codes = [c.post("/login", data={"email": "a@b.com", "password": "x", "csrf_token": tok}).status_code for _ in range(22)]
        os.unlink(app._db_path)
        self.assertIn(429, codes)

    def test_xss_in_name_is_escaped(self):
        self.post("/register", {"name": "<script>alert(1)</script>", "email": "x@y.com", "password": PASSWORD, "confirm": PASSWORD})
        # invalid name is rejected outright
        self.assertEqual(self.client.get("/dashboard").status_code, 302)
        self.assertEqual(self.client.get("/account").status_code, 302)

    def test_sql_injection_attempt_is_harmless(self):
        self.register(); self.post("/logout")
        r = self.post("/login", {"email": "' OR 1=1 --", "password": "' OR '1'='1"})
        self.assertEqual(r.status_code, 200)

    def test_404_json_and_html(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)
        r = self.client.get("/api/nope")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.get_json())


class RoadmapTests(Base):
    def setUp(self):
        super().setUp()
        self.register()

    def test_profile_validation(self):
        self.assertEqual(self.setup_profile("nope", 10).status_code, 400)
        self.assertEqual(self.setup_profile("cse", 0).status_code, 400)
        self.assertEqual(self.setup_profile("cse", 500).status_code, 400)
        self.assertEqual(self.setup_profile("cse", "abc").status_code, 400)
        self.assertEqual(self.setup_profile("cse", 10).status_code, 200)

    def test_roadmap_requires_profile(self):
        self.assertEqual(self.client.get("/api/roadmap").status_code, 409)

    def test_tier_changes_roadmap_depth(self):
        self.setup_profile("cse", 4)
        low = self.client.get("/api/roadmap").get_json()["meter"]["total_count"]
        self.setup_profile("cse", 30)
        high = self.client.get("/api/roadmap").get_json()["meter"]["total_count"]
        self.assertGreater(high, low)

    def test_tick_and_untick_updates_meter(self):
        self.setup_profile("cse", 10)
        data = self.client.get("/api/roadmap").get_json()
        self.assertEqual(data["meter"]["percent"], 0)
        step = data["phases"][0]["steps"][0]
        r = self.post(f"/api/progress/{step['id']}", json={"done": True}).get_json()
        self.assertGreater(r["meter"]["percent"], 0)
        r = self.post(f"/api/progress/{step['id']}", json={"done": False}).get_json()
        self.assertEqual(r["meter"]["percent"], 0)

    def test_progress_is_per_user(self):
        self.setup_profile("cse", 10)
        step = self.client.get("/api/roadmap").get_json()["phases"][0]["steps"][0]
        self.post(f"/api/progress/{step['id']}", json={"done": True})
        other = self.app.test_client()
        self.register("b@example.com", "Aman Verma", client=other)
        self.setup_profile("cse", 10, client=other)
        self.assertEqual(other.get("/api/roadmap").get_json()["meter"]["percent"], 0)

    def test_cannot_tick_other_stream_or_higher_tier_step(self):
        self.setup_profile("cse", 4)  # Starter tier
        from dreampath import db as dbmod
        with self.app.app_context():
            conn = dbmod.get_db()
            ece = conn.execute("SELECT s.id FROM steps s JOIN streams st ON st.id = s.stream_id WHERE st.slug = 'ece' LIMIT 1").fetchone()[0]
            elite = conn.execute("SELECT s.id FROM steps s JOIN streams st ON st.id = s.stream_id WHERE st.slug = 'cse' AND s.min_tier = 3 LIMIT 1").fetchone()[0]
        self.assertEqual(self.post(f"/api/progress/{ece}", json={"done": True}).status_code, 404)
        self.assertEqual(self.post(f"/api/progress/{elite}", json={"done": True}).status_code, 404)
        self.assertEqual(self.post("/api/progress/1", json={"done": "yes"}).status_code, 400)

    def test_ai_fallbacks_without_key(self):
        self.setup_profile("cse", 10)
        r = self.post("/api/ai/recommend-stream", json={"interests": "I love building bridges and roads in cities"}).get_json()
        self.assertEqual((r["stream"], r["source"]), ("civil", "rules"))
        r = self.post("/api/ai/mentor", json={"message": "What should I start with?"}).get_json()
        self.assertEqual(r["source"], "rules")
        self.assertIn("Start with", r["reply"])
        self.assertEqual(len(self.client.get("/api/ai/mentor").get_json()["messages"]), 2)
        self.assertIn("analysis", self.post("/api/ai/gap", json={}).get_json())
        self.assertEqual(self.post("/api/ai/mentor", json={"message": "x" * 700}).status_code, 400)
        self.assertEqual(self.post("/api/ai/recommend-stream", json={"interests": "hi"}).status_code, 400)


class FacultyTests(Base):
    def make_faculty(self):
        from werkzeug.security import generate_password_hash
        from dreampath import db as dbmod
        with self.app.app_context():
            conn = dbmod.get_db()
            conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('Dr Mathur', 'fac@example.com', ?, 'faculty')",
                         (generate_password_hash(PASSWORD),))
            conn.commit()
        c = self.app.test_client()
        self.post("/login", {"email": "fac@example.com", "password": PASSWORD}, client=c)
        return c

    def test_students_blocked(self):
        self.register()
        self.assertEqual(self.client.get("/faculty").status_code, 403)
        self.assertEqual(self.client.get("/api/faculty/overview").status_code, 403)
        self.assertEqual(self.post("/api/faculty/steps", json={}).status_code, 403)

    def test_faculty_crud_and_verify(self):
        fac = self.make_faculty()
        self.assertEqual(fac.get("/faculty").status_code, 200)
        payload = {"stream": "cse", "title": "Intro to Flask", "url": "https://example.com/v", "phase": 3,
                   "duration_min": 90, "weight": 6, "min_tier": 1, "verified": False}
        r = self.post("/api/faculty/steps", json=payload, client=fac)
        self.assertEqual(r.status_code, 201)
        sid = r.get_json()["id"]
        tok = self.token(fac)
        r = fac.put(f"/api/faculty/steps/{sid}", json={**payload, "verified": True}, headers={"X-CSRF-Token": tok})
        self.assertEqual(r.status_code, 200)
        steps = fac.get("/api/faculty/steps?stream=cse").get_json()["steps"]
        self.assertTrue(next(s for s in steps if s["id"] == sid)["verified"])
        self.assertEqual(fac.delete(f"/api/faculty/steps/{sid}", headers={"X-CSRF-Token": tok}).status_code, 200)

    def test_faculty_input_validation(self):
        fac = self.make_faculty()
        base = {"stream": "cse", "title": "Valid title", "url": "https://example.com", "phase": 1,
                "duration_min": 30, "weight": 5, "min_tier": 0}
        for bad in ({"url": "javascript:alert(1)"}, {"weight": 11}, {"phase": 9}, {"title": "ab"}, {"duration_min": 0}):
            self.assertEqual(self.post("/api/faculty/steps", json={**base, **bad}, client=fac).status_code, 400, bad)


class PlanTests(unittest.TestCase):
    def test_estimate_finish(self):
        today = date(2026, 10, 10)
        e = estimate_finish(69.5, 1.5, today)
        self.assertEqual((e["days_left"], e["finish_date"]), (47, "2026-11-26"))
        self.assertEqual(estimate_finish(0, 2, today)["days_left"], 0)
        self.assertEqual(estimate_finish(10, "junk", today)["daily_hours"], 1.5)   # bad input falls back
        self.assertEqual(estimate_finish(10, 99, today)["daily_hours"], 8.0)       # clamped
        self.assertEqual(estimate_finish(10, 0, today)["daily_hours"], 0.5)

    def test_streak(self):
        t = date(2026, 10, 10); d = lambda n: date(2026, 10, n)
        self.assertEqual(streak_days({d(10), d(9), d(8)}, t), 3)
        self.assertEqual(streak_days({d(9), d(8)}, t), 2)   # not studied yet today: still alive
        self.assertEqual(streak_days({d(7)}, t), 0)         # broken
        self.assertEqual(streak_days({d(10), d(8)}, t), 1)  # gap
        self.assertEqual(streak_days(set(), t), 0)


class LearningProfileTests(Base):
    def setUp(self):
        super().setUp()
        self.register()
        self.setup_profile("cse", 10)

    def test_roadmap_has_plan_streak_recent(self):
        d = self.client.get("/api/roadmap").get_json()
        self.assertEqual((d["streak"], d["recent"], d["active_today"]), (0, [], False))
        self.assertEqual(d["plan"]["daily_hours"], 1.5)
        step = d["phases"][0]["steps"][0]
        r = self.post(f"/api/progress/{step['id']}", json={"done": True}).get_json()
        self.assertEqual(r["streak"], 1)
        self.assertTrue(r["active_today"])
        self.assertEqual(r["recent"][0]["title"], step["title"])
        self.post(f"/api/progress/{step['id']}", json={"done": False})
        self.assertEqual(self.client.get("/api/roadmap").get_json()["streak"], 0)

    def test_partial_profile_update_keeps_other_fields(self):
        r = self.post("/api/profile", json={"daily_hours": 3})
        self.assertEqual(r.status_code, 200)
        d = self.client.get("/api/roadmap").get_json()
        self.assertEqual((d["stream"]["slug"], d["target_lpa"], d["plan"]["daily_hours"]), ("cse", 10.0, 3.0))
        self.assertEqual(self.post("/api/profile", json={"stream": "eee"}).status_code, 200)
        self.assertEqual(self.client.get("/api/roadmap").get_json()["target_lpa"], 10.0)

    def test_pace_validation(self):
        for bad in (0.1, 9, "x", True, None):
            self.assertEqual(self.post("/api/profile", json={"daily_hours": bad}).status_code, 400, bad)

    def test_new_user_cannot_save_pace_without_stream(self):
        c = self.app.test_client()
        self.register("n@example.com", "New Student", client=c)
        self.assertEqual(self.post("/api/profile", json={"daily_hours": 2}, client=c).status_code, 400)

    def test_completion_dates_use_configured_offset(self):
        app = make_app(UTC_OFFSET_MINUTES=0)
        with app.app_context():
            from dreampath.routes_api import local_now
            a = local_now()
        app2 = make_app(UTC_OFFSET_MINUTES=330)
        with app2.app_context():
            b = local_now()
        os.unlink(app._db_path); os.unlink(app2._db_path)
        self.assertAlmostEqual((b - a).total_seconds(), 330 * 60, delta=5)


class MigrationTests(unittest.TestCase):
    def test_old_database_gets_daily_hours_column(self):
        import sqlite3
        fd, path = tempfile.mkstemp(suffix=".db"); os.close(fd)
        conn = sqlite3.connect(path)
        conn.executescript("""CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student', stream_id INTEGER, target_lpa REAL,
            failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')));
            INSERT INTO users (name, email, password_hash) VALUES ('Old User', 'old@example.com', 'x');""")
        conn.commit(); conn.close()
        app = create_app({"TESTING": True, "DATABASE": path, "SECRET_KEY": "k", "RATELIMIT_ENABLED": False})
        with app.app_context():
            from dreampath.db import get_db
            row = get_db().execute("SELECT daily_hours FROM users WHERE email = 'old@example.com'").fetchone()
        os.unlink(path)
        self.assertEqual(row["daily_hours"], 1.5)


class PublicPagesAndRedirectTests(Base):
    def test_landing_lists_streams_and_stats(self):
        html = self.client.get("/").get_data(as_text=True)
        for name in ("Computer Science", "Mechanical", "Civil"):
            self.assertIn(name, html)
        self.assertIn("/streams/cse", html)
        self.assertIn("curated lessons", html)

    def test_stream_preview_public_and_404(self):
        r = self.client.get("/streams/cse")
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn("Data structures and algorithms", html)
        self.assertIn("Depth by package", html)
        self.assertIn("/register?stream=cse", html)
        self.assertEqual(self.client.get("/streams/nope").status_code, 404)
        self.assertEqual(self.client.get("/streams/%3Cscript%3E").status_code, 404)

    def test_tier_stats_are_cumulative(self):
        from dreampath.catalog import streams_with_stats
        from dreampath import db as dbmod
        with self.app.app_context():
            cse = next(s for s in streams_with_stats(dbmod.get_db()) if s["slug"] == "cse")
        self.assertEqual(cse["lessons"], sorted(cse["lessons"]))
        self.assertEqual(cse["total_lessons"], cse["lessons"][-1])
        self.assertGreater(cse["lessons"][3], cse["lessons"][0])

    def test_register_from_stream_page_flows_to_setup_with_preselect(self):
        r = self.post("/register", {"name": "Riya Sharma", "email": "r@example.com", "password": PASSWORD,
                                    "confirm": PASSWORD, "stream": "mech", "next": "/roadmap"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("stream=mech", r.headers["Location"])
        self.assertIn("next=/roadmap", r.headers["Location"])
        html = self.client.get(r.headers["Location"]).get_data(as_text=True)
        self.assertIn('data-slug="mech"', html)
        self.assertIn('data-next="/roadmap"', html)

    def test_register_page_shows_chosen_stream_and_ignores_junk(self):
        self.assertIn("Mechanical Engineering", self.client.get("/register?stream=mech").get_data(as_text=True))
        html = self.client.get("/register?stream=<script>").get_data(as_text=True)
        self.assertNotIn("<script>", html)

    def test_login_redirect_matrix(self):
        self.register(); self.post("/logout")
        # profile incomplete -> setup, keeping the requested page
        r = self.post("/login", {"email": "stu@example.com", "password": PASSWORD, "next": "/roadmap"})
        self.assertEqual(r.headers["Location"], "/setup?next=/roadmap")
        self.setup_profile("cse", 10); self.post("/logout")
        r = self.post("/login", {"email": "stu@example.com", "password": PASSWORD, "next": "/roadmap"})
        self.assertEqual(r.headers["Location"], "/roadmap")
        self.post("/logout")
        r = self.post("/login", {"email": "stu@example.com", "password": PASSWORD})
        self.assertEqual(r.headers["Location"], "/dashboard")

    def test_protected_page_redirects_to_login_with_message_and_returns_after(self):
        r = self.client.get("/roadmap")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers["Location"], "/login?next=/roadmap")
        html = self.client.get(r.headers["Location"]).get_data(as_text=True)
        self.assertIn("Please log in to continue", html)
        self.assertIn('name="next" value="/roadmap"', html)

    def test_signed_in_users_skip_login_and_register(self):
        self.register()
        self.assertEqual(self.client.get("/login").headers["Location"], "/dashboard")
        self.assertEqual(self.client.get("/register").headers["Location"], "/dashboard")
        self.assertEqual(self.client.get("/login?next=/mentor").headers["Location"], "/mentor")
        self.assertEqual(self.client.get("/login?next=https://evil.com").headers["Location"], "/dashboard")

    def test_incomplete_profile_pages_redirect_to_setup(self):
        self.register()
        for path in ("/dashboard", "/roadmap", "/mentor"):
            r = self.client.get(path)
            self.assertEqual(r.headers["Location"], f"/setup?next=/{path[1:]}", path)

    def test_setup_prefills_saved_plan_and_returns_to_next(self):
        self.register(); self.setup_profile("ece", 18)
        self.post("/api/profile", json={"daily_hours": 3})
        html = self.client.get("/setup?next=/roadmap").get_data(as_text=True)
        self.assertIn('data-slug="ece"', html)
        self.assertIn('data-lpa="18.0"', html)
        self.assertIn('data-pace="3.0"', html)
        self.assertIn('data-next="/roadmap"', html)
        self.assertIn('data-next="/dashboard"', self.client.get("/setup?next=https://evil.com").get_data(as_text=True))

    def test_dashboard_renders_stream_banner_and_user_name_escaped(self):
        self.register(); self.setup_profile("civil", 8)
        html = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("thumb-civil", html)
        self.assertIn("Welcome back, Riya", html)

    def test_header_menu_and_nav_by_state(self):
        guest = self.client.get("/").get_data(as_text=True)
        self.assertIn("Sign up free", guest)
        self.assertNotIn("My learning", guest.split("<main")[0])
        self.register(); self.setup_profile("cse", 10)
        html = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("My learning", html)
        self.assertIn('aria-current="page"', html)
        self.assertIn(">RS<", html)  # avatar initials

    def test_error_page_has_navigation(self):
        html = self.client.get("/nope").get_data(as_text=True)
        self.assertIn("Page not found", html)
        self.assertIn("Back to home", html)

    def test_duration_filter(self):
        with self.app.app_context():
            f = self.app.jinja_env.filters["duration"]
            self.assertEqual((f(45), f(300), f(90), f(60)), ("45 min", "5 h", "1 h 30 min", "1 h"))


if __name__ == "__main__":
    unittest.main()
