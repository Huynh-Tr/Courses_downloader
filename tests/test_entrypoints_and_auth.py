"""
Unit tests for Phase 03: Entrypoint & Authentication Simplification.
Verifies sys.argv immutability, secret token redaction in logs, universal cookie loading,
URL/slug harmonization, platform detection, and unified CLI dispatching.
"""

import io
import logging
import os
import sys
import tempfile
import tests  # noqa: F401 - triggers test network guard and shims
import unittest
from unittest.mock import MagicMock, patch

import cookies
import coursedownloader
import coursera_dl
import edx_dl
import general


class TestSysArgvImmutability(unittest.TestCase):
    """Ensure programmatic invocations never mutate global sys.argv."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_argv = list(sys.argv)

    def tearDown(self):
        sys.argv = self.original_argv
        self.tmpdir.cleanup()

    @patch("coursera_dl.main_f")
    def test_download_coursera_course_preserves_sys_argv(self, mock_main_f):
        cookies_file = os.path.join(self.tmpdir.name, "cookies.txt")
        with open(cookies_file, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")

        initial_argv = ["test_runner.py", "--some-flag", "val"]
        sys.argv = list(initial_argv)

        ok = coursera_dl.download_coursera_course(
            "https://www.coursera.org/learn/test-course",
            output_path=self.tmpdir.name,
            cookies_file=cookies_file,
        )

        self.assertTrue(ok)
        self.assertEqual(sys.argv, initial_argv)
        mock_main_f.assert_called_once_with([
            "--cookies_file",
            cookies_file,
            "--path",
            self.tmpdir.name,
            "test-course",
        ])

    @patch("coursera_dl.main_f")
    def test_cli_main_with_explicit_argv_preserves_sys_argv(self, mock_main_f):
        initial_argv = ["test_runner.py"]
        sys.argv = list(initial_argv)

        ret = coursera_dl._cli_main(["-u", "user", "-p", "pass", "class-name"])
        self.assertEqual(ret, 0)
        self.assertEqual(sys.argv, initial_argv)
        mock_main_f.assert_called_once_with(["-u", "user", "-p", "pass", "class-name"])


class TestSecretRedaction(unittest.TestCase):
    """Verify secrets (CAUTH tokens, session cookies) are never logged in plaintext."""

    def test_prepare_auth_headers_redacts_cauth_in_debug_logs(self):
        secret_token = "VERY_SECRET_CAUTH_TOKEN_987654321"
        session = MagicMock()
        session.cookies.get.return_value = secret_token

        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger()
        orig_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            cookies.prepare_auth_headers(session, include_cauth=True)
            output = log_stream.getvalue()
            self.assertNotIn(secret_token, output)
            self.assertIn("[REDACTED]", output)
        finally:
            logger.removeHandler(handler)
            logger.setLevel(orig_level)

    @patch("cookies.load_cookies_from_browser")
    def test_create_session_browser_redacts_cauth_in_debug_logs(self, mock_load):
        secret_token = "SUPER_SECRET_BROWSER_COOKIE_112233"
        cookie_mock = MagicMock()
        cookie_mock.name = "CAUTH"
        cookie_mock.value = secret_token
        mock_load.return_value = [cookie_mock]

        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger()
        orig_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        args = MagicMock()
        args.cookies_cauth = None
        args.browser = "chrome"
        args.use_edge_cookies = False
        args.cookies_file = None

        try:
            with patch("coursera_dl.get_session") as mock_get_sess:
                sess_mock = MagicMock()
                mock_get_sess.return_value = sess_mock
                coursera_dl.create_session(args)
                sess_mock.cookies.set.assert_called_once_with("CAUTH", secret_token)

            output = log_stream.getvalue()
            self.assertNotIn(secret_token, output)
        finally:
            logger.removeHandler(handler)
            logger.setLevel(orig_level)


class TestUniversalCookieLoading(unittest.TestCase):
    """Verify cookies.py loads Netscape format and JSON format seamlessly."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_get_cookie_jar_loads_netscape_format(self):
        cookie_file = os.path.join(self.tmpdir.name, "cookies.txt")
        with open(cookie_file, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write(".coursera.org\tTRUE\t/\tTRUE\t2147483647\tCAUTH\tsample_cauth_123\n")

        jar = cookies.get_cookie_jar(cookie_file)
        names = [c.name for c in jar]
        self.assertIn("CAUTH", names)

    def test_get_cookie_jar_loads_json_list_format(self):
        cookie_file = os.path.join(self.tmpdir.name, "cookies.json")
        with open(cookie_file, "w") as f:
            f.write('[{"name": "CAUTH", "value": "json_cauth_456", "domain": ".coursera.org", "path": "/"}]')

        jar = cookies.get_cookie_jar(cookie_file)
        cauth_val = None
        for c in jar:
            if c.name == "CAUTH":
                cauth_val = c.value
        self.assertEqual(cauth_val, "json_cauth_456")

    def test_get_cookie_jar_loads_json_dict_format(self):
        cookie_file = os.path.join(self.tmpdir.name, "cookies_dict.json")
        with open(cookie_file, "w") as f:
            f.write('{"CAUTH": "dict_cauth_789", "sessionid": "sess_123"}')

        jar = cookies.get_cookie_jar(cookie_file)
        values = {c.name: c.value for c in jar}
        self.assertEqual(values.get("CAUTH"), "dict_cauth_789")
        self.assertEqual(values.get("sessionid"), "sess_123")


class TestUrlAndSlugHarmonization(unittest.TestCase):
    """Test unified slug extraction and platform auto-detection."""

    def test_extract_slug_from_url_and_urltoclassname(self):
        cases = [
            ("wharton-quantitative-modeling", "wharton-quantitative-modeling"),
            ("https://www.coursera.org/learn/machine-learning", "machine-learning"),
            ("https://www.coursera.org/learn/deep-neural-network/home/week/2", "deep-neural-network"),
            ("https://www.coursera.org/learn/nlp-intro?specialization=deep-learning", "nlp-intro"),
            ("https://www.coursera.org/LEARN/Model-Thinking", "model-thinking"),
        ]
        for inp, expected in cases:
            self.assertEqual(general.extract_slug_from_url(inp), expected)
            self.assertEqual(general.urltoclassname(inp), expected)

        # Invalid URLs
        self.assertEqual(general.urltoclassname("https://example.com/not-coursera"), "")
        with self.assertRaises(ValueError):
            coursera_dl.extract_course_slug("https://example.com/not-coursera")

    def test_detect_platform(self):
        # Coursera URLs
        self.assertEqual(
            general.detect_platform("https://www.coursera.org/learn/machine-learning"),
            "coursera",
        )
        self.assertEqual(
            general.detect_platform("https://coursera.org/learn/finance?spec=all"),
            "coursera",
        )

        # edX URLs and Keys
        self.assertEqual(
            general.detect_platform("https://learning.edx.org/course/course-v1:MITx+15.481x+1T2021/home"),
            "edx",
        )
        self.assertEqual(
            general.detect_platform("https://courses.edx.org/courses/course-v1:HarvardX+CS50+X/courseware"),
            "edx",
        )
        self.assertEqual(
            general.detect_platform("course-v1:MITx+15.481x+1T2021"),
            "edx",
        )
        self.assertEqual(
            general.detect_platform("https://courses.learn.mit.edu/learn/course/course-v1:MITxT+15.415.2x+2T2026/home"),
            "edx",
        )
        self.assertEqual(
            general.detect_platform("MITx/6.00.1x/3T2026"),
            "edx",
        )

        # Unknown
        self.assertEqual(general.detect_platform("just-a-slug"), "unknown")
        self.assertEqual(general.detect_platform("https://udemy.com/course/python"), "unknown")
        self.assertEqual(general.detect_platform(""), "unknown")


class TestUnifiedDispatcher(unittest.TestCase):
    """Test coursedownloader.py top-level CLI dispatching and auto-detection."""

    def test_help_and_version(self):
        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = coursedownloader.main(["--help"])
            self.assertEqual(ret, 0)
            self.assertIn("Course Downloader", out.getvalue())

        out2 = io.StringIO()
        with patch("sys.stdout", out2):
            ret = coursedownloader.main(["--version"])
            self.assertEqual(ret, 0)
            self.assertIn("Course Downloader", out2.getvalue())

    def test_no_args_returns_one(self):
        ret = coursedownloader.main([])
        self.assertEqual(ret, 1)

    @patch("coursera_dl._cli_main")
    def test_subcommand_coursera_dispatch(self, mock_coursera):
        mock_coursera.return_value = 0
        ret = coursedownloader.main(["coursera", "-u", "user", "-p", "pass", "ml"])
        self.assertEqual(ret, 0)
        mock_coursera.assert_called_once_with(["-u", "user", "-p", "pass", "ml"])

    @patch("edx_dl.main")
    def test_subcommand_edx_dispatch(self, mock_edx):
        mock_edx.return_value = 0
        ret = coursedownloader.main(["edx", "--dry-run", "course-v1:MITx+15.481x+1T2021"])
        self.assertEqual(ret, 0)
        mock_edx.assert_called_once_with(["--dry-run", "course-v1:MITx+15.481x+1T2021"])

    @patch("coursera_dl._cli_main")
    def test_autodetect_coursera_url(self, mock_coursera):
        mock_coursera.return_value = 0
        url = "https://www.coursera.org/learn/wharton-quantitative-modeling"
        ret = coursedownloader.main([url, "--path", "/downloads"])
        self.assertEqual(ret, 0)
        mock_coursera.assert_called_once_with([url, "--path", "/downloads"])

    @patch("edx_dl.main")
    def test_autodetect_edx_url(self, mock_edx):
        mock_edx.return_value = 0
        url = "https://learning.edx.org/course/course-v1:MITx+15.481x+1T2021/home"
        ret = coursedownloader.main([url, "--dry-run"])
        self.assertEqual(ret, 0)
        mock_edx.assert_called_once_with([url, "--dry-run"])

    @patch("edx_dl.main")
    def test_autodetect_edx_course_key(self, mock_edx):
        mock_edx.return_value = 0
        key = "course-v1:MITx+15.481x+1T2021"
        ret = coursedownloader.main([key, "--dry-run"])
        self.assertEqual(ret, 0)
        mock_edx.assert_called_once_with([key, "--dry-run"])

    def test_unrecognized_target_returns_one(self):
        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = coursedownloader.main(["random-unrecognized-string"])
            self.assertEqual(ret, 1)
            self.assertIn("Could not auto-detect platform", out.getvalue())


if __name__ == "__main__":
    unittest.main()
