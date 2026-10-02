import json
import unittest

from app import parse_ytdlp_json


class ParseYtdlpJsonTests(unittest.TestCase):
    def test_single_object(self):
        out = json.dumps({"title": "one"})
        self.assertEqual(parse_ytdlp_json(out)["title"], "one")

    def test_returns_first_of_many_lines(self):
        out = json.dumps({"title": "first"}) + "\n" + json.dumps({"title": "second"})
        self.assertEqual(parse_ytdlp_json(out)["title"], "first")

    def test_skips_blank_lines(self):
        out = "\n\n  \n" + json.dumps({"title": "x"}) + "\n"
        self.assertEqual(parse_ytdlp_json(out)["title"], "x")

    def test_empty_output_raises(self):
        with self.assertRaises(ValueError):
            parse_ytdlp_json("  \n\n")

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_ytdlp_json("not json")


if __name__ == "__main__":
    unittest.main()
