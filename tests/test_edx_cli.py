"""
Unit tests for edX CLI (edx_dl.py): argument parsing, dry-run reporting,
cookie loading, and compliance notices.
"""

import io
import os
import tempfile
import tests  # noqa: F401 - triggers test network guard and shims
import unittest
from unittest.mock import MagicMock, patch

import edx_dl
import edx_provider
from tests.fixtures.edx_course_blocks import EDX_COURSE_KEY, VALID_EDX_BLOCKS


class TestEdxCli(unittest.TestCase):
    """Test CLI commands, flags, dry-run output, and error conditions."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_cli_missing_course_argument_returns_one(self):
        ret = edx_dl.main([])
        self.assertEqual(ret, 1)

    def test_cli_invalid_course_key_returns_one(self):
        ret = edx_dl.main(["invalid-course-key"])
        self.assertEqual(ret, 1)

    def test_cli_cookies_file_not_found_returns_one(self):
        ret = edx_dl.main([
            "--cookies-file", "/tmp/nonexistent_cookies_12345.txt",
            EDX_COURSE_KEY,
        ])
        self.assertEqual(ret, 1)

    @patch("edx_provider.EdxClient.get_course_blocks")
    def test_cli_dry_run_produces_sanitized_summary_and_no_disk_writes(self, mock_blocks):
        mock_blocks.return_value = VALID_EDX_BLOCKS

        out_dir = os.path.join(self.tmpdir.name, "edx_out")
        captured_stdout = io.StringIO()

        with patch("sys.stdout", captured_stdout):
            ret = edx_dl.main([
                "--dry-run",
                "--path", out_dir,
                "--sub-lang", "vi",
                EDX_COURSE_KEY,
            ])

        output = captured_stdout.getvalue()

        # 1. Successful zero exit code
        self.assertEqual(ret, 0)

        # 2. Compliance notice printed
        self.assertIn("Terms of Service", output)

        # 3. Structured summary header and counts
        self.assertIn("edX Course Dry-Run Summary", output)
        self.assertIn("Hierarchy: 2 Modules", output)
        self.assertIn("Direct MP4 Videos: 2", output)
        self.assertIn("Subtitles: 2", output)
        self.assertIn("Attachments/Documents: 1", output)

        # 4. Skip tracking categories present in output
        self.assertIn("RESTRICTED_MEDIA", output)
        self.assertIn("UNSUPPORTED_MEDIA", output)
        self.assertIn("Dry-run complete. 0 files written to disk.", output)

        # 5. Absolutely no files written to disk
        self.assertFalse(os.path.exists(out_dir))

    @patch("edx_provider.EdxClient.get_course_blocks")
    def test_cli_loads_cookies_file_successfully(self, mock_blocks):
        mock_blocks.return_value = VALID_EDX_BLOCKS

        cookie_file = os.path.join(self.tmpdir.name, "cookies.txt")
        with open(cookie_file, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write(".edx.org\tTRUE\t/\tTRUE\t2147483647\tsessionid\tsample_session_secret\n")

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            ret = edx_dl.main([
                "--dry-run",
                "--cookies-file", cookie_file,
                EDX_COURSE_KEY,
            ])

        self.assertEqual(ret, 0)
        output = captured_stdout.getvalue()
        # Verify secret session token was never printed to output
        self.assertNotIn("sample_session_secret", output)

    @patch("edx_provider.EdxClient.get_course_blocks")
    def test_cli_auth_error_returns_one(self, mock_blocks):
        mock_blocks.side_effect = edx_provider.EdxAuthError("Session expired (HTTP 401)")

        ret = edx_dl.main([
            "--dry-run",
            EDX_COURSE_KEY,
        ])
        self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main()
