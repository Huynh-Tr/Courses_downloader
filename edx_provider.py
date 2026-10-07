"""
edX.org Course Provider: Parser, Client, and Neutral Manifest Generator.

Translates edX Course Blocks API structures into provider-neutral CourseManifest
records (CourseManifest -> Module -> Section -> Lecture -> Resource) without performing
unauthorized asset downloads or bypassing media restrictions.
"""

from dataclasses import dataclass, field
import ipaddress
import json
import logging
import os
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import parse_qs, quote, unquote, urlparse, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import requests

import models
import workflow


# --- Error Classes ---

class EdxError(Exception):
    """Base exception for edX provider errors."""
    category: str = "RESOURCE_FAILED"


class EdxAuthError(EdxError):
    """Raised when authentication credentials are missing, expired, or forbidden."""
    category: str = "AUTH_REQUIRED"


class EdxNotEnrolledError(EdxError):
    """Raised when the user is not enrolled in the requested course."""
    category: str = "NOT_ENROLLED_OR_FORBIDDEN"


class EdxCourseNotFoundError(EdxError):
    """Raised when the course key is not found on edX."""
    category: str = "COURSE_NOT_FOUND"


class EdxRateLimitError(EdxError):
    """Raised when edX returns HTTP 429 Too Many Requests."""
    category: str = "RATE_LIMITED"


class EdxSchemaError(EdxError):
    """Raised when the edX response does not match the expected schema."""
    category: str = "SCHEMA_UNSUPPORTED"


# --- Data Structures ---

@dataclass(frozen=True)
class SkippedItem:
    """Represents a course item that was skipped with a structured reason."""

    block_id: str
    title: str
    category: str  # RESTRICTED_MEDIA, UNSUPPORTED_MEDIA, UNSAFE_URL, etc.
    reason: str


# --- Identifier and URL Helpers ---

COURSE_KEY_RE = re.compile(
    r"^course-v1:([a-zA-Z0-9_\-\.]+)[\+]([a-zA-Z0-9_\-\.]+)[\+]([a-zA-Z0-9_\-\.]+)$"
)
LEGACY_COURSE_KEY_RE = re.compile(
    r"^([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)$"
)

# Standard video extension priority for direct MP4 selection in MVP
PREFERRED_VIDEO_PROFILES = (
    "desktop_mp4",
    "high",
    "fallback",
    "mobile_high",
    "mobile_low",
)

ATTACHMENT_EXTENSIONS = {
    "pdf", "zip", "tar", "gz", "tgz", "csv", "tsv", "xlsx", "xls",
    "docx", "doc", "pptx", "ppt", "txt", "py", "ipynb", "r", "sql",
}

DEFAULT_ALLOWED_HOSTS = {
    "courses.edx.org",
    "learning.edx.org",
    "edx.org",
    "courses.learn.mit.edu",
    "learn.mit.edu",
    "edx-video.net",
    "cloudfront.net",
    "s3.amazonaws.com",
}


def load_cookies_from_file(cookies_path: str, default_domain: str = ".edx.org") -> requests.cookies.RequestsCookieJar:
    """Load cookies from file (Netscape format or JSON format) into a RequestsCookieJar in memory."""
    import cookies
    return cookies.load_cookies_from_file(cookies_path, default_domain=default_domain)


def load_cookies_from_browser(browser_name: str, domain: str = "edx.org") -> requests.cookies.RequestsCookieJar:
    """Load edX session cookies from local browser profile into memory.

    Tries rookiepy first, then browser_cookie3.
    """
    import cookies
    try:
        return cookies.load_cookies_from_browser(browser_name, domain=domain)
    except Exception as e:
        raise EdxAuthError(
            f"Could not load cookies from browser '{browser_name}'. "
            "Ensure the browser profile exists or supply a Netscape cookies file using --cookies-file."
        ) from e


