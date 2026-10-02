import os
import unittest
from unittest import mock

from app import build_download_cmd, get_cookies_file, ytdlp_cmd


class CookiesTests(unittest.TestCase):
    def test_no_cookies_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(get_cookies_file())
            self.assertEqual(ytdlp_cmd("-j", "u"), ["yt-dlp", "-j", "u"])

    def test_path_is_used(self):
        with mock.patch.dict(os.environ, {"YTDLP_COOKIES": "/tmp/c.txt"}, clear=True):
            self.assertEqual(ytdlp_cmd("-j", "u"), ["yt-dlp", "--cookies", "/tmp/c.txt", "-j", "u"])

    def test_content_is_written_to_a_file(self):
        env = {"YTDLP_COOKIES_CONTENT": "# Netscape HTTP Cookie File\n"}
        with mock.patch.dict(os.environ, env, clear=True):
            path = get_cookies_file()
            self.assertTrue(os.path.isfile(path))
            with open(path) as fh:
                self.assertEqual(fh.read(), env["YTDLP_COOKIES_CONTENT"])
            self.assertEqual(get_cookies_file(), path)  # reused, not rewritten
        os.remove(path)

    def test_download_command_uses_cookies(self):
        with mock.patch.dict(os.environ, {"YTDLP_COOKIES": "/tmp/c.txt"}, clear=True):
            cmd = build_download_cmd("o.%(ext)s", "https://x/v", "video", None)
        self.assertEqual(cmd[:3], ["yt-dlp", "--cookies", "/tmp/c.txt"])


if __name__ == "__main__":
    unittest.main()
