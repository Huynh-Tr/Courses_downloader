import tests  # noqa: F401
"""
Characterization tests for syllabus traversal and file path hierarchy generation.
Covers _iter_modules and _walk_modules across various flags and fixtures.
"""

import os
import unittest
from types import SimpleNamespace

import workflow
from tests.fixtures.sanitized_syllabus import (
    EMPTY_SYLLABUS,
    MULTI_MODULE_SYLLABUS,
    SINGLE_MODULE_SYLLABUS,
    SPECIAL_CHARS_SYLLABUS,
)


def _make_args(**kwargs):
    defaults = {
        "file_formats": ["all"],
        "lecture_filter": None,
        "resource_filter": None,
        "section_filter": None,
        "verbose_dirs": False,
        "combined_section_lectures_nums": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestWorkflowTraversal(unittest.TestCase):
    """Test module/section/lecture/resource hierarchy and path generation."""

    def test_single_module_default_paths(self):
        base_path = "/downloads"
        class_name = "test-course"
        args = _make_args()

        items = list(workflow._walk_modules(SINGLE_MODULE_SYLLABUS, class_name, base_path, [], args))
        self.assertEqual(len(items), 5)  # mp4, srt, txt, html, pdf

        # Check Module
        module, section, lecture, resource = items[0]
        self.assertEqual(module.name, "01_week-1-introduction")
        self.assertEqual(section.name, "00_lesson-1-welcome")
        self.assertEqual(
            section.dir,
            os.path.join(base_path, class_name, "01_week-1-introduction", "01_lesson-1-welcome"),
        )

        # Check individual filenames
        filenames = [l.filename(r.fmt, r.title) for m, s, l, r in items]
        expected_dir = os.path.join(base_path, class_name, "01_week-1-introduction", "01_lesson-1-welcome")
        expected_filenames = [
            os.path.join(expected_dir, "01_01-welcome-lecture_Welcome Video.mp4"),
            os.path.join(expected_dir, "01_01-welcome-lecture_Welcome Video_en.srt"),
            os.path.join(expected_dir, "01_01-welcome-lecture_Welcome Video_en.txt"),
            os.path.join(expected_dir, "02_02-course-syllabus_Syllabus Reading.html"),
            os.path.join(expected_dir, "02_02-course-syllabus_Syllabus Document.pdf"),
        ]
        self.assertEqual(filenames, expected_filenames)

    def test_multi_module_hierarchy(self):
        args = _make_args()
        items = list(workflow._walk_modules(MULTI_MODULE_SYLLABUS, "multi-course", "/out", [], args))
        self.assertEqual(len(items), 7)

        modules_visited = list(dict.fromkeys(m.name for m, s, l, r in items))
        self.assertEqual(modules_visited, ["01_01-fundamentals", "02_02-advanced-topics"])

    def test_verbose_dirs_naming(self):
        args = _make_args(verbose_dirs=True)
        items = list(workflow._walk_modules(SINGLE_MODULE_SYLLABUS, "my-class", "/out", [], args))
        section = items[0][1]
        self.assertEqual(
            section.dir,
            os.path.join("/out", "my-class", "01_week-1-introduction", "MY-CLASS_01_lesson-1-welcome"),
        )

    def test_combined_section_lectures_nums(self):
        args = _make_args(combined_section_lectures_nums=True)
        items = list(workflow._walk_modules(SINGLE_MODULE_SYLLABUS, "c", "/out", [], args))
        filenames = [os.path.basename(l.filename(r.fmt, r.title)) for m, s, l, r in items]
        self.assertEqual(filenames[0], "01_01_01-welcome-lecture_Welcome Video.mp4")
        self.assertEqual(filenames[3], "01_02_02-course-syllabus_Syllabus Reading.html")

    def test_format_filtering_single_format(self):
        args = _make_args(file_formats=["mp4"])
        items = list(workflow._walk_modules(SINGLE_MODULE_SYLLABUS, "c", "/out", [], args))
        formats = [r.fmt for m, s, l, r in items]
        self.assertEqual(formats, ["mp4"])

    def test_ignored_formats_filtering(self):
        args = _make_args(file_formats=["all"])
        items = list(workflow._walk_modules(SINGLE_MODULE_SYLLABUS, "c", "/out", ["srt", "txt"], args))
        formats = [r.fmt for m, s, l, r in items]
        self.assertNotIn("srt", formats)
        self.assertNotIn("txt", formats)
        self.assertIn("mp4", formats)
        self.assertIn("html", formats)
        self.assertIn("pdf", formats)

    def test_section_filtering_regex(self):
        args = _make_args(section_filter="setup")
        items = list(workflow._walk_modules(MULTI_MODULE_SYLLABUS, "c", "/out", [], args))
        sections = [s.name for m, s, l, r in items]
        self.assertTrue(all("setup" in s for s in sections))
        self.assertEqual(len(items), 2)  # html, pdf in sec-2-setup

    def test_lecture_filtering_regex(self):
        args = _make_args(lecture_filter="architecture")
        items = list(workflow._walk_modules(MULTI_MODULE_SYLLABUS, "c", "/out", [], args))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][2].name, "lec-2-architecture")

    def test_resource_filter_regex(self):
        args = _make_args(resource_filter="Exercise")
        items = list(workflow._walk_modules(MULTI_MODULE_SYLLABUS, "c", "/out", [], args))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][3].title, "Exercise Notebook")

    def test_empty_syllabus(self):
        args = _make_args()
        items = list(workflow._walk_modules(EMPTY_SYLLABUS, "empty", "/out", [], args))
        self.assertEqual(len(items), 0)


if __name__ == "__main__":
    unittest.main()
