"""
edX.org Downloadable Course MVP CLI entrypoint.

Dedicated command-line tool for discovering, dry-running, and downloading
explicitly downloadable course materials (direct MP4 videos, subtitles, and attachments)
from edX.org using an authenticated browser session.
"""

import argparse
import logging
import os
import sys
from typing import List, Optional, Tuple

import requests

import edx_provider
import models
import workflow

__version__ = "0.1.0"

COMPLIANCE_NOTICE = (
    "[Notice] Download of edX content is subject to the edX Terms of Service.\n"
    "Content may only be downloaded for personal, non-commercial educational use\n"
    "where explicit download links are provided. Circumvention of access controls\n"
    "or DRM is strictly prohibited.\n"
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line parser for edX downloader."""
    parser = argparse.ArgumentParser(
        prog="edx_dl.py",
        description="edX.org Downloadable Course MVP CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "course",
        nargs="?",
        help="Canonical course key (e.g. course-v1:Org+Course+Run) or official edX learning URL",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Inspect course outline and print planned downloads without requesting or saving assets",
    )
    parser.add_argument(
        "--cookies-file",
        dest="cookies_file",
        type=str,
        default=None,
        help="Path to Netscape-format cookies.txt file containing edX session",
    )
    parser.add_argument(
        "--browser",
        dest="browser",
        type=str,
        default=None,
        help="Browser name to import session cookies from (e.g. chrome, firefox, edge, brave)",
    )
    parser.add_argument(
        "--path",
        dest="path",
        type=str,
        default="Downloads",
        help="Target directory to save downloaded course content",
    )
    parser.add_argument(
        "--overwrite",
        dest="overwrite",
        action="store_true",
        default=False,
        help="Overwrite already downloaded files instead of skipping them",
    )
    parser.add_argument(
        "--sub-lang",
        dest="sub_lang",
        type=str,
        default="en",
        help="Preferred subtitle language code (e.g. en, vi, es, fr)",
    )
    parser.add_argument(
        "--section-filter",
        dest="section_filter",
        type=str,
        default=None,
        help="Regular expression to filter sections by slug (e.g. 'overview')",
    )
    parser.add_argument(
        "--limit",
        dest="limit",
        type=int,
        default=0,
        help="Maximum number of resources to download (0 = unlimited)",
    )
    parser.add_argument(
        "--base-url",
        dest="base_url",
        type=str,
        default=None,
        help="Base LMS URL for Open edX platform (e.g. https://courses.edx.org or https://courses.learn.mit.edu)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"edx-dl {__version__}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable detailed debug logging",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress informational output",
    )
    return parser


def create_edx_session(
    cookies_file: Optional[str] = None,
    browser: Optional[str] = None,
    default_domain: str = ".edx.org",
) -> requests.Session:
    """Construct an authenticated requests.Session for edX from cookies file or browser."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })

    if cookies_file:
        jar = edx_provider.load_cookies_from_file(cookies_file, default_domain=default_domain)
        session.cookies.update(jar)
        logging.info("Loaded edX session cookies from %s", cookies_file)
    elif browser:
        jar = edx_provider.load_cookies_from_browser(browser, domain=default_domain.lstrip("."))
        session.cookies.update(jar)
        logging.info("Imported edX session cookies from browser '%s'", browser)

    return session


def format_dry_run_summary(
    manifest: models.CourseManifest,
    skips: List[edx_provider.SkippedItem],
    planned_modules: List[workflow.PlannedModule],
) -> str:
    """Render a clean, structured dry-run report for the user."""
    lines: List[str] = []
    lines.append("=" * 80)
    lines.append(f"edX Course Dry-Run Summary: {manifest.title}")
    lines.append(f"Course ID: {manifest.course_id} | Slug: {manifest.slug}")
    lines.append("=" * 80)

    # Count resources by kind
    videos_count = 0
    subs_count = 0
    docs_count = 0

    planned_files: List[Tuple[str, str]] = []
    for mod in planned_modules:
        for sec in mod.sections:
            for res in sec.resources:
                if res.filename.endswith(".mp4"):
                    videos_count += 1
                    kind = "video"
                elif res.filename.endswith(".srt") or res.filename.endswith(".vtt"):
                    subs_count += 1
                    kind = "subtitle"
                else:
                    docs_count += 1
                    kind = "document"
                planned_files.append((kind, res.filename))

    lines.append(
        f"Hierarchy: {len(manifest.modules)} Modules | "
        f"{sum(len(m.sections) for m in manifest.modules)} Sections"
    )
    lines.append(f"Downloadable Resources: {len(planned_files)}")
    lines.append(f"  - Direct MP4 Videos: {videos_count}")
    lines.append(f"  - Subtitles: {subs_count}")
    lines.append(f"  - Attachments/Documents: {docs_count}")
    lines.append("")

    lines.append("Planned File Paths:")
    for kind, path in planned_files[:20]:
        lines.append(f"  [{kind}] {path}")
    if len(planned_files) > 20:
        lines.append(f"  ... and {len(planned_files) - 20} more files.")
    lines.append("")

    lines.append(f"Skipped / Restricted Items: {len(skips)}")
    for item in skips:
        lines.append(f"  - [{item.category}] {item.title}: {item.reason}")

    lines.append("=" * 80)
    lines.append("Dry-run complete. 0 files written to disk.")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI execution entrypoint."""
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    # Configure logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.course:
        parser.print_usage()
        print("Error: Course key or learning URL required.")
        return 1

    print(COMPLIANCE_NOTICE)

    try:
        from urllib.parse import urlparse

        base_url = args.base_url
        if not base_url and (args.course.startswith("http://") or args.course.startswith("https://")):
            parsed_course_url = urlparse(args.course)
            base_url = f"{parsed_course_url.scheme}://{parsed_course_url.netloc}"
        if not base_url:
            base_url = "https://courses.edx.org"

        course_key = edx_provider.extract_edx_course_key(args.course)
        logging.info("Target edX course key: %s (LMS: %s)", course_key, base_url)

        default_cookie_domain = ".learn.mit.edu" if "mit.edu" in base_url else ".edx.org"
        session = create_edx_session(
            cookies_file=args.cookies_file,
            browser=args.browser,
            default_domain=default_cookie_domain,
        )
        client = edx_provider.EdxClient(session, base_url=base_url)

        # 1. Fetch blocks
        blocks_data = client.get_course_blocks(course_key)

        # 2. Parse course
        edx_parser = edx_provider.EdxCourseParser(
            subtitle_language=args.sub_lang,
            base_url=base_url,
        )
        manifest, skips = edx_parser.parse(blocks_data, course_key=course_key)

        # 3. Plan downloads using Phase 01 neutral core
        target_path = (
            args.path
            if os.path.basename(args.path.rstrip("/\\")) in ("edx", "Edx", "MIT")
            else os.path.join(args.path, "edx")
        )
        planned_modules = workflow.plan_downloads(
            modules=manifest,
            class_name=manifest.slug,
            path=target_path,
            args=args,
        )

        if args.dry_run:
            summary = format_dry_run_summary(manifest, skips, planned_modules)
            print(summary)
            return 0

        # Non-dry-run download execution (Group 4)
        if manifest.total_resources == 0:
            logging.info("No downloadable resources found in course manifest.")
            return 0

        downloader = edx_provider.EdxDownloader(
            session=session,
            path=target_path,
            overwrite=args.overwrite,
        )
        success = downloader.download_planned_modules(planned_modules, limit=args.limit)
        print(downloader.format_summary(manifest.title))
        return 0 if success else 1

    except (ValueError, edx_provider.EdxError, FileNotFoundError) as e:
        logging.error("%s", e)
        return 1
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        if args.debug:
            logging.exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
