#!/usr/bin/env python3
import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

BASE_DOWNLOADS = Path(__file__).resolve().parent / "Downloads"
GDRIVE_BASE_REMOTE = "gdrive:Learning/Coursera/Positive Psychology"
GDRIVE_MOUNT_BASE = Path("/mnt/gdrive/Learning/Coursera/Positive Psychology")

COURSES = [
    "positive-psychology-project",
    "positive-psychology-methods",
    "positive-psychology-applications",
    "positive-psychology-visionary-science",
    "positive-psychology-resilience",
]

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def get_disk_usage():
    stat = shutil.disk_usage("/")
    free_gb = stat.free / (1024**3)
    total_gb = stat.total / (1024**3)
    used_gb = stat.used / (1024**3)
    pct = (stat.used / stat.total) * 100
    return f"Root Disk: {used_gb:.1f}G/{total_gb:.1f}G used ({pct:.1f}%), {free_gb:.1f}G available"

def count_local_files(dir_path: Path):
    if not dir_path.exists():
        return 0, 0
    files = [f for f in dir_path.rglob("*") if f.is_file() and not f.is_symlink()]
    total_size = sum(f.stat().st_size for f in files)
    return len(files), total_size

def get_remote_file_count(remote_path: str):
    cmd = ["rclone", "size", remote_path, "--json"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        import json
        try:
            data = json.loads(res.stdout)
            return data.get("count", 0), data.get("bytes", 0)
        except Exception:
            pass
    return None, None

def process_course(course: str):
    local_dir = BASE_DOWNLOADS / course
    remote_path = f"{GDRIVE_BASE_REMOTE}/{course}"
    mount_target = GDRIVE_MOUNT_BASE / course

    if local_dir.is_symlink():
        log(f"Skipping {course}: Already a symlink pointing to {local_dir.resolve()}")
        return True

    if not local_dir.exists():
        log(f"Warning: Local directory {local_dir} does not exist!")
        return False

    local_count, local_bytes = count_local_files(local_dir)
    log(f"============================================================")
    log(f"Processing: {course}")
    log(f"  Local files: {local_count:,} ({local_bytes / (1024**2):.2f} MB)")
    log(f"  Remote target: {remote_path}")
    log(f"  {get_disk_usage()}")
    log(f"============================================================")

    # Run rclone copy
    cmd = [
        "rclone", "copy",
        str(local_dir), remote_path,
        "--transfers", "16",
        "--checkers", "32",
        "--fast-list",
        "--drive-chunk-size", "64M",
        "--drive-pacer-min-sleep", "10ms",
        "--drive-pacer-burst", "100",
        "-P",
        "--stats", "10s",
    ]

    start_time = time.time()
    proc = subprocess.run(cmd)
    elapsed = time.time() - start_time

    if proc.returncode != 0:
        log(f"ERROR: rclone copy failed for {course} with code {proc.returncode}")
        return False

    log(f"Copy completed in {elapsed:.1f}s. Verifying file count...")
    remote_count, remote_bytes = get_remote_file_count(remote_path)
    log(f"  Local:  {local_count:,} files ({local_bytes / (1024**2):.2f} MB)")
    log(f"  Remote: {remote_count:,} files ({remote_bytes / (1024**2):.2f} MB)")

    if remote_count is not None and remote_count >= local_count:
        log(f"Verification SUCCESS! Freeing local disk space...")
        # Remove local directory
        shutil.rmtree(local_dir)
        # Create symlink
        local_dir.symlink_to(mount_target)
        log(f"Created symlink: {local_dir} -> {mount_target}")
        log(f"After cleanup: {get_disk_usage()}")
        return True
    else:
        log(f"ERROR: Remote file count ({remote_count}) < Local file count ({local_count}). Keeping local files for safety!")
        return False

def main():
    log("Starting Coursera to Google Drive migration & disk optimization...")
    log(get_disk_usage())

    success = {}
    for course in COURSES:
        ok = process_course(course)
        success[course] = ok

    log("Refreshing rclone mount...")
    subprocess.run(["sudo", "systemctl", "restart", "rclone-gdrive.service"])
    time.sleep(3)

    log("============================================================")
    log("MIGRATION SUMMARY:")
    for course, ok in success.items():
        status = "DONE (Symlinked)" if ok else "FAILED"
        log(f"  {course:<45}: {status}")
    log(f"Final {get_disk_usage()}")
    log("============================================================")

if __name__ == "__main__":
    main()
