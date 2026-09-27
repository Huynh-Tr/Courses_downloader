"""
Unit tests for edX.org provider parser, security guards, client interface,
and integration with Phase 01 neutral CourseManifest planning.
"""

import tests  # noqa: F401 - triggers test network guard and shims
import unittest
from unittest.mock import MagicMock, patch

import edx_provider
import models
from tests.fixtures.edx_course_blocks import (
    EDX_COURSE_KEY,
    EDX_COURSES_URL,
    EDX_LEARNING_URL,
    EMPTY_EDX_BLOCKS,
    ENROLLMENT_NOT_ENROLLED,
    ENROLLMENT_SUCCESS,
    VALID_EDX_BLOCKS,
)
import workflow


class TestEdxIdentifiersAndSecurity(unittest.TestCase):
    """Test course key parsing, URL redaction, and SSRF security guards."""

    def test_extract_course_key_canonical_and_legacy(self):
        self.assertEqual(
            edx_provider.extract_edx_course_key("course-v1:HarvardX+CS50+X"),
            "course-v1:HarvardX+CS50+X",
        )
        self.assertEqual(
            edx_provider.extract_edx_course_key("MITx/6.00.1x/3T2026"),
            "MITx/6.00.1x/3T2026",
        )

    def test_extract_course_key_from_urls(self):
        self.assertEqual(
            edx_provider.extract_edx_course_key(EDX_LEARNING_URL),
            EDX_COURSE_KEY,
        )
        self.assertEqual(
            edx_provider.extract_edx_course_key(EDX_COURSES_URL),
            EDX_COURSE_KEY,
        )

    def test_extract_course_key_invalid_raises(self):
        invalid_inputs = [
            "",
            "   ",
            "not-a-course-key",
            "https://edx.org/search?q=python",
            "course-v1:single_token",
        ]
        for item in invalid_inputs:
            with self.assertRaises(ValueError):
                edx_provider.extract_edx_course_key(item)

    def test_course_key_to_slug(self):
        slug = edx_provider.course_key_to_slug(EDX_COURSE_KEY)
        self.assertEqual(slug, "TestOrg-CS101-2026_T1")

        legacy_slug = edx_provider.course_key_to_slug("MITx/6.00.1x/3T2026")
        self.assertEqual(legacy_slug, "MITx-6.00.1x-3T2026")

    def test_redact_url(self):
        raw = "https://edx-video.net/video.mp4?Signature=secret123&Expires=1790000000#t=10"
        redacted = edx_provider.redact_url(raw)
        self.assertEqual(redacted, "https://edx-video.net/video.mp4")
        self.assertNotIn("secret123", redacted)

    def test_is_safe_edx_url_allowed_domains(self):
        safe_urls = [
            "https://courses.edx.org/api/courses/v1/blocks",
            "https://learning.edx.org/course/xyz",
            "https://edx-video.net/video.mp4",
            "https://d3c33hcgiwev3.cloudfront.net/video.mp4",
            "https://mybucket.s3.amazonaws.com/files/notes.pdf",
        ]
        for url in safe_urls:
            self.assertTrue(edx_provider.is_safe_edx_url(url), f"Expected safe: {url}")

    def test_is_safe_edx_url_rejects_unsafe(self):
        unsafe_urls = [
            "http://courses.edx.org/insecure",           # HTTP not HTTPS
            "https://localhost/admin",                   # Localhost
            "https://127.0.0.1/steal",                   # Loopback IP
            "https://10.0.0.1/internal",                 # Private IP
            "https://192.168.1.1/router",                # Private IP
            "https://169.254.169.254/latest/meta-data",  # Link-local / AWS metadata
            "https://user:password@courses.edx.org",     # Credentials in URL
            "https://evil-attacker.com/malware.exe",     # Non-whitelisted domain
            "",                                          # Empty
        ]
        for url in unsafe_urls:
            self.assertFalse(edx_provider.is_safe_edx_url(url), f"Expected unsafe: {url}")