def extract_edx_course_key(identifier_or_url: str) -> str:
    """Extract and validate canonical edX course key from raw string or URL.

    Accepts:
      - Canonical course keys: 'course-v1:Org+Course+Run'
      - Learning URLs: 'https://learning.edx.org/course/course-v1:Org+Course+Run/home'
      - Courseware URLs: 'https://courses.edx.org/courses/course-v1:Org+Course+Run/courseware/...'
    """
    raw = identifier_or_url.strip()

    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        path_parts = [p for p in parsed.path.split("/") if p]
        for part in path_parts:
            unquoted = unquote(part)
            if COURSE_KEY_RE.match(unquoted):
                return unquoted
            if LEGACY_COURSE_KEY_RE.match(unquoted):
                return unquoted
        raise ValueError(f"Could not extract a valid edX course key from URL: {identifier_or_url}")

    if COURSE_KEY_RE.match(raw) or LEGACY_COURSE_KEY_RE.match(raw):
        return raw

    raise ValueError(
        f"Invalid edX course key format: {identifier_or_url!r}. "
        "Expected format 'course-v1:Org+Course+Run' or an official edX learning URL."
    )


def course_key_to_slug(course_key: str) -> str:
    """Convert a course key into a safe filesystem folder slug."""
    clean = course_key.replace("course-v1:", "")
    clean = re.sub(r"[+/:]", "-", clean)
    clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean)
    return clean.strip("._-") or "edx-course"


def redact_url(url: str) -> str:
    """Strip query strings and authentication tokens from URLs for safe logging."""
    try:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        return "[redacted-url]"


def get_candidate_urls(raw_url: str) -> List[str]:
    """Generate candidate URLs for CDN fallbacks (edx-video.net vs CloudFront)."""
    candidates = [raw_url]
    if "edx-video.net" in raw_url:
        candidates.append(raw_url.replace("edx-video.net", "d3tsb3m56iwvoq.cloudfront.net"))
    elif "d3tsb3m56iwvoq.cloudfront.net" in raw_url:
        candidates.append(raw_url.replace("d3tsb3m56iwvoq.cloudfront.net", "edx-video.net"))
    if "/transcoded/" in raw_url:
        candidates.reverse()
    return candidates


