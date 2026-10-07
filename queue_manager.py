#!/usr/bin/env python3
"""
Queue Manager for Coursera Course Downloads & Google Drive Uploads
Runs sequentially across specializations and courses.
Each course is:
  1. Downloaded locally into Downloads/<course-slug>
  2. Uploaded to Google Drive via rclone
  3. Verified for file count
  4. Local copy deleted & replaced by symlink pointing to /mnt/gdrive/Learning/Coursera/<Category>/<course-slug>
  5. State saved in queue_state.json
"""

import os
import sys
import time
import json
import shutil
import fcntl
import subprocess
from pathlib import Path
from datetime import datetime

APP_DIR = Path(__file__).resolve().parent
VENV_PYTHON = APP_DIR / ".venv" / "bin" / "python"
DOWNLOADS_DIR = APP_DIR / "Downloads"
COOKIES_FILE = APP_DIR / "coursera_cookies.txt"
STATE_FILE = APP_DIR / "queue_state.json"
LOG_FILE = APP_DIR / "queue_downloader.log"
LOCK_FILE = APP_DIR / "queue.lock"

GDRIVE_REMOTE_BASE = "gdrive:Learning/Coursera"
GDRIVE_MOUNT_BASE = Path("/mnt/gdrive/Learning/Coursera")

# List of specializations and their respective courses
SPECIALIZATIONS = [
    {
        "id": "finance-quantitative-modeling-analysts",
        "name": "Finance & Quantitative Modeling for Analysts Specialization",
        "url": "https://www.coursera.org/specializations/finance-quantitative-modeling-analysts",
        "folder": "Finance and Quantitative Modeling for Analysts",
        "courses": [
            "finance-healthcare-managers",
            "wharton-finance",
        ],
    },
    {
        "id": "team-building",
        "name": "High Performance Collaboration: Leadership, Teamwork, and Negotiation Specialization",
        "url": "https://www.coursera.org/specializations/team-building",
        "folder": "Team Building",
        "courses": [
            "team-culture",
            "high-performing-teams",
            "diverse-teams",
            "continuous-learning-culture",
            "team-building-capstone",
        ],
    },
    {
        "id": "wharton-global-business-strategy",
        "name": "Global Business Strategy Specialization",
        "url": "https://www.coursera.org/specializations/wharton-global-business-strategy",
        "folder": "Wharton Global Business Strategy",
        "courses": [
            "wharton-global-trends-business",
            "wharton-corruption",
            "wharton-social-entrepreneurship",
            "wharton-social-impact",
        ],
    },
    {
        "id": "business-analytics",
        "name": "Business Analytics Specialization",
        "url": "https://www.coursera.org/specializations/business-analytics",
        "folder": "Wharton Business Analytics",
        "courses": [
            "wharton-customer-analytics",
            "wharton-operations-analytics",
            "wharton-people-analytics",
            "accounting-analytics",
            "wharton-capstone-analytics",
        ],
    },
    {
        "id": "wharton-success",
        "name": "Achieving Personal and Professional Success Specialization",
        "url": "https://www.coursera.org/specializations/wharton-success",
        "folder": "Wharton Success",
        "courses": [
            "wharton-success",
            "wharton-communication-skills",
            "wharton-influence",
            "wharton-online-negotiations",
        ],
    },
]

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_disk_usage() -> str:
    try:
        stat = shutil.disk_usage("/")
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_gb = stat.used / (1024**3)
        pct = (stat.used / stat.total) * 100
        return f"Disk: {used_gb:.1f}G/{total_gb:.1f}G ({pct:.1f}%), {free_gb:.1f}G free"
    except Exception:
        return "Disk: N/A"

def load_state(specs=None) -> dict:
    specs = specs or SPECIALIZATIONS
    state = None
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            log(f"Warning: Failed to parse {STATE_FILE}: {e}")

    # Initialize empty state if missing
    if not state or not isinstance(state, dict):
        state = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_courses": sum(len(s["courses"]) for s in specs),
            "completed_count": 0,
            "failed_count": 0,
            "current_course": None,
            "courses": {},
        }
    for spec in specs:
        for c in spec["courses"]:
            if c not in state["courses"]:
                state["courses"][c] = {
                    "specialization_id": spec.get("id", "custom"),
                    "specialization_name": spec.get("name", "Custom"),
                    "folder": spec.get("folder", "Other"),
                    "status": "PENDING",  # PENDING, DOWNLOADING, UPLOADING, COMPLETED, FAILED
                    "files": 0,
                    "size_mb": 0.0,
                    "duration_s": 0.0,
                    "start_time": None,
                    "end_time": None,
                    "error": None,
                }
    state["total_courses"] = len(state["courses"])
    return state

