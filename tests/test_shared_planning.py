"""
Tests for shared download planning seam and CourseraDownloader manifest integration (workflow.py).
Verifies pure planning equivalence, options matrix, and download_manifest execution.
"""

import os
import tempfile
import tests  # noqa: F401
import unittest
from types import SimpleNamespace

import models
import workflow
from tests.fixtures.sanitized_syllabus import (
    EMPTY_SYLLABUS,
    MULTI_MODULE_SYLLABUS,
    SINGLE_MODULE_SYLLABUS,
    SPECIAL_CHARS_SYLLABUS,
)


class SpyDownloader:
    """Mock downloader capturing calls and results without network I/O."""

    def __init__(self, result=True):
        self.calls = []
        self.joined = False
        self.result = result

    def download(self, callback, url, filename, resume=False):
        self.calls.append({
            "url": url,
            "filename": filename,
            "resume": resume,
        })
        if callback:
            callback(url, self.result)

    def join(self):
        self.joined = True


def _make_args(**kwargs):
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


class TestSharedPlanningSeam(unittest.TestCase):
    """Test plan_downloads pure planning behavior across inputs and options."""

    def test_plan_downloads_accepts_both_legacy_and_manifest(self):
        args = _make_args()
        plan_from_legacy = workflow.plan_downloads(
            SINGLE_MODULE_SYLLABUS, class_name="c1", path="/out", args=args
        )

        manifest = models.legacy_to_manifest(SINGLE_MODULE_SYLLABUS, class_name="c1")
        plan_from_manifest = workflow.plan_downloads(
            manifest, class_name="c1", path="/out", args=args
        )

        self.assertEqual(plan_from_legacy, plan_from_manifest)

    def test_plan_downloads_empty_syllabus(self):
        args = _make_args()
        plan = workflow.plan_downloads(EMPTY_SYLLABUS, class_name="empty", path="/out", args=args)
        self.assertEqual(plan, [])

    def test_plan_downloads_pure_equivalence_with_legacy_walk(self):
        args = _make_args()
        for syllabus in (SINGLE_MODULE_SYLLABUS, MULTI_MODULE_SYLLABUS, SPECIAL_CHARS_SYLLABUS):
            planned_modules = workflow.plan_downloads(syllabus, "c", "/tmp/base", args=args)
            planned_resources = [
                (res.filename, res.url, res.fmt)
                for mod in planned_modules
                for sec in mod.sections
                for res in sec.resources
            ]

            legacy_items = list(workflow._walk_modules(syllabus, "c", "/tmp/base", [], args))
            legacy_resources = [
                (workflow.normalize_path(l.filename(r.fmt, r.title)), r.url, r.fmt)
                for m, s, l, r in legacy_items
            ]

            self.assertEqual(planned_resources, legacy_resources)

    def test_options_matrix_equivalence(self):
        manifest = models.legacy_to_manifest(MULTI_MODULE_SYLLABUS, "multi-test")

        variations = [
            {"verbose_dirs": True},
            {"combined_section_lectures_nums": True},
            {"file_formats": ["mp4", "srt"]},
            {"ignored_formats": ["txt", "pdf"]},
            {"section_filter": "setup"},
            {"lecture_filter": "overview"},
            {"resource_filter": "Overview"},
        ]

        for var in variations:
            ignored = var.pop("ignored_formats", [])
            args = _make_args(**var)

            planned_modules = workflow.plan_downloads(manifest, "multi-test", "/tmp/out", ignored, args)
            planned_flat = [
                (res.filename, res.url, res.fmt)
                for mod in planned_modules
                for sec in mod.sections
                for res in sec.resources
            ]

            legacy_items = list(workflow._walk_modules(MULTI_MODULE_SYLLABUS, "multi-test", "/tmp/out", ignored, args))
            legacy_flat = [
                (workflow.normalize_path(l.filename(r.fmt, r.title)), r.url, r.fmt)
                for m, s, l, r in legacy_items
            ]

            self.assertEqual(planned_flat, legacy_flat, f"Mismatch on variation {var}")


