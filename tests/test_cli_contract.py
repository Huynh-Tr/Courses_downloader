import tests  # noqa: F401
"""
Characterization tests for CLI argument parsing contract (commandline.py).
Captures all flag defaults, list splitting, validation rules, and exit codes.
"""

import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import commandline


class TestCommandLineContract(unittest.TestCase):
    """Test parse_args contract and validation rules."""

    def test_default_options_with_cauth(self):
        cmd = ["-ca", "dummy_cauth_token", "machine-learning"]
        args = commandline.parse_args(cmd)

        self.assertEqual(args.class_names, ["machine-learning"])
        self.assertEqual(args.cookies_cauth, "dummy_cauth_token")
        self.assertEqual(args.jobs, 1)
        self.assertEqual(args.download_delay, 60)
        self.assertFalse(args.preview)
        self.assertEqual(args.path, "")
        self.assertEqual(args.subtitle_language, "all")
        self.assertFalse(args.specialization)
        self.assertFalse(args.only_syllabus)
        self.assertFalse(args.download_quizzes)
        self.assertFalse(args.download_notebooks)
        self.assertFalse(args.about)
        self.assertEqual(args.file_formats, ["all"])
        self.assertIsNone(args.ignore_formats)
        self.assertEqual(args.video_resolution, "540p")
        self.assertFalse(args.disable_url_skipping)
        self.assertFalse(args.resume)
        self.assertFalse(args.overwrite)
        self.assertFalse(args.verbose_dirs)
        self.assertFalse(args.quiet)
        self.assertFalse(args.reverse)
        self.assertFalse(args.combined_section_lectures_nums)
        self.assertFalse(args.unrestricted_filenames)
        self.assertEqual(args.downloader_arguments, [])

    def test_multiple_class_names(self):
        cmd = ["-ca", "token", "course-1", "course-2", "course-3"]
        args = commandline.parse_args(cmd)
        self.assertEqual(args.class_names, ["course-1", "course-2", "course-3"])

    def test_formats_string_splitting(self):
        cmd = ["-ca", "token", "-f", "mp4 pdf srt ipynb", "ml"]
        args = commandline.parse_args(cmd)
        self.assertEqual(args.file_formats, ["mp4", "pdf", "srt", "ipynb"])

    def test_downloader_arguments_splitting(self):
        cmd = ["-ca", "token", "--downloader-arguments", "--limit-rate 500k -k", "ml"]
        args = commandline.parse_args(cmd)
        self.assertEqual(args.downloader_arguments, ["--limit-rate", "500k", "-k"])

    def test_custom_flags(self):
        cmd = [
            "-ca", "token",
            "--jobs", "4",
            "--video-resolution", "720p",
            "--subtitle-language", "en,es",
            "--download-delay", "10",
            "--resume",
            "--overwrite",
            "--verbose-dirs",
            "--reverse",
            "--combined-section-lectures-nums",
            "--unrestricted-filenames",
            "--download-quizzes",
            "--download-notebooks",
            "--disable-url-skipping",
            "deep-learning",
        ]
        args = commandline.parse_args(cmd)
        self.assertEqual(args.jobs, 4)
        self.assertEqual(args.video_resolution, "720p")
        self.assertEqual(args.subtitle_language, "en,es")
        self.assertEqual(args.download_delay, 10)
        self.assertTrue(args.resume)
        self.assertTrue(args.overwrite)
        self.assertTrue(args.verbose_dirs)
        self.assertTrue(args.reverse)
        self.assertTrue(args.combined_section_lectures_nums)
        self.assertTrue(args.unrestricted_filenames)
        self.assertTrue(args.download_quizzes)
        self.assertTrue(args.download_notebooks)
        self.assertTrue(args.disable_url_skipping)

    def test_auth_branches_accepted(self):
        # 1. browser cookie
        args_browser = commandline.parse_args(["-caa", "chrome", "ml"])
        self.assertEqual(args_browser.browser, "chrome")

        # 2. edge cookies flag
        args_edge = commandline.parse_args(["--edge-cookies", "ml"])
        self.assertTrue(args_edge.use_edge_cookies)

        # 3. cookie file
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("# Netscape HTTP Cookie File\n")
            f_path = f.name
        try:
            args_file = commandline.parse_args(["-c", f_path, "ml"])
            self.assertEqual(args_file.cookies_file, f_path)
        finally:
            os.remove(f_path)

        # 4. username and password
        args_up = commandline.parse_args(["-u", "student@example.test", "-p", "secret123", "ml"])
        self.assertEqual(args_up.username, "student@example.test")
        self.assertEqual(args_up.password, "secret123")

    def test_missing_auth_exits_with_error(self):
        with self.assertRaises(SystemExit) as ctx:
            commandline.parse_args(["ml"])
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_class_name_exits_with_error(self):
        with self.assertRaises(SystemExit) as ctx:
            commandline.parse_args(["-ca", "token"])
        self.assertEqual(ctx.exception.code, 1)

    def test_version_flag_prints_and_exits_zero(self):
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf), self.assertRaises(SystemExit) as ctx:
            commandline.parse_args(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        output = stdout_buf.getvalue().strip()
        self.assertEqual(output, commandline.__courseradlversion__)

    def test_class_name_arg_required_helper(self):
        class DummyArgs:
            list_courses = False
            version = False
            save_edge_cookies = None

        args = DummyArgs()
        self.assertTrue(commandline.class_name_arg_required(args))

        args.list_courses = True
        self.assertFalse(commandline.class_name_arg_required(args))

        args.list_courses = False
        args.version = True
        self.assertFalse(commandline.class_name_arg_required(args))

        args.version = False
        args.save_edge_cookies = "cookies.txt"
        self.assertFalse(commandline.class_name_arg_required(args))

    def test_get_credentials_error_on_missing_username(self):
        with self.assertRaises(commandline.CredentialsError):
            commandline.get_credentials(username=None, password=None)


if __name__ == "__main__":
    unittest.main()
