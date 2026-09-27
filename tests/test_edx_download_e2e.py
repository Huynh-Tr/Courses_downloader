"""
End-to-End integration tests for edX.org course downloader:
verifies full workflow execution, atomic writes, idempotency, retry policies,
SSRF rejection, and session cookie isolation.
"""

import io
import os
import tempfile
import tests  # noqa: F401 - triggers test network guard and shims
import unittest
from unittest.mock import MagicMock, patch

import requests

import edx_dl
import edx_provider
import models
from tests.fixtures.edx_course_blocks import (
    EDX_COURSE_KEY,
    EMPTY_EDX_BLOCKS,
    VALID_EDX_BLOCKS,
)
import workflow


class TestEdxDownloadE2E(unittest.TestCase):
    """End-to-End tests for edX download execution."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.output_path = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def _create_mock_asset_response(self, content: bytes = b"dummy content", status_code: int = 200, headers: dict = None):
        """Helper to create a streaming response mock."""
        resp = MagicMock()
        resp.status_code = status_code
        resp.headers = headers or {"Content-Length": str(len(content))}
        resp.url = "https://edx-video.net/asset.mp4"
        resp.history = []
        resp.iter_content.return_value = [content]
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return resp

    @patch("time.sleep", return_value=None)
    @patch("edx_provider.EdxClient.get_course_blocks")
    def test_e2e_fake_course_download_success(self, mock_blocks, mock_sleep):
        """Verify full download workflow creates exact planned files on disk and skips restricted media."""
        mock_blocks.return_value = VALID_EDX_BLOCKS

        # Mock download requests
        mock_get_calls = []

        def mock_get(url, *args, **kwargs):
            mock_get_calls.append(url)
            if "desktop.mp4" in url:
                return self._create_mock_asset_response(b"VIDEO_DATA_01")
            elif "arrays_low.mp4" in url:
                return self._create_mock_asset_response(b"VIDEO_DATA_02")
            elif "lang=vi" in url or "lang=en" in url:
                return self._create_mock_asset_response(b"WEBVTT\n1\n00:00 -> 00:01\nHi")
            elif "week1_algorithms.pdf" in url:
                return self._create_mock_asset_response(b"%PDF-1.4 dummy pdf")
            return self._create_mock_asset_response(b"UNKNOWN")

        with patch("requests.Session.get", side_effect=mock_get):
            ret = edx_dl.main([
                "--path", self.output_path,
                "--sub-lang", "vi",
                EDX_COURSE_KEY,
            ])

        self.assertEqual(ret, 0)

        # Verify course directory structure
        course_dir = os.path.join(self.output_path, "edx", "TestOrg-CS101-2026_T1")
        self.assertTrue(os.path.isdir(course_dir))

        # Check Module 1 -> Section 1 files
        sec1_dir = os.path.join(
            course_dir,
            "01_01_week-1-fundamentals",
            "01_01_lesson-1-algorithms",
        )
        self.assertTrue(os.path.isdir(sec1_dir), f"Directory missing: {sec1_dir}")

        files_mod1 = os.listdir(sec1_dir)
        # Should have video, subtitle, and attachment
        mp4_files = [f for f in files_mod1 if f.endswith(".mp4")]
        sub_files = [f for f in files_mod1 if f.endswith(".vtt") or f.endswith(".srt")]
        pdf_files = [f for f in files_mod1 if f.endswith(".pdf")]

        self.assertEqual(len(mp4_files), 1)
        self.assertEqual(len(sub_files), 1)
        self.assertEqual(len(pdf_files), 1)

        # Check file content
        with open(os.path.join(sec1_dir, mp4_files[0]), "rb") as f:
            self.assertEqual(f.read(), b"VIDEO_DATA_01")

        with open(os.path.join(sec1_dir, pdf_files[0]), "rb") as f:
            self.assertEqual(f.read(), b"%PDF-1.4 dummy pdf")

        # Verify restricted media was NOT requested
        # 'vid_restricted' had only_on_web=True
        # 'vid_hls_only' had only HLS streams
        for called_url in mock_get_calls:
            self.assertNotIn("restricted", called_url.lower())
            self.assertNotIn("hls", called_url.lower())

    @patch("time.sleep", return_value=None)
    @patch("edx_provider.EdxClient.get_course_blocks")
    def test_e2e_idempotency_preserves_existing_files(self, mock_blocks, mock_sleep):
        """Verify rerun skips already completed files with zero redundant network requests."""
        mock_blocks.return_value = VALID_EDX_BLOCKS

        call_count = [0]

        def mock_get(url, *args, **kwargs):
            call_count[0] += 1
            return self._create_mock_asset_response(b"FILE_CONTENT")

        with patch("requests.Session.get", side_effect=mock_get):
            # First run: downloads all resources
            ret1 = edx_dl.main([
                "--path", self.output_path,
                "--sub-lang", "vi",
                EDX_COURSE_KEY,
            ])
            self.assertEqual(ret1, 0)
            initial_calls = call_count[0]
            self.assertGreater(initial_calls, 0)

            # Second run on same directory: should skip existing files
            call_count[0] = 0
            ret2 = edx_dl.main([
                "--path", self.output_path,
                "--sub-lang", "vi",
                EDX_COURSE_KEY,
            ])
            self.assertEqual(ret2, 0)
            # ZERO asset calls made on second run
            self.assertEqual(call_count[0], 0)

    @patch("time.sleep", return_value=None)
    @patch("edx_provider.EdxClient.get_course_blocks")
    def test_e2e_overwrite_flag_redownloads(self, mock_blocks, mock_sleep):
        """Verify --overwrite flag forces redownload of existing files."""
        mock_blocks.return_value = VALID_EDX_BLOCKS

        def mock_get_v1(url, *args, **kwargs):
            return self._create_mock_asset_response(b"VERSION_1")

        with patch("requests.Session.get", side_effect=mock_get_v1):
            ret1 = edx_dl.main([
                "--path", self.output_path,
                EDX_COURSE_KEY,
            ])
            self.assertEqual(ret1, 0)

        # Run again with --overwrite and updated mock content
        def mock_get_v2(url, *args, **kwargs):
            return self._create_mock_asset_response(b"VERSION_2")

        with patch("requests.Session.get", side_effect=mock_get_v2):
            ret2 = edx_dl.main([
                "--path", self.output_path,
                "--overwrite",
                EDX_COURSE_KEY,
            ])
            self.assertEqual(ret2, 0)

        # Check that file content was updated to VERSION_2
        course_dir = os.path.join(self.output_path, "edx", "TestOrg-CS101-2026_T1")
        sec1_dir = os.path.join(course_dir, "01_01_week-1-fundamentals", "01_01_lesson-1-algorithms")
        mp4_file = [f for f in os.listdir(sec1_dir) if f.endswith(".mp4")][0]
        with open(os.path.join(sec1_dir, mp4_file), "rb") as f:
            self.assertEqual(f.read(), b"VERSION_2")

    @patch("time.sleep", return_value=None)
    def test_atomic_download_partial_file_cleanup_on_failure(self, mock_sleep):
        """Verify partial file (.part) is deleted on error and final file is never corrupted."""
        session = MagicMock()
        downloader = edx_provider.EdxDownloader(
            session=session,
            path=self.output_path,
            max_retries=1,
        )

        target_file = os.path.join(self.output_path, "test_lecture.mp4")
        part_file = f"{target_file}.part"

        # Simulate failure during streaming
        resp = MagicMock()
        resp.status_code = 200
        resp.url = "https://edx-video.net/video.mp4"
        resp.history = []

        def failing_chunks(chunk_size):
            yield b"partial data"
            raise requests.exceptions.ChunkedEncodingError("Connection dropped")

        resp.iter_content.side_effect = failing_chunks
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False

        with patch("requests.Session.get", return_value=resp):
            res = workflow.PlannedResource(
                url="https://edx-video.net/video.mp4",
                fmt="mp4",
                filename=target_file,
                title="Test Lecture",
            )
            success = downloader.download_resource(res)

        self.assertFalse(success)
        # Verify both target file and .part file do not exist
        self.assertFalse(os.path.exists(target_file))
        self.assertFalse(os.path.exists(part_file))
        self.assertEqual(downloader.summary.failed, 1)

    @patch("time.sleep", return_value=None)
    def test_auth_failure_401_403_no_retry(self, mock_sleep):
        """Verify 401 or 403 returns failure immediately without retrying."""
        session = MagicMock()
        resp = self._create_mock_asset_response(status_code=403)
        session.get.return_value = resp

        downloader = edx_provider.EdxDownloader(
            session=session,
            path=self.output_path,
            max_retries=3,
        )

        res = workflow.PlannedResource(
            url="https://courses.edx.org/api/subtitles/123",
            fmt="vtt",
            filename=os.path.join(self.output_path, "sub.vtt"),
            title="Subtitles",
        )
        success = downloader.download_resource(res)

        self.assertFalse(success)
        # Crucial check: called exactly once, no retry attempts
        self.assertEqual(session.get.call_count, 1)
        self.assertEqual(downloader.summary.failed, 1)

    @patch("time.sleep", return_value=None)
    def test_rate_limit_429_retries_and_succeeds(self, mock_sleep):
        """Verify HTTP 429 respects Retry-After and retries successfully."""
        session = MagicMock()
        downloader = edx_provider.EdxDownloader(
            session=session,
            path=self.output_path,
            max_retries=2,
        )

        resp_429 = self._create_mock_asset_response(
            status_code=429,
            headers={"Retry-After": "1"},
        )
        resp_200 = self._create_mock_asset_response(content=b"OK", status_code=200)

        get_mock = MagicMock(side_effect=[resp_429, resp_200])

        with patch("requests.Session.get", get_mock):
            res = workflow.PlannedResource(
                url="https://edx-video.net/video.mp4",
                fmt="mp4",
                filename=os.path.join(self.output_path, "video.mp4"),
                title="Video",
            )
            success = downloader.download_resource(res)

        self.assertTrue(success)
        self.assertEqual(get_mock.call_count, 2)
        mock_sleep.assert_called_once_with(1)
        self.assertEqual(downloader.summary.downloaded, 1)

    def test_ssrf_and_unsafe_url_protection(self):
        """Verify unsafe scheme/host URLs are rejected prior to making any network calls."""
        session = MagicMock()
        downloader = edx_provider.EdxDownloader(session=session, path=self.output_path)

        unsafe_urls = [
            "http://courses.edx.org/insecure.mp4",
            "https://127.0.0.1/admin.mp4",
            "https://169.254.169.254/latest/meta-data",
            "https://evil-attacker.com/malware.mp4",
        ]

        for unsafe_url in unsafe_urls:
            with patch("requests.Session.get") as mock_get:
                res = workflow.PlannedResource(
                    url=unsafe_url,
                    fmt="mp4",
                    filename=os.path.join(self.output_path, "unsafe.mp4"),
                    title="Unsafe",
                )
                success = downloader.download_resource(res)
                self.assertFalse(success)
                mock_get.assert_not_called()

    def test_redirect_to_unsafe_host_rejected(self):
        """Verify redirect to an unsafe domain is detected and rejected."""
        session = MagicMock()
        downloader = edx_provider.EdxDownloader(session=session, path=self.output_path)

        resp = MagicMock()
        resp.status_code = 200
        # Final URL points to untrusted host
        resp.url = "https://untrusted-host.com/video.mp4"
        resp.history = []
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False

        with patch("requests.Session.get", return_value=resp):
            res = workflow.PlannedResource(
                url="https://edx-video.net/initial.mp4",
                fmt="mp4",
                filename=os.path.join(self.output_path, "redirect.mp4"),
                title="Redirect",
            )
            success = downloader.download_resource(res)

        self.assertFalse(success)
        self.assertEqual(downloader.summary.failed, 1)

    def test_cookie_isolation_for_external_cdn(self):
        """Verify edX session cookies are not sent when downloading assets from external CDNs."""
        session = requests.Session()
        session.cookies.set("sessionid", "SECRET_EDX_COOKIE", domain=".edx.org")

        downloader = edx_provider.EdxDownloader(session=session, path=self.output_path)

        captured_sessions = []

        def capture_get(self_session, url, *args, **kwargs):
            captured_sessions.append(dict(self_session.cookies))
            return self._create_mock_asset_response(b"DATA")

        # Download from external CDN (edx-video.net)
        with patch.object(requests.Session, "get", capture_get):
            res = workflow.PlannedResource(
                url="https://edx-video.net/lecture.mp4",
                fmt="mp4",
                filename=os.path.join(self.output_path, "lecture.mp4"),
                title="Lecture",
            )
            downloader.download_resource(res)

        self.assertEqual(len(captured_sessions), 1)
        # Ensure SECRET_EDX_COOKIE was NOT in the session cookies used for external CDN
        self.assertNotIn("sessionid", captured_sessions[0])

    @patch("edx_provider.EdxClient.get_course_blocks")
    def test_empty_course_manifest_exits_zero(self, mock_blocks):
        """Verify course with 0 downloadable resources logs notice and exits 0 cleanly."""
        mock_blocks.return_value = EMPTY_EDX_BLOCKS

        ret = edx_dl.main([
            "--path", self.output_path,
            "course-v1:TestOrg+EMPTY+2026",
        ])
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
