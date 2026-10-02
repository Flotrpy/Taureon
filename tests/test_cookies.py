import os
import tempfile
import unittest
from unittest import mock

import app as app_module
from app import build_download_cmd, get_cookies_file, ytdlp_cmd


class CookiesTests(unittest.TestCase):
    def setUp(self):
        # get_cookies_file() caches its result in a module global; reset it
        # between tests so each test starts from a clean slate.
        app_module._cookies_tmp_path = None

    def tearDown(self):
        path = app_module._cookies_tmp_path
        if path and os.path.isfile(path):
            os.remove(path)
        app_module._cookies_tmp_path = None

    def test_no_cookies_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(get_cookies_file())
            self.assertEqual(ytdlp_cmd("-j", "u"), ["yt-dlp", "-j", "u"])

    def test_path_is_copied_to_a_writable_temp_file(self):
        # yt-dlp rewrites the cookies file it's given, so a read-only source
        # (e.g. a Render secret file) must be copied somewhere writable first.
        fd, src = tempfile.mkstemp()
        with os.fdopen(fd, "w") as fh:
            fh.write("# Netscape HTTP Cookie File\n")
        try:
            with mock.patch.dict(os.environ, {"YTDLP_COOKIES": src}, clear=True):
                path = get_cookies_file()
                self.assertNotEqual(path, src)
                with open(path) as fh:
                    self.assertEqual(fh.read(), "# Netscape HTTP Cookie File\n")
                self.assertEqual(get_cookies_file(), path)  # cached, not re-copied
        finally:
            os.remove(src)

    def test_content_is_written_to_a_file(self):
        env = {"YTDLP_COOKIES_CONTENT": "# Netscape HTTP Cookie File\n"}
        with mock.patch.dict(os.environ, env, clear=True):
            path = get_cookies_file()
            self.assertTrue(os.path.isfile(path))
            with open(path) as fh:
                self.assertEqual(fh.read(), env["YTDLP_COOKIES_CONTENT"])
            self.assertEqual(get_cookies_file(), path)  # reused, not rewritten

    def test_download_command_uses_cookies(self):
        env = {"YTDLP_COOKIES_CONTENT": "# Netscape HTTP Cookie File\n"}
        with mock.patch.dict(os.environ, env, clear=True):
            cmd = build_download_cmd("o.%(ext)s", "https://x/v", "video", None)
        self.assertEqual(cmd[0], "yt-dlp")
        self.assertEqual(cmd[1], "--cookies")
        self.assertTrue(os.path.isfile(cmd[2]))


if __name__ == "__main__":
    unittest.main()