class TestEdxCourseParser(unittest.TestCase):
    """Test parsing Course Blocks into neutral CourseManifest and tracking skips."""

    def setUp(self):
        self.parser = edx_provider.EdxCourseParser(subtitle_language="vi")

    def test_parse_valid_blocks_produces_manifest_and_skips(self):
        manifest, skips = self.parser.parse(VALID_EDX_BLOCKS, EDX_COURSE_KEY)

        # 1. Manifest structure
        self.assertIsInstance(manifest, models.CourseManifest)
        self.assertEqual(manifest.provider, "edx")
        self.assertEqual(manifest.course_id, EDX_COURSE_KEY)
        self.assertEqual(manifest.title, "Introduction to Computer Science")

        # 2. Modules hierarchy (Chapter 1 and Chapter 2)
        self.assertEqual(len(manifest.modules), 2)
        mod1 = manifest.modules[0]
        self.assertEqual(mod1.title, "Week 1: Fundamentals")
        self.assertEqual(len(mod1.sections), 1)

        sec1 = mod1.sections[0]
        self.assertEqual(sec1.title, "Lesson 1: Algorithms")
        self.assertEqual(len(sec1.lectures), 1)

        unit1 = sec1.lectures[0]
        self.assertEqual(unit1.title, "Algorithm Basics")

        # 3. Resources inside Unit 1: Video (MP4) + Subtitle (VI) + PDF Attachment
        self.assertEqual(len(unit1.resources), 3)

        res_video = unit1.resources[0]
        self.assertEqual(res_video.kind, "video")
        self.assertEqual(res_video.format, "mp4")
        self.assertEqual(res_video.source, "https://edx-video.net/TestOrgCS101-V01_desktop.mp4")

        res_sub = unit1.resources[1]
        self.assertEqual(res_sub.kind, "subtitle")
        self.assertTrue(res_sub.format in ("srt", "vtt"))
        self.assertIn("lang=vi", res_sub.source)

        res_att = unit1.resources[2]
        self.assertEqual(res_att.kind, "document")
        self.assertEqual(res_att.format, "pdf")
        self.assertEqual(res_att.source, "https://edx-video.net/notes/week1_algorithms.pdf")

        # 4. Check Module 2 Video (low quality fallback selection)
        mod2 = manifest.modules[1]
        unit3 = mod2.sections[0].lectures[0]
        self.assertEqual(len(unit3.resources), 2)  # Low quality MP4 + English subtitle
        self.assertEqual(unit3.resources[0].source, "https://edx-video.net/arrays_low.mp4")

        # 5. Check Skipped Items
        # Expected skips:
        # - vid_restricted: only_on_web
        # - vid_hls_only: HLS/YouTube stream-only
        # - prob_01: problem block
        skip_categories = {s.category for s in skips}
        self.assertIn("RESTRICTED_MEDIA", skip_categories)
        self.assertIn("UNSUPPORTED_MEDIA", skip_categories)

        skip_reasons = {s.block_id: s.reason for s in skips}
        self.assertTrue(any("only_on_web" in r for r in skip_reasons.values()))
        self.assertTrue(any("HLS/YouTube" in r for r in skip_reasons.values()))
        self.assertTrue(any("problem" in r for r in skip_reasons.values()))

    def test_parse_empty_blocks(self):
        manifest, skips = self.parser.parse(EMPTY_EDX_BLOCKS, "course-v1:TestOrg+EMPTY+2026")
        self.assertEqual(len(manifest.modules), 0)
        self.assertEqual(manifest.total_resources, 0)
        self.assertEqual(len(skips), 0)

    def test_parse_malformed_blocks_raises_schema_error(self):
        with self.assertRaises(edx_provider.EdxSchemaError):
            self.parser.parse({}, "course-v1:Malformed")
        with self.assertRaises(edx_provider.EdxSchemaError):
            self.parser.parse({"blocks": {}}, "course-v1:NoCourseRoot")

    def test_integration_with_phase01_shared_planning(self):
        """Verify that edX CourseManifest works seamlessly with Phase 01 plan_downloads."""
        manifest, _ = self.parser.parse(VALID_EDX_BLOCKS, EDX_COURSE_KEY)
        planned = workflow.plan_downloads(manifest, class_name=manifest.slug, path="/downloads")

        self.assertEqual(len(planned), 2)
        p_mod1 = planned[0]
        self.assertTrue(p_mod1.name.startswith("01_"))
        self.assertEqual(len(p_mod1.sections), 1)

        p_sec1 = p_mod1.sections[0]
        self.assertEqual(len(p_sec1.resources), 3)

        filenames = [r.filename for r in p_sec1.resources]
        self.assertTrue(any(f.endswith(".mp4") for f in filenames))
        self.assertTrue(any(f.endswith(".srt") or f.endswith(".vtt") for f in filenames))
        self.assertTrue(any(f.endswith(".pdf") for f in filenames))


class TestEdxClient(unittest.TestCase):
    """Test HTTP client error handling, enrollment verification, and blocks retrieval."""

    def setUp(self):
        self.session = MagicMock()
        self.client = edx_provider.EdxClient(self.session)

    def test_get_enrollments_success(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = ENROLLMENT_SUCCESS
        self.session.get.return_value = resp

        enrollments = self.client.get_enrollments()
        self.assertEqual(len(enrollments), 2)

    def test_verify_enrollment_true_and_false(self):
        resp_success = MagicMock(status_code=200, json=lambda: ENROLLMENT_SUCCESS)
        self.session.get.return_value = resp_success
        self.assertTrue(self.client.verify_enrollment(EDX_COURSE_KEY))

        resp_not_enrolled = MagicMock(status_code=200, json=lambda: ENROLLMENT_NOT_ENROLLED)
        self.session.get.return_value = resp_not_enrolled
        self.assertFalse(self.client.verify_enrollment(EDX_COURSE_KEY))

    def test_get_enrollments_auth_error_401_403(self):
        resp = MagicMock(status_code=401)
        self.session.get.return_value = resp
        with self.assertRaises(edx_provider.EdxAuthError):
            self.client.get_enrollments()

    def test_get_enrollments_rate_limited_429(self):
        resp = MagicMock(status_code=429)
        self.session.get.return_value = resp
        with self.assertRaises(edx_provider.EdxRateLimitError):
            self.client.get_enrollments()

    def test_get_course_blocks_success(self):
        resp = MagicMock(status_code=200, json=lambda: VALID_EDX_BLOCKS)
        self.session.get.return_value = resp
        blocks = self.client.get_course_blocks(EDX_COURSE_KEY)
        self.assertIn("blocks", blocks)

    def test_get_course_blocks_not_found_404(self):
        resp = MagicMock(status_code=404)
        self.session.get.return_value = resp
        with self.assertRaises(edx_provider.EdxCourseNotFoundError):
            self.client.get_course_blocks("course-v1:Unknown+Course+Run")


if __name__ == "__main__":
    unittest.main()