def is_safe_edx_url(url: str, allowed_hosts: Optional[Set[str]] = None) -> bool:
    """Validate that a URL is a secure HTTPS link and not an SSRF/private target."""
    if not url or not isinstance(url, str):
        return False
    try:
        parts = urlsplit(url.strip())
        if parts.scheme.lower() != "https":
            return False

        hostname = parts.hostname
        if not hostname:
            return False
        hostname = hostname.lower()

        # Reject credentials in URL
        if parts.username or parts.password:
            return False

        # Reject local and private IP addresses
        try:
            ip = ipaddress.ip_address(hostname)
            if (
                ip.is_loopback
                or ip.is_private
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False
        except ValueError:
            # hostname is a domain name, not a raw IP
            if hostname in ("localhost", "local", "broadcasthost"):
                return False

        # Check allowed hosts if specified
        allowed = allowed_hosts or DEFAULT_ALLOWED_HOSTS
        matched = False
        for base in allowed:
            if hostname == base or hostname.endswith("." + base):
                matched = True
                break
        return matched

    except Exception:
        return False


def _slugify(text: str) -> str:
    """Generate a clean URL/filename slug from title."""
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9_\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "item"


# --- edX Course Blocks Parser ---

class EdxCourseParser:
    """Pure parser converting edX Course Blocks API JSON into neutral CourseManifest."""

    def __init__(
        self,
        subtitle_language: str = "en",
        allowed_hosts: Optional[Set[str]] = None,
        base_url: Optional[str] = None,
    ):
        self._sub_lang = subtitle_language.lower().strip()
        self._allowed_hosts = allowed_hosts or DEFAULT_ALLOWED_HOSTS
        self._base_url = base_url.rstrip("/") if base_url else None

    def parse(
        self,
        blocks_data: Dict[str, Any],
        course_key: str,
        course_title: Optional[str] = None,
    ) -> Tuple[models.CourseManifest, List[SkippedItem]]:
        """Parse Course Blocks response into CourseManifest and list of SkippedItem."""
        if not isinstance(blocks_data, dict) or "blocks" not in blocks_data:
            raise EdxSchemaError("Malformed Course Blocks JSON: 'blocks' dictionary missing")

        blocks = blocks_data["blocks"]
        root_id = blocks_data.get("root")

        if not root_id or root_id not in blocks:
            # Fallback: search for block of type 'course'
            course_candidates = [
                b for b in blocks.values() if b.get("type") == "course"
            ]
            if not course_candidates:
                raise EdxSchemaError("No 'course' root block found in Course Blocks data")
            root_block = course_candidates[0]
            root_id = root_block.get("id")
        else:
            root_block = blocks[root_id]

        title = course_title or root_block.get("display_name") or course_key
        course_slug = course_key_to_slug(course_key)

        skipped_items: List[SkippedItem] = []
        modules: List[models.Module] = []

        chapter_ids = root_block.get("children", [])
        m_idx = 0

        for chap_id in chapter_ids:
            chap_block = blocks.get(chap_id)
            if not chap_block or chap_block.get("type") != "chapter":
                continue

            chap_title = chap_block.get("display_name") or f"Module {m_idx + 1}"
            chap_slug = f"{m_idx + 1:02d}_{_slugify(chap_title)}"
            sections: List[models.Section] = []

            sequential_ids = chap_block.get("children", [])
            s_idx = 0

            for seq_id in sequential_ids:
                seq_block = blocks.get(seq_id)
                if not seq_block or seq_block.get("type") != "sequential":
                    continue

                seq_title = seq_block.get("display_name") or f"Section {s_idx + 1}"
                seq_slug = f"{s_idx + 1:02d}_{_slugify(seq_title)}"
                lectures: List[models.Lecture] = []

                vertical_ids = seq_block.get("children", [])
                v_idx = 0

                for vert_id in vertical_ids:
                    vert_block = blocks.get(vert_id)
                    if not vert_block or vert_block.get("type") != "vertical":
                        continue

                    vert_title = vert_block.get("display_name") or f"Unit {v_idx + 1}"
                    vert_slug = f"{v_idx + 1:02d}_{_slugify(vert_title)}"

                    resources = self._parse_vertical_components(
                        vert_block=vert_block,
                        blocks=blocks,
                        skipped_items=skipped_items,
                        course_key=course_key,
                    )

                    if resources:
                        lectures.append(
                            models.Lecture(
                                index=v_idx,
                                slug=vert_slug,
                                title=vert_title,
                                resources=tuple(resources),
                            )
                        )
                        v_idx += 1

                if lectures:
                    sections.append(
                        models.Section(
                            index=s_idx,
                            slug=seq_slug,
                            title=seq_title,
                            lectures=tuple(lectures),
                        )
                    )
                    s_idx += 1

            if sections:
                modules.append(
                    models.Module(
                        index=m_idx,
                        slug=chap_slug,
                        title=chap_title,
                        sections=tuple(sections),
                    )
                )
                m_idx += 1

        manifest = models.CourseManifest(
            provider="edx",
            course_id=course_key,
            slug=course_slug,
            title=title,
            modules=tuple(modules),
        )

        return manifest, skipped_items

    def _parse_vertical_components(
        self,
        vert_block: Dict[str, Any],
        blocks: Dict[str, Any],
        skipped_items: List[SkippedItem],
        course_key: Optional[str] = None,
    ) -> List[models.Resource]:
        """Extract valid downloadable resources from a vertical unit."""
        resources: List[models.Resource] = []
        r_idx = 0

        for comp_id in vert_block.get("children", []):
            comp_block = blocks.get(comp_id)
            if not comp_block:
                continue

            comp_type = comp_block.get("type")
            comp_title = comp_block.get("display_name") or "Component"
            student_data = comp_block.get("student_view_data") or {}

            if comp_type == "video":
                v_resources = self._parse_video_block(
                    comp_id, comp_title, student_data, skipped_items, start_idx=r_idx, course_key=course_key
                )
                resources.extend(v_resources)
                r_idx += len(v_resources)

            elif comp_type == "html":
                h_resources = self._parse_html_block(
                    comp_id, comp_title, student_data, skipped_items, start_idx=r_idx
                )
                resources.extend(h_resources)
                r_idx += len(h_resources)

            else:
                # Unsupported components (problem, discussion, exam, etc.)
                skipped_items.append(
                    SkippedItem(
                        block_id=comp_id,
                        title=comp_title,
                        category="UNSUPPORTED_MEDIA",
                        reason=f"Block type '{comp_type}' is out of scope for MVP",
                    )
                )

        return resources

    def _parse_video_block(
        self,
        block_id: str,
        title: str,
        student_data: Dict[str, Any],
        skipped_items: List[SkippedItem],
        start_idx: int = 0,
        course_key: Optional[str] = None,
    ) -> List[models.Resource]:
        """Parse video component: extracts best direct MP4 and requested subtitles."""
        resources: List[models.Resource] = []
        cur_idx = start_idx

        # 1. Check for explicit restriction
        if student_data.get("only_on_web"):
            skipped_items.append(
                SkippedItem(
                    block_id=block_id,
                    title=title,
                    category="RESTRICTED_MEDIA",
                    reason="Video is marked 'only_on_web' (download disabled by provider)",
                )
            )
            return []

        encoded_videos = student_data.get("encoded_videos") or {}

        # 2. Select direct MP4 stream by preferred quality profile
        selected_url: Optional[str] = None
        for profile in PREFERRED_VIDEO_PROFILES:
            profile_data = encoded_videos.get(profile)
            if isinstance(profile_data, dict):
                candidate_url = profile_data.get("url")
                if candidate_url and isinstance(candidate_url, str):
                    selected_url = candidate_url.strip()
                    break

        if not selected_url:
            sources = student_data.get("sources") or []
            if isinstance(sources, list):
                for s in sources:
                    if isinstance(s, str) and ".mp4" in s.lower():
                        selected_url = s.strip()
                        break

        if selected_url:
            if is_safe_edx_url(selected_url, self._allowed_hosts):
                resources.append(
                    models.Resource(
                        index=cur_idx,
                        format="mp4",
                        title=title,
                        source=selected_url,
                        kind="video",
                    )
                )
                cur_idx += 1
            else:
                skipped_items.append(
                    SkippedItem(
                        block_id=block_id,
                        title=title,
                        category="UNSAFE_URL",
                        reason=f"Video URL failed security allowlist check: {redact_url(selected_url)}",
                    )
                )
        else:
            # Check if it was HLS or YouTube only
            if "hls" in encoded_videos or "youtube" in encoded_videos:
                skipped_items.append(
                    SkippedItem(
                        block_id=block_id,
                        title=title,
                        category="UNSUPPORTED_MEDIA",
                        reason="Video is stream-only (HLS/YouTube; not in MVP scope)",
                    )
                )
            else:
                skipped_items.append(
                    SkippedItem(
                        block_id=block_id,
                        title=title,
                        category="UNSUPPORTED_MEDIA",
                        reason="No downloadable direct MP4 video profile found",
                    )
                )

        # 3. Discover subtitles / transcripts
        transcripts = student_data.get("transcripts") or student_data.get("subtitles") or {}
        sub_url = None
        if isinstance(transcripts, dict) and transcripts:
            # Select requested language first, or default to English / first available
            sub_url = (
                transcripts.get(self._sub_lang)
                or transcripts.get("en")
                or next(iter(transcripts.values()), None)
            )

        # Fallback to standard Open edX transcript handler if not present in student_data (only for downloadable videos)
        if not sub_url and selected_url and self._base_url and course_key and block_id:
            sub_url = f"{self._base_url}/courses/{course_key}/xblock/{block_id}/handler/transcript/download"

        if sub_url and isinstance(sub_url, str):
            sub_url = sub_url.strip()
            # Determine subtitle format extension
            ext = "vtt" if ".vtt" in sub_url.lower() else "srt"
            sub_title = f"{title}.{self._sub_lang}"
            if is_safe_edx_url(sub_url, self._allowed_hosts):
                resources.append(
                    models.Resource(
                        index=cur_idx,
                        format=ext,
                        title=sub_title,
                        source=sub_url,
                        kind="subtitle",
                    )
                )
                cur_idx += 1
            else:
                skipped_items.append(
                    SkippedItem(
                        block_id=block_id,
                        title=sub_title,
                        category="UNSAFE_URL",
                        reason=f"Subtitle URL failed security allowlist check: {redact_url(sub_url)}",
                    )
                )

        return resources

    def _parse_html_block(
        self,
        block_id: str,
        title: str,
        student_data: Dict[str, Any],
        skipped_items: List[SkippedItem],
        start_idx: int = 0,
    ) -> List[models.Resource]:
        """Discover explicit downloadable file attachments inside HTML components."""
        resources: List[models.Resource] = []
        cur_idx = start_idx

        content = student_data.get("custom_tag") or student_data.get("content") or ""
        if not content or not isinstance(content, str):
            return []

        try:
            soup = BeautifulSoup(content, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"].strip()
                parsed_href = urlsplit(href)
                path = parsed_href.path
                _, ext = os.path.splitext(path)
                clean_ext = ext.lower().lstrip(".")

                if clean_ext in ATTACHMENT_EXTENSIONS:
                    link_text = link.get_text().strip() or title
                    att_title = f"{title}_{_slugify(link_text)}"

                    if is_safe_edx_url(href, self._allowed_hosts):
                        resources.append(
                            models.Resource(
                                index=cur_idx,
                                format=clean_ext,
                                title=att_title,
                                source=href,
                                kind="document",
                            )
                        )
                        cur_idx += 1
                    else:
                        skipped_items.append(
                            SkippedItem(
                                block_id=block_id,
                                title=att_title,
                                category="UNSAFE_URL",
                                reason=f"Attachment URL failed security allowlist check: {redact_url(href)}",
                            )
                        )
        except Exception as e:
            logging.debug("HTML parsing error for block %s: %s", block_id, e)

        return resources


# --- HTTP Client Interface ---

class EdxClient:
    """HTTP client interacting with edX.org REST endpoints using authenticated session."""

    def __init__(
        self,
        session: requests.Session,
        base_url: str = "https://courses.edx.org",
    ):
        self._session = session
        self._base_url = base_url.rstrip("/")

    def get_enrollments(self) -> List[Dict[str, Any]]:
        """Retrieve user's active enrollments from official enrollment endpoint."""
        url = f"{self._base_url}/api/enrollment/v1/enrollment"
        logging.info("Checking edX enrollments at %s", redact_url(url))

        try:
            resp = self._session.get(url, timeout=30)
            if resp.status_code in (401, 403):
                raise EdxAuthError(
                    "edX authentication failed: session cookie missing, expired, or invalid."
                )
            if resp.status_code == 429:
                raise EdxRateLimitError("edX rate limit exceeded (HTTP 429).")
            resp.raise_for_status()

            data = resp.json()
            if isinstance(data, list):
                return data
            return []
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response is not None and e.response.status_code in (401, 403):
                    raise EdxAuthError("edX authentication failed (HTTP 401/403).")
            raise EdxError(f"Network error querying edX enrollment: {e}")

    def verify_enrollment(self, course_key: str) -> bool:
        """Check whether the authenticated user is enrolled in the target course."""
        enrollments = self.get_enrollments()
        for item in enrollments:
            details = item.get("course_details", {})
            if details.get("course_id") == course_key and item.get("is_active", False):
                return True
        return False

    def get_current_username(self) -> Optional[str]:
        """Fetch username for the authenticated session, if available."""
        url = f"{self._base_url}/api/user/v1/me"
        try:
            resp = self._session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("username")
        except Exception as e:
            logging.debug("Could not determine username from /api/user/v1/me: %s", e)
        return None

    def get_course_blocks(self, course_key: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Fetch full Course Blocks tree for the specified course."""
        url = f"{self._base_url}/api/courses/v1/blocks/"
        logging.info("Fetching edX Course Blocks: %s", redact_url(url))

        target_user = username or self.get_current_username()
        params = {
            "course_id": course_key,
            "depth": "all",
            "student_view_data": "video,html",
            "requested_fields": "children,display_name,type,student_view_data",
        }
        if target_user:
            params["username"] = target_user
        else:
            params["all_blocks"] = "true"

        try:
            resp = self._session.get(url, params=params, timeout=60)
            if resp.status_code in (401, 403):
                raise EdxAuthError("Access forbidden to course blocks (HTTP 401/403).")
            if resp.status_code == 404:
                raise EdxCourseNotFoundError(f"Course key not found: {course_key}")
            if resp.status_code == 429:
                raise EdxRateLimitError("edX rate limit exceeded (HTTP 429).")
            resp.raise_for_status()

            data = resp.json()
            if not isinstance(data, dict):
                raise EdxSchemaError("Expected dictionary response from edX Course Blocks API")
            return data
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                status = e.response.status_code if e.response is not None else 0
                if status in (401, 403):
                    raise EdxAuthError("Access forbidden to course blocks (HTTP 401/403).")
                if status == 404:
                    raise EdxCourseNotFoundError(f"Course key not found: {course_key}")
            raise EdxError(f"Network error querying edX course blocks: {e}")


# --- Downloader and Execution Engine (Group 4) ---

@dataclass
class DownloadSummary:
    """Summary of resources processed during an edX download execution."""

    total_planned: int = 0
    downloaded: int = 0
    skipped_existing: int = 0
    failed: int = 0
    failed_details: List[Tuple[str, str, str]] = field(default_factory=list)  # (filename, url, reason)
    bytes_downloaded: int = 0


class EdxDownloader(workflow.CourseDownloader):
    """
    Downloader for edX courses reusing the Phase 01 neutral CourseManifest and planning seam.

    Enforces host allowlists, avoids leaking edX session cookies to third-party CDNs,
    performs atomic file writes (.part -> final destination), handles 429 rate limits,
    and skips retries on 401/403 errors.
    """

    def __init__(
        self,
        session: requests.Session,
        path: str = "Downloads/edx",
        overwrite: bool = False,
        timeout: int = 30,
        max_retries: int = 2,
        allowed_hosts: Optional[Set[str]] = None,
    ):
        super().__init__()
        self.session = session
        self.path = path
        self.overwrite = overwrite
        self.timeout = timeout
        self.max_retries = max_retries
        self.allowed_hosts = allowed_hosts or DEFAULT_ALLOWED_HOSTS
        self.summary = DownloadSummary()

    def download_resource(self, resource: workflow.PlannedResource) -> bool:
        """
        Download a single PlannedResource with atomic writes, security guards, and retries.
        """
        url = resource.url
        filename = resource.filename

        # 1. Scheme and host allowlist validation before request
        if not is_safe_edx_url(url, self.allowed_hosts):
            logging.error("Rejected unsafe download URL: %s", redact_url(url))
            self.summary.failed += 1
            self.summary.failed_details.append((filename, redact_url(url), "UNSAFE_URL"))
            return False

        # 2. Skip existing non-empty files if overwrite is False
        if os.path.exists(filename) and os.path.getsize(filename) > 0 and not self.overwrite:
            logging.info("Already downloaded: %s", filename)
            self.summary.skipped_existing += 1
            return True

        # 3. Create destination directory
        target_dir = os.path.dirname(filename)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        # 4. Scope session cookies: do not send edX auth cookies to external CDNs/S3
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        is_edx_domain = (
            host == "edx.org"
            or host.endswith(".edx.org")
            or host == "learn.mit.edu"
            or host.endswith(".learn.mit.edu")
        )

        if is_edx_domain:
            req_session = self.session
        else:
            req_session = requests.Session()
            req_session.headers["User-Agent"] = self.session.headers.get(
                "User-Agent", "edx-dl"
            )

        part_filename = f"{filename}.part"
        candidate_urls = get_candidate_urls(url)

        for cand_idx, current_url in enumerate(candidate_urls):
            attempt = 0
            while attempt <= self.max_retries:
                try:
                    logging.info("Downloading: %s", filename)
                    resp = req_session.get(
                        current_url,
                        stream=True,
                        timeout=(10, self.timeout),
                        allow_redirects=True,
                    )

                    # Validate redirects
                    with resp:
                        if resp.url and not is_safe_edx_url(resp.url, self.allowed_hosts):
                            raise EdxError(f"Redirected to unsafe URL: {redact_url(resp.url)}")
                        for hist in resp.history:
                            if hist.url and not is_safe_edx_url(hist.url, self.allowed_hosts):
                                raise EdxError(f"Redirect hop unsafe: {redact_url(hist.url)}")

                        if resp.status_code == 200:
                            with open(part_filename, "wb") as f:
                                for chunk in resp.iter_content(chunk_size=65536):
                                    if chunk:
                                        f.write(chunk)
                                        self.summary.bytes_downloaded += len(chunk)
                            os.replace(part_filename, filename)
                            self.summary.downloaded += 1
                            logging.info("Completed: %s", filename)
                            return True

                        elif resp.status_code in (401, 403):
                            if cand_idx < len(candidate_urls) - 1:
                                logging.debug("Candidate %s returned %d, trying fallback...", redact_url(current_url), resp.status_code)
                                break
                            err = f"HTTP {resp.status_code} Forbidden/Unauthorized"
                            logging.error("Download failed (%s): %s", err, redact_url(current_url))
                            self.summary.failed += 1
                            self.summary.failed_details.append((filename, redact_url(current_url), err))
                            return False

                        elif resp.status_code == 404:
                            if cand_idx < len(candidate_urls) - 1:
                                logging.debug("Candidate %s returned 404, trying fallback...", redact_url(current_url))
                                break
                            err = "HTTP 404 Not Found"
                            if filename.endswith((".srt", ".vtt")):
                                logging.info("Transcript not available on LMS (%s): %s (skipping)", err, redact_url(current_url))
                                return False
                            logging.error("Download failed (%s): %s", err, redact_url(current_url))
                            self.summary.failed += 1
                            self.summary.failed_details.append((filename, redact_url(current_url), err))
                            return False

                        elif resp.status_code == 429:
                            retry_after_str = resp.headers.get("Retry-After")
                            wait_time = 2
                            if retry_after_str and retry_after_str.isdigit():
                                wait_time = min(int(retry_after_str), 10)
                            attempt += 1
                            if attempt <= self.max_retries:
                                logging.warning(
                                    "Rate limited (HTTP 429). Waiting %ds before retry %d/%d...",
                                    wait_time, attempt, self.max_retries,
                                )
                                time.sleep(wait_time)
                                continue
                            else:
                                err = "HTTP 429 Rate Limit Exceeded"
                                logging.error("Download failed: %s", err)
                                self.summary.failed += 1
                                self.summary.failed_details.append((filename, redact_url(current_url), err))
                                return False

                        else:
                            # 5xx or other status: retry with backoff
                            attempt += 1
                            if attempt <= self.max_retries:
                                wait_time = 2 ** attempt
                                logging.warning(
                                    "HTTP %d error for %s. Retrying in %ds...",
                                    resp.status_code, filename, wait_time,
                                )
                                time.sleep(wait_time)
                                continue
                            else:
                                err = f"HTTP {resp.status_code} Server Error"
                                logging.error("Download failed: %s", err)
                                self.summary.failed += 1
                                self.summary.failed_details.append((filename, redact_url(current_url), err))
                                return False

                except requests.exceptions.RequestException as e:
                    attempt += 1
                    if attempt <= self.max_retries:
                        wait_time = 2 ** attempt
                        logging.warning(
                            "Network error (%s) downloading %s. Retrying in %ds...",
                            e, filename, wait_time,
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        err = f"Network error: {type(e).__name__}"
                        logging.error("Download failed: %s", err)
                        self.summary.failed += 1
                        self.summary.failed_details.append((filename, redact_url(current_url), err))
                        return False
                except Exception as e:
                    err = str(e)
                    logging.error("Download error for %s: %s", filename, err)
                    self.summary.failed += 1
                    self.summary.failed_details.append((filename, redact_url(current_url), err))
                    return False
                finally:
                    if os.path.exists(part_filename):
                        try:
                            os.remove(part_filename)
                        except OSError:
                            pass

        return False

    def download_planned_modules(
        self,
        planned_modules: List[workflow.PlannedModule],
        limit: int = 0,
    ) -> bool:
        """Download all resources across planned modules, with optional count limit."""
        total = sum(
            len(sec.resources)
            for mod in planned_modules
            for sec in mod.sections
        )
        self.summary.total_planned = total

        for mod in planned_modules:
            for sec in mod.sections:
                for res in sec.resources:
                    if limit > 0 and (self.summary.downloaded + self.summary.skipped_existing) >= limit:
                        logging.info("Reached resource download limit of %d. Stopping.", limit)
                        return self.summary.failed == 0
                    self.download_resource(res)

        return self.summary.failed == 0

    def download_manifest(self, manifest: models.CourseManifest) -> bool:
        """Plan and download all resources from a CourseManifest."""
        planned_modules = workflow.plan_downloads(
            modules=manifest,
            class_name=manifest.slug,
            path=self.path,
        )
        return self.download_planned_modules(planned_modules)

    def download_modules(self, modules: Any) -> bool:
        """Implement CourseDownloader abstract method."""
        if isinstance(modules, models.CourseManifest):
            return self.download_manifest(modules)
        manifest = models.legacy_to_manifest(modules, class_name="edx-course")
        return self.download_manifest(manifest)

    def format_summary(self, course_title: str = "edX Course") -> str:
        """Format human-readable download completion report."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"edX Download Summary: {course_title}")
        lines.append("=" * 80)
        lines.append(f"Total Planned: {self.summary.total_planned}")
        lines.append(f"Downloaded:    {self.summary.downloaded} ({self.summary.bytes_downloaded} bytes)")
        lines.append(f"Skipped:       {self.summary.skipped_existing} (already existing)")
        lines.append(f"Failed:        {self.summary.failed}")

        if self.summary.failed_details:
            lines.append("")
            lines.append("Failed Resources:")
            for fname, u, reason in self.summary.failed_details:
                lines.append(f"  - {os.path.basename(fname)}: {reason}")

        lines.append("=" * 80)
        return "\n".join(lines)

