#!/usr/bin/env python
"""
Course Downloader - Unified CLI Entrypoint for Coursera and edX.org.

Usage:
    coursedownloader coursera [options...] <course-slug-or-url>
    coursedownloader edx [options...] <course-key-or-url>
    coursedownloader <url-or-key> [options...]   (Auto-detects platform)

Examples:
    coursedownloader coursera -c cookies.txt machine-learning
    coursedownloader edx --dry-run course-v1:MITx+15.481x+1T2021
    coursedownloader https://www.coursera.org/learn/wharton-quantitative-modeling -c cookies.txt
    coursedownloader https://learning.edx.org/course/course-v1:MITx+15.481x+1T2021/home --dry-run
"""

import sys
from typing import List, Optional

import coursera_dl
import edx_dl
import general

__version__ = "0.1.0"


def print_help():
    print(__doc__.strip())


def main(argv: Optional[List[str]] = None) -> int:
    """Unified CLI dispatch entrypoint."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print_help()
        return 1

    first = argv[0].strip()

    # Global options
    if first in ("-h", "--help"):
        print_help()
        return 0
    if first in ("-v", "--version"):
        print(f"Course Downloader {__version__}")
        return 0

    # Explicit subcommands
    if first == "coursera":
        return coursera_dl._cli_main(argv[1:])
    if first == "edx":
        return edx_dl.main(argv[1:])

    # Platform auto-detection from first argument
    platform = general.detect_platform(first)
    if platform == "coursera":
        return coursera_dl._cli_main(argv)
    if platform == "edx":
        return edx_dl.main(argv)

    # Check remaining positional tokens for a recognizable URL/key
    for arg in argv[1:]:
        if not arg.startswith("-"):
            detected = general.detect_platform(arg)
            if detected == "coursera":
                return coursera_dl._cli_main(argv)
            if detected == "edx":
                return edx_dl.main(argv)

    print(
        f"Error: Could not auto-detect platform for target '{first}'.\n"
        "Please specify a subcommand explicitly:\n"
        "  coursedownloader coursera [options...] <course>\n"
        "  coursedownloader edx [options...] <course>\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
