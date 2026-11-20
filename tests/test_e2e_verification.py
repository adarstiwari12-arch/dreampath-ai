"""Comprehensive E2E QA Verification Script for DreamPath AI.
Simulates real student journeys through all workflows and tests API/page contracts.
"""
import os
import re
import tempfile
import unittest

from dreampath import create_app

class TestDreamPathE2E(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "test-e2e-key",
            "RATELIMIT_ENABLED": False,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def get_csrf(self, client=None, path="/"):
        c = client or self.client
        html = c.get(path).get_data(as_text=True)
        m = re.search(r'name="csrf-token" content="([^"]+)"', html)
        return m.group(1) if m else ""

    def test_complete_student_lifecycle(self):
        # 1. Landing page check
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Plan your path to the package you want.", res.get_data(as_text=True))
        self.assertIn("Choose your stream", res.get_data(as_text=True))
        self.assertIn("Computer Science", res.get_data(as_text=True))

        # 2. Registration
        token = self.get_csrf(path="/register")
        reg_res = self.client.post("/register", data={
            "name": "Aarav Sharma",
            "email": "aarav.sharma@college.edu",
            "password": "Password2026x",
            "confirm": "Password2026x",
            "csrf_token": token
        }, follow_redirects=False)
        self.assertEqual(reg_res.status_code, 302)
        self.assertIn("/setup", reg_res.headers["Location"])

        # 3. Setup / Onboarding (Stream: CSE, LPA: 14.5, Pace: 2.0)
        token = self.get_csrf(path="/setup")
        profile_res = self.client.post("/api/profile", json={
            "stream": "cse",
            "target_lpa": 14.5,
            "daily_hours": 2.0
        }, headers={"X-CSRF-Token": token})
        self.assertEqual(profile_res.status_code, 200)
        pdata = profile_res.get_json()
        self.assertTrue(pdata.get("ok"))
        self.assertEqual(pdata["tier"]["name"], "Pro")

        # 4. Dashboard
        dash_res = self.client.get("/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        dash_html = dash_res.get_data(as_text=True)
        self.assertIn("Welcome back, Aarav", dash_html)
        self.assertIn("thumb-cse", dash_html)

        # 5. Roadmap API & Dream Meter Initial State
        road_res = self.client.get("/api/roadmap")
        self.assertEqual(road_res.status_code, 200)
        rdata = road_res.get_json()
        self.assertEqual(rdata["meter"]["percent"], 0.0)
        self.assertEqual(rdata["meter"]["done_count"], 0)
        total_steps = rdata["meter"]["total_count"]
        self.assertGreater(total_steps, 10)
        first_step = rdata["phases"][0]["steps"][0]
        self.assertFalse(first_step["done"])

        # 6. Mark first lesson done (Ticking progress)
        token = self.get_csrf()
        tick_res = self.client.post(f"/api/progress/{first_step['id']}", json={"done": True}, headers={"X-CSRF-Token": token})
        self.assertEqual(tick_res.status_code, 200)
        tdata = tick_res.get_json()
        new_pct = tdata["meter"]["percent"]
        self.assertGreater(new_pct, 0.0)
        self.assertEqual(tdata["streak"], 1)
        self.assertTrue(tdata["active_today"])
        self.assertEqual(tdata["recent"][0]["title"], first_step["title"])

        # 7. Persistence check on fresh load
        fresh_road = self.client.get("/api/roadmap").get_json()
        self.assertEqual(fresh_road["meter"]["percent"], new_pct)
        self.assertTrue(fresh_road["phases"][0]["steps"][0]["done"])

        # 8. AI Mentor Question
        mentor_res = self.client.post("/api/ai/mentor", json={"message": "What should I focus on next?"}, headers={"X-CSRF-Token": token})
        self.assertEqual(mentor_res.status_code, 200)
        mdata = mentor_res.get_json()
        self.assertIn("reply", mdata)
        self.assertIn("source", mdata)
        self.assertIn(mdata["source"], ("rules", "llm"))

        # 9. Informational Pages
        for route in ("/about", "/faq", "/privacy", "/terms"):
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200)

        # 10. Logout and protected routes check
        self.client.post("/logout", data={"csrf_token": token})
        self.assertEqual(self.client.get("/dashboard").status_code, 302)
        self.assertEqual(self.client.get("/api/roadmap").status_code, 401)
        print(">>> All E2E lifecycle tests passed successfully!")

if __name__ == "__main__":
    unittest.main()