class TestCourseraDownloaderManifestExecution(unittest.TestCase):
    """Test execution equivalence between legacy download_modules and download_manifest."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_download_manifest_produces_identical_calls_as_legacy_modules(self):
        args = _make_args()

        # Run 1: legacy tuples via download_modules
        spy_legacy = SpyDownloader()
        dir_legacy = os.path.join(self.path, "legacy_run")
        dl_legacy = workflow.CourseraDownloader(spy_legacy, args, "course_a", path=dir_legacy)
        comp_legacy = dl_legacy.download_modules(MULTI_MODULE_SYLLABUS)

        # Run 2: neutral manifest via download_manifest
        manifest = models.legacy_to_manifest(MULTI_MODULE_SYLLABUS, "course_a")
        spy_manifest = SpyDownloader()
        dir_manifest = os.path.join(self.path, "manifest_run")
        dl_manifest = workflow.CourseraDownloader(spy_manifest, args, "course_a", path=dir_manifest)
        comp_manifest = dl_manifest.download_manifest(manifest)

        # 1. Same completion status
        self.assertEqual(comp_legacy, comp_manifest)

        # 2. Both joined downloader
        self.assertTrue(spy_legacy.joined)
        self.assertTrue(spy_manifest.joined)

        # 3. Exactly same relative target files called
        calls_legacy_rel = [
            (c["url"], os.path.relpath(c["filename"], dir_legacy), c["resume"])
            for c in spy_legacy.calls
        ]
        calls_manifest_rel = [
            (c["url"], os.path.relpath(c["filename"], dir_manifest), c["resume"])
            for c in spy_manifest.calls
        ]
        self.assertEqual(calls_legacy_rel, calls_manifest_rel)

        # 4. In-memory reading exists in both output directories
        inmem_rel = os.path.join(
            "course_a",
            "01_01-fundamentals",
            "02_sec-2-setup",
            "01_lec-3-installation_Installation Guide.html",
        )
        self.assertTrue(os.path.exists(os.path.join(dir_legacy, inmem_rel)))
        self.assertTrue(os.path.exists(os.path.join(dir_manifest, inmem_rel)))

    def test_direct_provider_manifest_download(self):
        """Simulate a future provider (e.g. edX) constructing a CourseManifest and downloading."""
        provider_manifest = models.CourseManifest(
            provider="edx",
            course_id="course-v1:Org+Demo+Run",
            slug="demo-course",
            title="Demo Course",
            modules=(
                models.Module(
                    index=0,
                    slug="chapter-1",
                    title="Chapter 1",
                    sections=(
                        models.Section(
                            index=0,
                            slug="seq-1",
                            title="Sequence 1",
                            lectures=(
                                models.Lecture(
                                    index=0,
                                    slug="video-1",
                                    title="Video 1",
                                    resources=(
                                        models.Resource(
                                            index=0,
                                            format="mp4",
                                            title="Lecture Video",
                                            source="https://cdn.edx.test/video.mp4",
                                            kind="video",
                                        ),
                                        models.Resource(
                                            index=1,
                                            format="srt",
                                            title="English Subtitles",
                                            source="https://cdn.edx.test/sub.srt",
                                            kind="subtitle",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        spy = SpyDownloader()
        args = _make_args()
        cdl = workflow.CourseraDownloader(spy, args, "demo-course", path=self.path)

        completed = cdl.download_manifest(provider_manifest)

        self.assertTrue(spy.joined)
        self.assertEqual(len(spy.calls), 2)
        urls_called = [c["url"] for c in spy.calls]
        self.assertEqual(urls_called, ["https://cdn.edx.test/video.mp4", "https://cdn.edx.test/sub.srt"])

        expected_video_path = os.path.join(
            self.path,
            "demo-course",
            "01_chapter-1",
            "01_seq-1",
            "01_video-1_Lecture Video.mp4",
        )
        self.assertEqual(spy.calls[0]["filename"], workflow.normalize_path(expected_video_path))


if __name__ == "__main__":
    unittest.main()
