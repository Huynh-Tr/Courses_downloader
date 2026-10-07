#!/usr/bin/env python3
"""
MITx Online Course Downloader (Compatibility wrapper delegating to unified edx_dl).
"""
import sys
from pathlib import Path

import edx_dl

DEFAULT_COOKIES = "/home/ubuntu/Courses_downloader/mit_cookies.json"
FALLBACK_COOKIES = "/tmp/mit_cookies.json"
DEFAULT_OUTPUT_DIR = "/mnt/gdrive/Learning/MIT"
DEFAULT_BASE_URL = "https://courses.learn.mit.edu"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args_list = list(argv)
    if "--base-url" not in args_list:
        args_list.extend(["--base-url", DEFAULT_BASE_URL])

    if "--cookies-file" not in args_list and "-c" not in args_list:
        if Path(DEFAULT_COOKIES).exists():
            args_list.extend(["--cookies-file", DEFAULT_COOKIES])
        elif Path(FALLBACK_COOKIES).exists():
            args_list.extend(["--cookies-file", FALLBACK_COOKIES])

    if "--path" not in args_list:
        args_list.extend(["--path", DEFAULT_OUTPUT_DIR])

    return edx_dl.main(args_list)


if __name__ == "__main__":
    sys.exit(main())
