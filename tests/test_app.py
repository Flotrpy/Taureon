import unittest

from app import app, build_download_cmd


class BuildDownloadCmdTests(unittest.TestCase):
    def test_audio_extracts_mp3(self):
        cmd = build_download_cmd("out.%(ext)s", "https://x/v", "audio", None)
        self.assertIn("-x", cmd)
        self.assertEqual(cmd[cmd.index("--audio-format") + 1], "mp3")
        self.assertEqual(cmd[-1], "https://x/v")

    def test_video_with_format_id(self):
        cmd = build_download_cmd("out.%(ext)s", "https://x/v", "video", "137")
        self.assertEqual(cmd[cmd.index("-f") + 1], "137+bestaudio/best")
        self.assertIn("--merge-output-format", cmd)

    def test_video_default_best(self):
        cmd = build_download_cmd("out.%(ext)s", "https://x/v", "video", None)
        self.assertEqual(cmd[cmd.index("-f") + 1], "bestvideo+bestaudio/best")

    def test_never_downloads_playlists(self):
        cmd = build_download_cmd("out.%(ext)s", "https://x/v", "video", None)
        self.assertIn("--no-playlist", cmd)


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})

    def test_info_requires_url(self):
        res = self.client.post("/api/info", json={"url": "  "})
        self.assertEqual(res.status_code, 400)

    def test_download_requires_url(self):
        res = self.client.post("/api/download", json={})
        self.assertEqual(res.status_code, 400)

    def test_unknown_job_is_404(self):
        self.assertEqual(self.client.get("/api/status/nope").status_code, 404)
        self.assertEqual(self.client.get("/api/file/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main()
