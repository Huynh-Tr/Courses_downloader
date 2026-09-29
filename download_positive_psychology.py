#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from pathlib import Path

COURSES = [
    "positive-psychology-visionary-science",
    "positive-psychology-applications",
    "positive-psychology-methods",
    "positive-psychology-resilience",
    "positive-psychology-project",
]

APP_DIR = str(Path(__file__).resolve().parent)
VENV_PYTHON = str(Path(APP_DIR) / ".venv" / "bin" / "python")

def main():
    os.chdir(APP_DIR)
    print("=" * 80)
    print("Starting download of Coursera Specialization: Positive Psychology")
    print(f"Total courses: {len(COURSES)}")
    for idx, c in enumerate(COURSES, 1):
        print(f"  {idx}. {c}")
    print("=" * 80)
    sys.stdout.flush()

    results = {}
    for idx, course in enumerate(COURSES, 1):
        print(f"\n[{idx}/{len(COURSES)}] >>> Starting: {course}")
        start_time = time.time()
        sys.stdout.flush()

        cmd = [
            VENV_PYTHON,
            "coursedownloader.py",
            "coursera",
            "-c", "coursera_cookies.txt",
            "--path", "Downloads",
            "--resume",
            course,
        ]

        proc = subprocess.run(cmd, cwd=APP_DIR)
        elapsed = time.time() - start_time
        course_dir = Path(APP_DIR) / "Downloads" / course
        files = [f for f in course_dir.rglob("*") if f.is_file()] if course_dir.exists() else []
        file_count = len(files)
        total_size = sum(f.stat().st_size for f in files)

        results[course] = {
            "exit_code": proc.returncode,
            "elapsed": elapsed,
            "files": file_count,
            "size_mb": total_size / (1024 * 1024),
        }

        print(f"[{idx}/{len(COURSES)}] <<< Completed {course} in {elapsed:.1f}s (Exit code: {proc.returncode})")
        print(f"    Files: {file_count}, Total size: {total_size / (1024*1024):.2f} MB")
        sys.stdout.flush()

    print("\n" + "=" * 80)
    print("FINAL SUMMARY - POSITIVE PSYCHOLOGY SPECIALIZATION:")
    print("=" * 80)
    all_ok = True
    total_all_files = 0
    total_all_size_mb = 0.0
    for course, r in results.items():
        status = "SUCCESS" if r["exit_code"] == 0 else f"FAILED (code {r['exit_code']})"
        if r["exit_code"] != 0:
            all_ok = False
        total_all_files += r["files"]
        total_all_size_mb += r["size_mb"]
        print(f"{course:<42} | {status:<10} | {r['files']:>4} files | {r['size_mb']:>8.2f} MB | {r['elapsed']:>6.1f}s")
    print("-" * 80)
    print(f"TOTAL: {total_all_files} files, {total_all_size_mb:.2f} MB ({total_all_size_mb / 1024:.2f} GB)")
    print("=" * 80)
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
