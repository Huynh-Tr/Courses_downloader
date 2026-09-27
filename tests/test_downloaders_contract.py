import tests  # noqa: F401
"""
Characterization tests for download wrappers and retry/resume semantics.
Covers parallel wrappers (ConsecutiveDownloader, ParallelDownloader),
Downloader retry/timeout/cleanup handling, and NativeDownloader Range requests.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

import requests

import downloaders
import parallel


class TestParallelWrappers(unittest.TestCase):
    """Test ConsecutiveDownloader and ParallelDownloader execution and callback behavior."""

    def test_consecutive_downloader_calls_callback_and_returns_result(self):
        fake_file_dl = MagicMock()
        fake_file_dl.download.return_value = True

        cd = parallel.ConsecutiveDownloader(fake_file_dl)
        callback = MagicMock()

        result = cd.download(callback, "https://example.test/f.mp4", "/tmp/f.mp4", resume=False)

        self.assertTrue(result)
        fake_file_dl.download.assert_called_once_with(
            "https://example.test/f.mp4", "/tmp/f.mp4", resume=False
        )
        callback.assert_called_once_with("https://example.test/f.mp4", True)

        # join is a safe no-op
        cd.join()

    def test_parallel_downloader_executes_async_and_joins(self):
        fake_file_dl = MagicMock()
        fake_file_dl.download.return_value = True

        pd = parallel.ParallelDownloader(fake_file_dl, processes=2)
        callback = MagicMock()

        async_result = pd.download(callback, "https://example.test/f1.mp4", "/tmp/f1.mp4", resume=False)
        pd.join()

        self.assertIsNotNone(async_result)
        fake_file_dl.download.assert_called_once_with(
            "https://example.test/f1.mp4", "/tmp/f1.mp4", resume=False
        )
        callback.assert_called_once_with("https://example.test/f1.mp4", True)


class StubDownloader(downloaders.Downloader):
    """Subclass of Downloader with programmable behavior for testing timeout/retry loops."""

    def __init__(self, outcomes):
        super().__init__()
        self.outcomes = list(outcomes)
        self.call_count = 0
        self.received_timeouts = []

    def _start_download(self, url, filename, resume, timeout_seconds=None):
        self.call_count += 1
        self.received_timeouts.append(timeout_seconds)
        if not self.outcomes:
            return True
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class TestDownloaderRetryPolicy(unittest.TestCase):
    """Test Downloader.download() timeout handling, retry count, and partial file cleanup."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_retry_on_single_timeout_then_success(self):
        fn = os.path.join(self.path, "test_retry.mp4")
        with open(fn, "wb") as f:
            f.write(b"partial")

        # First attempt times out, second succeeds
        stub = StubDownloader([downloaders.DownloadTimeoutError("timeout"), True])
        result = stub.download("https://example.test/file.mp4", fn, resume=False)

        self.assertTrue(result)
        self.assertEqual(stub.call_count, 2)
        # Timeout configured as 30s
        self.assertEqual(stub.received_timeouts[0], 30)

    def test_max_timeout_attempts_exceeded_returns_false(self):
        fn = os.path.join(self.path, "test_fail.mp4")
        with open(fn, "wb") as f:
            f.write(b"partial")

        # Both attempt 1 and attempt 2 time out (retries=1 means 2 total attempts)
        stub = StubDownloader([
            downloaders.DownloadTimeoutError("to1"),
            downloaders.DownloadTimeoutError("to2"),
        ])
        result = stub.download("https://example.test/file.mp4", fn, resume=False)

        self.assertFalse(result)
        self.assertEqual(stub.call_count, 2)
        # Partial file was removed because resume=False
        self.assertFalse(os.path.exists(fn))

    def test_requests_timeout_exception_handling(self):
        fn = os.path.join(self.path, "req_timeout.mp4")
        with open(fn, "wb") as f:
            f.write(b"data")

        stub = StubDownloader([
            requests.exceptions.Timeout("connection timeout"),
            True,
        ])
        result = stub.download("https://example.test/file.mp4", fn, resume=False)

        self.assertTrue(result)
        self.assertEqual(stub.call_count, 2)

    def test_keyboard_interrupt_removes_file_unless_resume(self):
        fn_no_resume = os.path.join(self.path, "no_resume.mp4")
        with open(fn_no_resume, "wb") as f:
            f.write(b"interrupted")

        stub1 = StubDownloader([KeyboardInterrupt()])
        with self.assertRaises(KeyboardInterrupt):
            stub1.download("https://example.test/f.mp4", fn_no_resume, resume=False)
        self.assertFalse(os.path.exists(fn_no_resume))

        fn_resume = os.path.join(self.path, "with_resume.mp4")
        with open(fn_resume, "wb") as f:
            f.write(b"preserve_me")

        stub2 = StubDownloader([KeyboardInterrupt()])
        with self.assertRaises(KeyboardInterrupt):
            stub2.download("https://example.test/f.mp4", fn_resume, resume=True)
        # Preserved when resume is True
        self.assertTrue(os.path.exists(fn_resume))


class TestNativeDownloaderContract(unittest.TestCase):
    """Test NativeDownloader Range header construction and HTTP status handling."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_range_header_when_resume_and_file_exists(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 416  # Range Not Satisfiable -> already downloaded
        session.get.return_value = response

        nd = downloaders.NativeDownloader(session)
        fn = os.path.join(self.path, "resume_test.mp4")
        with open(fn, "wb") as f:
            f.write(b"1234567890")  # 10 bytes

        result = nd._start_download("https://example.test/video.mp4", fn, resume=True)

        self.assertTrue(result)
        session.get.assert_called_once()
        headers = session.get.call_args[1]["headers"]
        self.assertEqual(headers.get("Range"), "bytes=10-")

    def test_no_range_header_when_file_does_not_exist(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-length": "0"}
        response.raw.read.return_value = b""
        session.get.return_value = response

        nd = downloaders.NativeDownloader(session)
        fn = os.path.join(self.path, "non_existent.mp4")

        result = nd._start_download("https://example.test/video.mp4", fn, resume=True)

        self.assertTrue(result)
        session.get.assert_called_once()
        headers = session.get.call_args[1]["headers"]
        self.assertNotIn("Range", headers)


if __name__ == "__main__":
    unittest.main()
