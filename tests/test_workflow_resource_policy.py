import tests  # noqa: F401
"""
Characterization tests for file download decisions, resume/overwrite logic,
in-memory content handling, and error/skip collection in CourseraDownloader.
"""

import os
import tempfile
import time
import unittest
from types import SimpleNamespace

import requests

from define import IN_MEMORY_MARKER
import workflow
from tests.fixtures.sanitized_syllabus import SINGLE_MODULE_SYLLABUS


class FakeDownloader:
    """Mock downloader tracking calls without network or subprocess activity."""

    def __init__(self, download_result=True):
        self.calls = []
        self.download_result = download_result
        self.joined = False

    def download(self, callback, url, filename, resume=False):
        self.calls.append({
            "url": url,
            "filename": filename,
            "resume": resume,
        })
        if callback:
            callback(url, self.download_result)

    def join(self):
        self.joined = True


def _make_downloader_args(**kwargs):
    defaults = {
        "overwrite": False,
        "resume": False,
        "skip_download": False,
        "file_formats": ["all"],
        "lecture_filter": None,
        "resource_filter": None,
        "section_filter": None,
        "verbose_dirs": False,
        "combined_section_lectures_nums": False,
        "playlist": False,
        "hooks": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestWorkflowResourcePolicy(unittest.TestCase):
    """Test _handle_resource policy on disk state and options."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_new_file_triggers_download(self):
        fake = FakeDownloader()
        args = _make_downloader_args()
        cdl = workflow.CourseraDownloader(fake, args, "class_a", path=self.path)

        target_file = os.path.join(self.path, "test_video.mp4")
        t_before = time.time()
        last_update = cdl._handle_resource(
            "https://example.test/v.mp4", "mp4", target_file, cdl._download_completion_handler, -1
        )

        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0]["url"], "https://example.test/v.mp4")
        self.assertEqual(fake.calls[0]["filename"], target_file)
        self.assertFalse(fake.calls[0]["resume"])
        self.assertGreaterEqual(last_update, t_before)

    def test_existing_file_skipped_when_no_overwrite_or_resume(self):
        fake = FakeDownloader()
        args = _make_downloader_args(overwrite=False, resume=False)
        cdl = workflow.CourseraDownloader(fake, args, "class_a", path=self.path)

        target_file = os.path.join(self.path, "existing_video.mp4")
        with open(target_file, "wb") as f:
            f.write(b"data")
        file_mtime = os.path.getmtime(target_file)

        last_update = cdl._handle_resource(
            "https://example.test/v.mp4", "mp4", target_file, cdl._download_completion_handler, 100
        )

        self.assertEqual(len(fake.calls), 0)
        self.assertEqual(last_update, max(100, file_mtime))

    def test_existing_file_overwritten_when_overwrite_true(self):
        fake = FakeDownloader()
        args = _make_downloader_args(overwrite=True, resume=False)
        cdl = workflow.CourseraDownloader(fake, args, "class_a", path=self.path)

        target_file = os.path.join(self.path, "existing_video.mp4")
        with open(target_file, "wb") as f:
            f.write(b"data")

        cdl._handle_resource(
            "https://example.test/v.mp4", "mp4", target_file, cdl._download_completion_handler, -1
        )

        self.assertEqual(len(fake.calls), 1)
        self.assertFalse(fake.calls[0]["resume"])

    def test_existing_file_resumed_when_resume_true(self):
        fake = FakeDownloader()
        args = _make_downloader_args(overwrite=False, resume=True)
        cdl = workflow.CourseraDownloader(fake, args, "class_a", path=self.path)

        target_file = os.path.join(self.path, "partial_video.mp4")
        with open(target_file, "wb") as f:
            f.write(b"partial")

        cdl._handle_resource(
            "https://example.test/v.mp4", "mp4", target_file, cdl._download_completion_handler, -1
        )

        self.assertEqual(len(fake.calls), 1)
        self.assertTrue(fake.calls[0]["resume"])

    def test_skip_download_touches_empty_file(self):
        fake = FakeDownloader()
        args = _make_downloader_args(skip_download=True)
        cdl = workflow.CourseraDownloader(fake, args, "class_a", path=self.path)

        target_file = os.path.join(self.path, "dry_run.mp4")
        cdl._handle_resource(
            "https://example.test/v.mp4", "mp4", target_file, cdl._download_completion_handler, -1
        )

        self.assertEqual(len(fake.calls), 0)
        self.assertTrue(os.path.exists(target_file))
        self.assertEqual(os.path.getsize(target_file), 0)

    def test_in_memory_reading_written_as_utf8(self):
        fake = FakeDownloader()
        args = _make_downloader_args()
        cdl = workflow.CourseraDownloader(fake, args, "class_a", path=self.path)

        target_file = os.path.join(self.path, "reading.html")
        html_payload = "<h1>Bài học nhập môn: Trí tuệ nhân tạo</h1>"
        url = f"{IN_MEMORY_MARKER}{html_payload}"

        cdl._handle_resource(url, "html", target_file, cdl._download_completion_handler, -1)

        self.assertEqual(len(fake.calls), 0)
        self.assertTrue(os.path.exists(target_file))
        with open(target_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), html_payload)

    def test_url_skipping_recorded(self):
        fake = FakeDownloader()
        args = _make_downloader_args()
        # Default: disable_url_skipping=False -> skipped_urls is a list
        cdl = workflow.CourseraDownloader(
            fake, args, "class_a", path=self.path, disable_url_skipping=False
        )

        target_file = os.path.join(self.path, "skipped.txt")
        mailto_url = "mailto:test@example.test"
        cdl._handle_resource(mailto_url, "txt", target_file, cdl._download_completion_handler, -1)

        self.assertEqual(len(fake.calls), 0)
        self.assertIn(mailto_url, cdl.skipped_urls)

    def test_disable_url_skipping_allows_download(self):
        fake = FakeDownloader()
        args = _make_downloader_args()
        cdl = workflow.CourseraDownloader(
            fake, args, "class_a", path=self.path, disable_url_skipping=True
        )

        target_file = os.path.join(self.path, "skipped.txt")
        mailto_url = "mailto:test@example.test"
        cdl._handle_resource(mailto_url, "txt", target_file, cdl._download_completion_handler, -1)

        self.assertIsNone(cdl.skipped_urls)
        self.assertEqual(len(fake.calls), 1)

    def test_completion_handler_tracks_failures(self):
        args = _make_downloader_args()
        cdl = workflow.CourseraDownloader(FakeDownloader(), args, "c", path=self.path)

        # 1. RequestException
        cdl._download_completion_handler("https://fail1.test", requests.exceptions.HTTPError("404"))
        self.assertIn("https://fail1.test", cdl.failed_urls)

        # 2. General Exception
        cdl._download_completion_handler("https://fail2.test", RuntimeError("IO Error"))
        self.assertIn("https://fail2.test", cdl.failed_urls)

        # 3. False return value
        cdl._download_completion_handler("https://fail3.test", False)
        self.assertIn("https://fail3.test", cdl.failed_urls)

        # 4. Successful result (True)
        cdl._download_completion_handler("https://success.test", True)
        self.assertNotIn("https://success.test", cdl.failed_urls)

    def test_full_download_modules_execution(self):
        fake = FakeDownloader()
        args = _make_downloader_args()
        cdl = workflow.CourseraDownloader(fake, args, "sample-course", path=self.path)

        completed = cdl.download_modules(SINGLE_MODULE_SYLLABUS)

        self.assertTrue(fake.joined)
        # Expected calls for files that are not in-memory:
        # mp4, srt, txt, pdf -> 4 downloader calls (html was in-memory)
        self.assertEqual(len(fake.calls), 4)
        urls_called = [c["url"] for c in fake.calls]
        self.assertIn("https://example.test/videos/welcome.mp4", urls_called)
        self.assertIn("https://example.test/subtitles/welcome_en.srt", urls_called)
        self.assertIn("https://example.test/transcripts/welcome_en.txt", urls_called)
        self.assertIn("https://example.test/docs/syllabus.pdf", urls_called)

        # In-memory HTML should exist on disk
        expected_html = os.path.join(
            self.path,
            "sample-course",
            "01_week-1-introduction",
            "01_lesson-1-welcome",
            "02_02-course-syllabus_Syllabus Reading.html",
        )
        self.assertTrue(os.path.exists(expected_html))


if __name__ == "__main__":
    unittest.main()
