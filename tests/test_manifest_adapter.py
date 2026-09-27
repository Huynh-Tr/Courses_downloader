"""
Tests for neutral course models and legacy Coursera adapter (models.py).
Verifies immutability, validation, round-trip fidelity, and traversal equivalence.
"""

import tests  # noqa: F401
import unittest
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import models
import workflow
from tests.fixtures.sanitized_syllabus import (
    EMPTY_SYLLABUS,
    MULTI_MODULE_SYLLABUS,
    SINGLE_MODULE_SYLLABUS,
    SPECIAL_CHARS_SYLLABUS,
)


class TestNeutralModels(unittest.TestCase):
    """Test immutability, validation, and properties of neutral models."""

    def test_resource_immutability(self):
        res = models.Resource(
            index=0,
            format="mp4",
            title="Video",
            source="https://example.test/v.mp4",
        )
        with self.assertRaises(FrozenInstanceError):
            res.title = "New Title"  # type: ignore

    def test_resource_validation(self):
        with self.assertRaises(ValueError):
            models.Resource(index=-1, format="mp4", title="t", source="http://a")
        with self.assertRaises(ValueError):
            models.Resource(index=0, format="", title="t", source="http://a")
        with self.assertRaises(ValueError):
            models.Resource(index=0, format="mp4", title="t", source="")

    def test_lecture_and_section_immutability(self):
        lec = models.Lecture(index=0, slug="lec-1", title="Lecture 1")
        with self.assertRaises(FrozenInstanceError):
            lec.slug = "other"  # type: ignore

        sec = models.Section(index=0, slug="sec-1", title="Section 1")
        with self.assertRaises(FrozenInstanceError):
            sec.title = "other"  # type: ignore

    def test_manifest_validation(self):
        with self.assertRaises(ValueError):
            models.CourseManifest(provider="", course_id="c1", slug="s1", title="t1")
        with self.assertRaises(ValueError):
            models.CourseManifest(provider="coursera", course_id="c1", slug="", title="t1")

    def test_infer_resource_kind(self):
        self.assertEqual(models.infer_resource_kind("mp4"), "video")
        self.assertEqual(models.infer_resource_kind("srt"), "subtitle")
        self.assertEqual(models.infer_resource_kind("vtt"), "subtitle")
        self.assertEqual(models.infer_resource_kind("txt"), "transcript")
        self.assertEqual(models.infer_resource_kind("html"), "reading")
        self.assertEqual(models.infer_resource_kind("htm"), "reading")
        self.assertEqual(models.infer_resource_kind("ipynb"), "notebook")
        self.assertEqual(models.infer_resource_kind("pdf"), "document")
        self.assertEqual(models.infer_resource_kind("docx"), "document")
        self.assertEqual(models.infer_resource_kind("zip"), "document")
        self.assertEqual(models.infer_resource_kind("unknown_ext"), "generic")


class TestLegacyAdapter(unittest.TestCase):
    """Test legacy Coursera tuple conversion and round-trip fidelity."""

    def test_single_module_conversion(self):
        manifest = models.legacy_to_manifest(
            SINGLE_MODULE_SYLLABUS, class_name="single-course", course_id="c_123", title="Single Course"
        )
        self.assertEqual(manifest.provider, "coursera")
        self.assertEqual(manifest.slug, "single-course")
        self.assertEqual(manifest.course_id, "c_123")
        self.assertEqual(manifest.title, "Single Course")
        self.assertEqual(len(manifest.modules), 1)

        mod = manifest.modules[0]
        self.assertEqual(mod.slug, "week-1-introduction")
        self.assertEqual(len(mod.sections), 1)

        sec = mod.sections[0]
        self.assertEqual(sec.slug, "lesson-1-welcome")
        self.assertEqual(len(sec.lectures), 2)

        # Lecture 1: mp4, srt, txt
        lec1 = sec.lectures[0]
        self.assertEqual(lec1.slug, "01-welcome-lecture")
        self.assertEqual(len(lec1.resources), 3)
        self.assertEqual(lec1.resources[0].format, "mp4")
        self.assertEqual(lec1.resources[0].kind, "video")
        self.assertFalse(lec1.resources[0].is_in_memory)

        # Lecture 2: html (in-memory), pdf
        lec2 = sec.lectures[1]
        self.assertEqual(lec2.slug, "02-course-syllabus")
        self.assertEqual(len(lec2.resources), 2)
        html_res = lec2.resources[0]
        self.assertEqual(html_res.format, "html")
        self.assertEqual(html_res.kind, "reading")
        self.assertTrue(html_res.is_in_memory)
        self.assertNotIn("#inmemory#", html_res.source)
        self.assertTrue(html_res.legacy_url.startswith("#inmemory#"))

    def test_round_trip_fidelity_single_module(self):
        manifest = models.legacy_to_manifest(SINGLE_MODULE_SYLLABUS, "course-1")
        reconstructed = models.manifest_to_legacy(manifest)
        self.assertEqual(reconstructed, SINGLE_MODULE_SYLLABUS)

    def test_round_trip_fidelity_multi_module(self):
        manifest = models.legacy_to_manifest(MULTI_MODULE_SYLLABUS, "course-2")
        reconstructed = models.manifest_to_legacy(manifest)
        self.assertEqual(reconstructed, MULTI_MODULE_SYLLABUS)

    def test_round_trip_fidelity_special_chars(self):
        manifest = models.legacy_to_manifest(SPECIAL_CHARS_SYLLABUS, "course-3")
        reconstructed = models.manifest_to_legacy(manifest)
        self.assertEqual(reconstructed, SPECIAL_CHARS_SYLLABUS)

    def test_round_trip_fidelity_empty(self):
        manifest = models.legacy_to_manifest(EMPTY_SYLLABUS, "empty-course")
        self.assertEqual(manifest.total_resources, 0)
        reconstructed = models.manifest_to_legacy(manifest)
        self.assertEqual(reconstructed, EMPTY_SYLLABUS)

    def test_malformed_legacy_inputs_raise_value_error(self):
        with self.assertRaises(ValueError):
            models.legacy_to_manifest("not a list", "c")
        with self.assertRaises(ValueError):
            models.legacy_to_manifest([("mod-1",)], "c")  # missing sections
        with self.assertRaises(ValueError):
            models.legacy_to_manifest([("mod-1", "not a list")], "c")
        with self.assertRaises(ValueError):
            models.legacy_to_manifest([("mod-1", [("sec-1", "not a list")])], "c")
        with self.assertRaises(ValueError):
            models.legacy_to_manifest([("mod-1", [("sec-1", [("lec-1", "not a dict")])])], "c")

    def test_traversal_equivalence_with_legacy_workflow(self):
        args = SimpleNamespace(
            file_formats=["all"],
            lecture_filter=None,
            resource_filter=None,
            section_filter=None,
            verbose_dirs=False,
            combined_section_lectures_nums=False,
        )
        for syllabus in (SINGLE_MODULE_SYLLABUS, MULTI_MODULE_SYLLABUS, SPECIAL_CHARS_SYLLABUS):
            manifest = models.legacy_to_manifest(syllabus, "c")
            manifest_resources = [
                (res.format, res.legacy_url, res.title) for m, s, l, res in manifest.iter_resources()
            ]
            legacy_resources = [
                (r.fmt, r.url, r.title)
                for m, s, l, r in workflow._walk_modules(syllabus, "c", "/tmp", [], args)
            ]
            self.assertEqual(manifest_resources, legacy_resources)


if __name__ == "__main__":
    unittest.main()
