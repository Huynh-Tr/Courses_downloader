"""
Sanitized offline test fixtures for edX.org Course Blocks & Enrollment APIs.
Contains NO credentials, cookies, tokens, personal data, or copyrighted assets.
"""

from typing import Any, Dict

EDX_COURSE_KEY = "course-v1:TestOrg+CS101+2026_T1"
EDX_LEARNING_URL = f"https://learning.edx.org/course/{EDX_COURSE_KEY}/home"
EDX_COURSES_URL = f"https://courses.edx.org/courses/{EDX_COURSE_KEY}/courseware"

# --- 1. Course Blocks Fixture ---

VALID_EDX_BLOCKS: Dict[str, Any] = {
    "root": f"block-v1:TestOrg+CS101+2026_T1+type@course+block@course",
    "blocks": {
        f"block-v1:TestOrg+CS101+2026_T1+type@course+block@course": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@course+block@course",
            "type": "course",
            "display_name": "Introduction to Computer Science",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@chapter+block@chap_01",
                f"block-v1:TestOrg+CS101+2026_T1+type@chapter+block@chap_02",
            ],
        },
        # Chapter 1
        f"block-v1:TestOrg+CS101+2026_T1+type@chapter+block@chap_01": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@chapter+block@chap_01",
            "type": "chapter",
            "display_name": "Week 1: Fundamentals",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@sequential+block@seq_01",
            ],
        },
        # Sequential 1
        f"block-v1:TestOrg+CS101+2026_T1+type@sequential+block@seq_01": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@sequential+block@seq_01",
            "type": "sequential",
            "display_name": "Lesson 1: Algorithms",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_01",
                f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_02",
            ],
        },
        # Vertical 1 (Unit 1): Direct MP4 + Subtitles + HTML with downloadable attachment
        f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_01": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_01",
            "type": "vertical",
            "display_name": "Algorithm Basics",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_01",
                f"block-v1:TestOrg+CS101+2026_T1+type@html+block@html_01",
            ],
        },
        # Video 1: Downloadable direct MP4 + Transcripts
        f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_01": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_01",
            "type": "video",
            "display_name": "Lecture 1: What is an Algorithm",
            "student_view_data": {
                "encoded_videos": {
                    "desktop_mp4": {
                        "url": "https://edx-video.net/TestOrgCS101-V01_desktop.mp4",
                        "file_size": 24000000,
                    },
                    "fallback": {
                        "url": "https://edx-video.net/TestOrgCS101-V01_fallback.mp4",
                        "file_size": 18000000,
                    },
                    "hls": {
                        "url": "https://edx-video.net/TestOrgCS101-V01.m3u8",
                    },
                },
                "transcripts": {
                    "en": "https://courses.edx.org/api/courses/v1/subtitles/vid_01?lang=en",
                    "vi": "https://courses.edx.org/api/courses/v1/subtitles/vid_01?lang=vi",
                },
                "only_on_web": False,
            },
        },
        # HTML 1: Contains explicit PDF attachment link
        f"block-v1:TestOrg+CS101+2026_T1+type@html+block@html_01": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@html+block@html_01",
            "type": "html",
            "display_name": "Lecture Notes & Reading",
            "student_view_data": {
                "custom_tag": '<p>Review the <a href="https://edx-video.net/notes/week1_algorithms.pdf">Algorithms Cheatsheet (PDF)</a> before the quiz.</p>',
            },
        },
        # Vertical 2 (Unit 2): Restricted video + HLS/YouTube-only video
        f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_02": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_02",
            "type": "vertical",
            "display_name": "Advanced Considerations",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_restricted",
                f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_hls_only",
            ],
        },
        # Video 2: restricted by only_on_web
        f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_restricted": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_restricted",
            "type": "video",
            "display_name": "Restricted Video",
            "student_view_data": {
                "encoded_videos": {
                    "desktop_mp4": {
                        "url": "https://edx-video.net/restricted.mp4",
                    },
                },
                "only_on_web": True,
            },
        },
        # Video 3: HLS / YouTube only, no direct MP4
        f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_hls_only": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_hls_only",
            "type": "video",
            "display_name": "External Stream Video",
            "student_view_data": {
                "encoded_videos": {
                    "hls": {
                        "url": "https://edx-video.net/stream.m3u8",
                    },
                    "youtube": {
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    },
                },
                "only_on_web": False,
            },
        },
        # Chapter 2
        f"block-v1:TestOrg+CS101+2026_T1+type@chapter+block@chap_02": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@chapter+block@chap_02",
            "type": "chapter",
            "display_name": "Week 2: Data Structures",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@sequential+block@seq_02",
            ],
        },
        # Sequential 2
        f"block-v1:TestOrg+CS101+2026_T1+type@sequential+block@seq_02": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@sequential+block@seq_02",
            "type": "sequential",
            "display_name": "Lesson 2: Arrays and Lists",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_03",
            ],
        },
        # Vertical 3: Video with mobile_low profile + Problem block
        f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_03": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@vertical+block@vert_03",
            "type": "vertical",
            "display_name": "Arrays in Memory",
            "children": [
                f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_low_quality",
                f"block-v1:TestOrg+CS101+2026_T1+type@problem+block@prob_01",
            ],
        },
        # Video 4: Only low quality mp4 available
        f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_low_quality": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@video+block@vid_low_quality",
            "type": "video",
            "display_name": "Array Memory Layout",
            "student_view_data": {
                "encoded_videos": {
                    "mobile_low": {
                        "url": "https://edx-video.net/arrays_low.mp4",
                        "file_size": 9000000,
                    },
                },
                "transcripts": {
                    "en": "https://courses.edx.org/api/courses/v1/subtitles/vid_low?lang=en",
                },
                "only_on_web": False,
            },
        },
        # Problem block: Unsupported in MVP
        f"block-v1:TestOrg+CS101+2026_T1+type@problem+block@prob_01": {
            "id": f"block-v1:TestOrg+CS101+2026_T1+type@problem+block@prob_01",
            "type": "problem",
            "display_name": "Array Knowledge Check",
            "student_view_data": {},
        },
    },
}

# --- 2. Empty Course Blocks Fixture ---
EMPTY_EDX_BLOCKS: Dict[str, Any] = {
    "root": f"block-v1:TestOrg+EMPTY+2026+type@course+block@course",
    "blocks": {
        f"block-v1:TestOrg+EMPTY+2026+type@course+block@course": {
            "id": f"block-v1:TestOrg+EMPTY+2026+type@course+block@course",
            "type": "course",
            "display_name": "Empty Course",
            "children": [],
        }
    },
}

# --- 3. Enrollment API Fixtures ---
ENROLLMENT_SUCCESS = [
    {
        "course_details": {
            "course_id": EDX_COURSE_KEY,
            "course_name": "Introduction to Computer Science",
        },
        "is_active": True,
        "mode": "verified",
    },
    {
        "course_details": {
            "course_id": "course-v1:OtherOrg+OTHER+2026",
            "course_name": "Other Course",
        },
        "is_active": True,
        "mode": "audit",
    },
]

ENROLLMENT_NOT_ENROLLED = [
    {
        "course_details": {
            "course_id": "course-v1:OtherOrg+OTHER+2026",
            "course_name": "Other Course",
        },
        "is_active": True,
        "mode": "audit",
    },
]