def save_state(state: dict):
    state["updated_at"] = datetime.now().isoformat()
    # Count stats
    completed = sum(1 for c in state["courses"].values() if c["status"] == "COMPLETED")
    failed = sum(1 for c in state["courses"].values() if c["status"] == "FAILED")
    state["completed_count"] = completed
    state["failed_count"] = failed

    tmp_path = STATE_FILE.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        tmp_path.replace(STATE_FILE)
    except Exception as e:
        log(f"Error saving state to {STATE_FILE}: {e}")

def count_local_files(dir_path: Path):
    if not dir_path.exists():
        return 0, 0
    files = [f for f in dir_path.rglob("*") if f.is_file() and not f.is_symlink()]
    total_size = sum(f.stat().st_size for f in files)
    return len(files), total_size

def get_remote_file_count(remote_path: str):
    cmd = ["rclone", "size", remote_path, "--json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return data.get("count", 0), data.get("bytes", 0)
    except Exception as e:
        log(f"Warning: rclone size error on {remote_path}: {e}")
    return None, None

def refresh_rclone_mount():
    log("Refreshing rclone mount (systemctl restart rclone-gdrive.service)...")
    try:
        res = subprocess.run(["sudo", "systemctl", "restart", "rclone-gdrive.service"], timeout=30)
        time.sleep(2)
        return res.returncode == 0
    except Exception as e:
        log(f"Warning: Failed to restart rclone-gdrive.service: {e}")
        return False

def download_course(course: str, max_retries: int = 3) -> bool:
    cmd = [
        str(VENV_PYTHON),
        str(APP_DIR / "coursedownloader.py"),
        "coursera",
        "-c", str(COOKIES_FILE),
        "--path", "Downloads",
        "--resume",
        course,
    ]

    for attempt in range(1, max_retries + 1):
        log(f"[{course}] Attempt {attempt}/{max_retries} starting download...")
        start_t = time.time()
        proc = subprocess.run(cmd, cwd=str(APP_DIR))
        elapsed = time.time() - start_t

        if proc.returncode == 0:
            log(f"[{course}] Download completed successfully in {elapsed:.1f}s (Exit code 0)")
            return True
        else:
            log(f"[{course}] Download returned code {proc.returncode} in {elapsed:.1f}s")
            if attempt < max_retries:
                log(f"[{course}] Waiting 15s before retry {attempt + 1}...")
                time.sleep(15)

    return False

def upload_and_symlink(course: str, folder: str) -> tuple[bool, int, float, str | None]:
    local_dir = DOWNLOADS_DIR / course
    remote_path = f"{GDRIVE_REMOTE_BASE}/{folder}/{course}"
    mount_target = GDRIVE_MOUNT_BASE / folder / course

    if not local_dir.exists():
        return False, 0, 0.0, f"Local directory {local_dir} does not exist"

    local_count, local_bytes = count_local_files(local_dir)
    size_mb = local_bytes / (1024**2)
    log(f"[{course}] Local files ready: {local_count:,} ({size_mb:.2f} MB)")
    log(f"[{course}] Uploading to remote: {remote_path}")

    # Rclone copy command
    rclone_cmd = [
        "rclone", "copy",
        str(local_dir), remote_path,
        "--transfers", "16",
        "--checkers", "32",
        "--fast-list",
        "--drive-chunk-size", "64M",
        "--drive-pacer-min-sleep", "10ms",
        "--drive-pacer-burst", "100",
        "-P",
        "--stats", "15s",
    ]

    start_t = time.time()
    proc = subprocess.run(rclone_cmd)
    elapsed = time.time() - start_t

    if proc.returncode != 0:
        err = f"rclone copy failed with code {proc.returncode}"
        log(f"[{course}] ERROR: {err}")
        return False, local_count, size_mb, err

    log(f"[{course}] Upload finished in {elapsed:.1f}s. Verifying remote count...")
    remote_count, remote_bytes = get_remote_file_count(remote_path)
    log(f"[{course}] Verification: Local={local_count} files, Remote={remote_count} files")

    if remote_count is not None and local_count > 0 and remote_count >= local_count:
        log(f"[{course}] Verification SUCCESS! Freeing local disk space...")
        try:
            shutil.rmtree(local_dir)
        except Exception as e:
            err = f"rmtree failed: {e}"
            log(f"[{course}] ERROR: {err}. Keeping local files for safety.")
            return False, local_count, size_mb, err

        refresh_rclone_mount()

        try:
            # Create symlink
            if local_dir.is_symlink():
                local_dir.unlink()
            elif not local_dir.exists():
                local_dir.symlink_to(mount_target)
                log(f"[{course}] Created symlink: {local_dir} -> {mount_target}")
            else:
                log(f"[{course}] Warning: local_dir still exists as real dir, cannot symlink")
        except Exception as e:
            log(f"[{course}] Warning: Failed to create symlink: {e}")

        log(f"[{course}] Course finished. {get_disk_usage()}")
        return True, local_count, size_mb, None
    else:
        err = (
            f"Remote count ({remote_count}) < Local count ({local_count})"
            if local_count > 0
            else "Local directory contains 0 files"
        )
        log(f"[{course}] ERROR: {err}. Keeping local files for safety.")
        return False, local_count, size_mb, err

def main(argv=None):
    import argparse
    import general

    parser = argparse.ArgumentParser(description="Coursera Queue Downloader & GDrive Backup")
    parser.add_argument("courses", nargs="*", help="Course slugs or URLs to queue")
    parser.add_argument("--folder", default=None, help="Google Drive category folder name")
    parser.add_argument("--name", default=None, help="Group / Specialization display name")
    parser.add_argument("--file", help="Path to text or JSON file listing course slugs")
    args = parser.parse_args(argv)

    os.chdir(str(APP_DIR))
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Determine target courses and specializations
    target_specs = []
    course_list = []
    if args.courses:
        for item in args.courses:
            for part in item.split(","):
                part = part.strip()
                if part:
                    slug = general.extract_slug_from_url(part) or part
                    course_list.append(slug)

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    slug = general.extract_slug_from_url(line) or line
                    course_list.append(slug)

    if course_list:
        folder_name = args.folder or "Custom Downloads"
        spec_name = args.name or folder_name
        target_specs = [{
            "id": "cli-custom-queue",
            "name": spec_name,
            "url": "",
            "folder": folder_name,
            "courses": course_list,
        }]
    else:
        target_specs = SPECIALIZATIONS

    # Acquire lock file
    lock_file = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"Another instance of queue_manager is already running. Exiting.", file=sys.stderr)
        return 1

    log("=" * 80)
    log("COURSERA QUEUE DOWNLOADER & GDRIVE BACKUP SERVICE STARTED")
    log(f"Working Directory: {APP_DIR}")
    log(f"Total Specializations: {len(target_specs)}")
    log(f"Total Courses in Queue: {sum(len(s['courses']) for s in target_specs)}")
    log(f"Initial {get_disk_usage()}")
    log("=" * 80)

    state = load_state(specs=target_specs)
    save_state(state)

    total_idx = 0
    all_courses_flat = []
    for spec in target_specs:
        for c in spec["courses"]:
            all_courses_flat.append((spec, c))

    for idx, (spec, course) in enumerate(all_courses_flat, 1):
        c_state = state["courses"].get(course, {})

        # Check if already completed
        if c_state.get("status") == "COMPLETED":
            log(f"[{idx:02d}/{len(all_courses_flat)}] Skipping {course} (Status already COMPLETED in state)")
            continue

        # Check if already a symlink pointing to an existing directory
        local_dir = DOWNLOADS_DIR / course
        if local_dir.is_symlink():
            target = local_dir.resolve()
            if target.exists():
                count, size = count_local_files(target)
                if count > 0:
                    log(f"[{idx:02d}/{len(all_courses_flat)}] Skipping {course}: Already symlinked to {target} ({count} files)")
                    c_state["status"] = "COMPLETED"
                    c_state["files"] = count
                    c_state["size_mb"] = size / (1024**2)
                    save_state(state)
                    continue

        log("\n" + "#" * 80)
        log(f"[{idx:02d}/{len(all_courses_flat)}] STARTING: {course}")
        log(f"    Specialization: {spec['name']}")
        log(f"    GDrive Category: {spec['folder']}")
        log(f"    {get_disk_usage()}")
        log("#" * 80)

        course_start_time = time.time()
        c_state["status"] = "DOWNLOADING"
        c_state["start_time"] = datetime.now().isoformat()
        c_state["error"] = None
        state["current_course"] = course
        save_state(state)

        # 1. Download
        dl_ok = download_course(course)
        if not dl_ok:
            c_state["status"] = "FAILED"
            c_state["error"] = "Download failed after retries"
            c_state["end_time"] = datetime.now().isoformat()
            c_state["duration_s"] = time.time() - course_start_time
            save_state(state)
            log(f"[{course}] Marked as FAILED. Moving to next course.")
            time.sleep(10)
            continue

        # 2. Upload & Symlink
        c_state["status"] = "UPLOADING"
        save_state(state)

        up_ok, f_count, s_mb, err = upload_and_symlink(course, spec["folder"])
        course_duration = time.time() - course_start_time

        c_state["files"] = f_count
        c_state["size_mb"] = s_mb
        c_state["end_time"] = datetime.now().isoformat()
        c_state["duration_s"] = course_duration

        if up_ok:
            c_state["status"] = "COMPLETED"
            c_state["error"] = None
            log(f"[{course}] Completed successfully in {course_duration:.1f}s ({f_count} files, {s_mb:.2f} MB)")
        else:
            c_state["status"] = "FAILED"
            c_state["error"] = err
            log(f"[{course}] Upload/Verification failed: {err}")

        state["current_course"] = None
        save_state(state)
        time.sleep(5)

    log("\n" + "=" * 80)
    log("ALL QUEUED COURSES PROCESSED!")
    log(f"Final {get_disk_usage()}")
    log("=" * 80)
    save_state(state)
    return 0

if __name__ == "__main__":
    sys.exit(main())
