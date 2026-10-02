import unittest

from app import app, jobs, parse_progress


class ParseProgressTests(unittest.TestCase):
    def test_percent_line(self):
        self.assertEqual(parse_progress("[download]  45.3% of 10.00MiB at 1.2MiB/s ETA 00:05"), 45.3)

    def test_complete_line(self):
        self.assertEqual(parse_progress("[download] 100% of 10.00MiB in 00:08"), 100.0)

    def test_ignores_other_lines(self):
        self.assertIsNone(parse_progress("[youtube] Extracting URL: https://x"))
        self.assertIsNone(parse_progress("[download] Destination: out.mp4"))


class StatusProgressTests(unittest.TestCase):
    def test_status_reports_progress(self):
        jobs["t1"] = {"status": "downloading", "progress": 42.5}
        try:
            data = app.test_client().get("/api/status/t1").get_json()
        finally:
            del jobs["t1"]
        self.assertEqual(data["progress"], 42.5)
        self.assertEqual(data["status"], "downloading")


if __name__ == "__main__":
    unittest.main()
