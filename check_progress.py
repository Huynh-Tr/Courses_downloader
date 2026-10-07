#!/usr/bin/env python3
"""
Check progress and status of Coursera Queue Downloader
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

APP_DIR = Path(__file__).resolve().parent
STATE_FILE = APP_DIR / "queue_state.json"
LOG_FILE = APP_DIR / "queue_downloader.log"

STATUS_ICONS = {
    "COMPLETED": "✅ COMPLETED",
    "DOWNLOADING": "⬇️  DOWNLOADING",
    "UPLOADING": "☁️  UPLOADING",
    "PENDING": "⏳ PENDING",
    "FAILED": "❌ FAILED",
}

def get_service_status() -> str:
    try:
        res = subprocess.run(["systemctl", "is-active", "coursera-downloader"], capture_output=True, text=True)
        status = res.stdout.strip()
        if status == "active":
            return "🟢 ACTIVE (Running)"
        elif status == "failed":
            return "🔴 FAILED"
        else:
            return f"⚪ {status.upper()}"
    except Exception:
        return "UNKNOWN"

def get_disk_info() -> str:
    stat = shutil.disk_usage("/")
    free_gb = stat.free / (1024**3)
    total_gb = stat.total / (1024**3)
    used_gb = stat.used / (1024**3)
    pct = (stat.used / stat.total) * 100
    return f"{used_gb:.1f} GB / {total_gb:.1f} GB ({pct:.1f}% used, {free_gb:.1f} GB free)"

def main():
    print("=" * 85)
    print("          COURSERA BACKGROUND DOWNLOAD QUEUE MONITOR")
    print("=" * 85)
    print(f"Service Status : {get_service_status()}")
    print(f"Server Disk    : {get_disk_info()}")

    if not STATE_FILE.exists():
        print("\nState file not found. Service has not initialized queue_state.json yet.")
        print(f"Check log: tail -n 20 {LOG_FILE}")
        return 0

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as e:
        print(f"\nError reading state file: {e}")
        return 1

    total = state.get("total_courses", 0)
    completed = state.get("completed_count", 0)
    failed = state.get("failed_count", 0)
    current = state.get("current_course", "None")
    updated = state.get("updated_at", "N/A")

    print(f"Queue Progress : {completed}/{total} completed, {failed} failed")
    print(f"Current Course : {current or 'Idle'}")
    print(f"Last Updated   : {updated}")
    print("-" * 85)

    courses = state.get("courses", {})
    # Group by specialization
    specs = {}
    for c_slug, c_info in courses.items():
        s_name = c_info.get("specialization_name", "Other")
        if s_name not in specs:
            specs[s_name] = []
        specs[s_name].append((c_slug, c_info))

    for s_name, c_list in specs.items():
        print(f"\n📚 {s_name}:")
        print(f"  {'Course Slug':<40} | {'Status':<15} | {'Files':>6} | {'Size':>9} | {'Duration':>8}")
        print("  " + "-" * 81)
        for slug, info in c_list:
            status_text = STATUS_ICONS.get(info.get("status"), info.get("status", "UNKNOWN"))
            files = info.get("files", 0)
            size_mb = info.get("size_mb", 0.0)
            duration_s = info.get("duration_s", 0.0)

            f_str = f"{files:,}" if files else "-"
            s_str = f"{size_mb:.1f} MB" if size_mb else "-"
            d_str = f"{duration_s:.0f}s" if duration_s else "-"

            print(f"  {slug:<40} | {status_text:<15} | {f_str:>6} | {s_str:>9} | {d_str:>8}")

    print("\n" + "=" * 85)
    print("RECENT LOGS (Last 10 lines):")
    print("-" * 85)
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(line.rstrip())
        except Exception as e:
            print(f"Error reading log: {e}")
    else:
        print("No log file found yet.")
    print("=" * 85)
    return 0

if __name__ == "__main__":
    sys.exit(main())
