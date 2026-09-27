import tests  # noqa: F401
"""
Characterization tests for pure utility and formatting functions.
These functions have no external I/O or network dependencies.
"""

import os
import sys
import time
import unittest

import general
import coursera_dl
import utils
import workflow


class TestSlugAndUrlParsing(unittest.TestCase):
    """Test URL to course slug extraction across CLI and GUI helpers."""

    def test_extract_course_slug_standard_url(self):
        url = "https://www.coursera.org/learn/machine-learning"
        self.assertEqual(coursera_dl.extract_course_slug(url), "machine-learning")

    def test_extract_course_slug_with_subpath(self):
        url = "https://www.coursera.org/learn/deep-neural-network/home/week/2"
        self.assertEqual(coursera_dl.extract_course_slug(url), "deep-neural-network")

    def test_extract_course_slug_with_query_params(self):
        url = "https://www.coursera.org/learn/nlp-intro?specialization=deep-learning"
        self.assertEqual(coursera_dl.extract_course_slug(url), "nlp-intro")

    def test_extract_course_slug_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            coursera_dl.extract_course_slug("https://example.com/not-coursera")

    def test_urltoclassname_slug_passthrough(self):
        self.assertEqual(general.urltoclassname("machine-learning"), "machine-learning")
        self.assertEqual(general.urltoclassname("model-thinking-001"), "model-thinking-001")

    def test_urltoclassname_standard_urls(self):
        self.assertEqual(
            general.urltoclassname("https://www.coursera.org/learn/model-thinking"),
            "model-thinking",
        )
        self.assertEqual(
            general.urltoclassname("https://www.coursera.org/learn/model-thinking/home/week/1"),
            "model-thinking",
        )
        self.assertEqual(
            general.urltoclassname("https://www.coursera.org/learn/neural-networks?specialization=deep-learning"),
            "neural-networks",
        )

    def test_urltoclassname_invalid_returns_empty(self):
        self.assertEqual(general.urltoclassname("https://other-site.org/course/123"), "")


class TestFilenameCleaning(unittest.TestCase):
    """Test filename sanitization behavior."""

    def test_clean_filename_forbidden_chars_replaced(self):
        raw = 'Intro: "Week 1" / Section <A> & B? *C* | Test \\ Done'
        cleaned = utils.clean_filename(raw, minimal_change=False)
        # Colons, slashes, quotes, angle brackets, pipes, question marks, asterisks -> replaced with '-'
        for forbidden in [':', '"', '/', '<', '>', '|', '?', '*']:
            self.assertNotIn(forbidden, cleaned)
        # Spaces converted to underscores
        self.assertNotIn(" ", cleaned)

    def test_clean_filename_trailing_dots_and_spaces_removed(self):
        raw = "My Course Lecture . . "
        cleaned = utils.clean_filename(raw, minimal_change=False)
        self.assertFalse(cleaned.endswith("."))
        self.assertFalse(cleaned.endswith(" "))

    def test_clean_filename_minimal_change(self):
        raw = "Lesson 1: Intro / Setup"
        cleaned = utils.clean_filename(raw, minimal_change=True)
        self.assertEqual(cleaned, "Lesson 1- Intro - Setup")

    def test_unescape_html_entities(self):
        raw = "Machine Learning &amp; Deep Learning &quot;Basics&quot;"
        self.assertEqual(utils.unescape_html(raw), 'Machine Learning & Deep Learning "Basics"')


class TestFormattingHelpers(unittest.TestCase):
    """Test section and resource formatting functions in workflow."""

    def test_format_section_standard(self):
        sec = workflow.format_section(1, "introduction", "ml-course", verbose_dirs=False)
        self.assertEqual(sec, "01_introduction")

    def test_format_section_verbose(self):
        sec = workflow.format_section(2, "advanced", "ml-course", verbose_dirs=True)
        self.assertEqual(sec, "ML-COURSE_02_advanced")

    def test_format_resource_with_and_without_title(self):
        with_title = workflow.format_resource(1, "welcome", "Overview", "mp4")
        self.assertEqual(with_title, "01_welcome_Overview.mp4")

        without_title = workflow.format_resource(2, "notes", "", "pdf")
        self.assertEqual(without_title, "02_notes.pdf")

    def test_format_combine_number_resource(self):
        res = workflow.format_combine_number_resource(1, 2, "lec-intro", "Welcome", "mp4")
        self.assertEqual(res, "01_02_lec-intro_Welcome.mp4")

    def test_get_lecture_filename(self):
        section_dir = "/tmp/downloads/01_intro"
        normal = workflow.get_lecture_filename(
            combined_section_lectures_nums=False,
            section_dir=section_dir,
            secnum=0,
            lecnum=0,
            lecname="welcome",
            title="Intro",
            fmt="mp4",
        )
        self.assertEqual(normal, os.path.join(section_dir, "01_welcome_Intro.mp4"))

        combined = workflow.get_lecture_filename(
            combined_section_lectures_nums=True,
            section_dir=section_dir,
            secnum=0,
            lecnum=0,
            lecname="welcome",
            title="Intro",
            fmt="mp4",
        )
        self.assertEqual(combined, os.path.join(section_dir, "01_01_welcome_Intro.mp4"))


class TestFilteringAndStatusHelpers(unittest.TestCase):
    """Test skip_format_url and is_course_complete heuristics."""

    def test_skip_format_url_empty_format(self):
        self.assertTrue(workflow.skip_format_url("", "https://example.test/file"))

    def test_skip_format_url_mailto_and_localhost(self):
        self.assertTrue(workflow.skip_format_url("mp4", "mailto:student@example.test"))
        self.assertTrue(workflow.skip_format_url("mp4", "http://localhost:8000/video.mp4"))

    def test_skip_format_url_valid_formats_accepted(self):
        for fmt in ["mp4", "pdf", "txt", "srt", "html", "htm", "zip", "csv", "xlsx", "ipynb", "json"]:
            self.assertFalse(
                workflow.skip_format_url(fmt, f"https://example.test/content/file.{fmt}"),
                f"Expected format '{fmt}' to NOT be skipped",
            )

    def test_skip_format_url_non_simple_format_skipped(self):
        self.assertTrue(workflow.skip_format_url("mp4?query=1", "https://example.test/file"))

    def test_skip_format_url_empty_or_root_path(self):
        # When a format is not in RE_VALID_FORMATS, root or empty path is skipped (True)
        self.assertTrue(workflow.skip_format_url("unknown_fmt", "https://example.test/"))
        self.assertTrue(workflow.skip_format_url("unknown_fmt", "https://example.test"))
        # But for recognized formats in RE_VALID_FORMATS (e.g. mp4), match succeeds before path check (False)
        self.assertFalse(workflow.skip_format_url("mp4", "https://example.test/"))

    def test_is_course_complete_over_30_days(self):
        old_time = time.time() - (31 * 86400)
        self.assertTrue(utils.is_course_complete(old_time))

    def test_is_course_complete_recent_update(self):
        recent_time = time.time() - (5 * 86400)
        self.assertFalse(utils.is_course_complete(recent_time))

    def test_is_course_complete_negative_time(self):
        self.assertFalse(utils.is_course_complete(-1))

    def test_normalize_path_non_windows(self):
        if sys.platform != "win32":
            p = "/tmp/my_dir/course"
            self.assertEqual(utils.normalize_path(p), p)


if __name__ == "__main__":
    unittest.main()
