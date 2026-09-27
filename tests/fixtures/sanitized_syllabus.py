"""
Sanitized syllabus data fixtures representing CourseraExtractor output.
No secrets, personal identifiable information, or live credentials.
"""

from define import IN_MEMORY_MARKER

# Single module, single section, multi-resource lecture
SINGLE_MODULE_SYLLABUS = [
    (
        "week-1-introduction",
        [
            (
                "lesson-1-welcome",
                [
                    (
                        "01-welcome-lecture",
                        {
                            "mp4": [("https://example.test/videos/welcome.mp4", "Welcome Video")],
                            "srt": [("https://example.test/subtitles/welcome_en.srt", "Welcome Video_en")],
                            "txt": [("https://example.test/transcripts/welcome_en.txt", "Welcome Video_en")],
                        },
                    ),
                    (
                        "02-course-syllabus",
                        {
                            "html": [(f"{IN_MEMORY_MARKER}<h1>Syllabus</h1><p>Welcome to the course.</p>", "Syllabus Reading")],
                            "pdf": [("https://example.test/docs/syllabus.pdf", "Syllabus Document")],
                        },
                    ),
                ],
            )
        ],
    )
]

# Multi-module, multi-section syllabus
MULTI_MODULE_SYLLABUS = [
    (
        "01-fundamentals",
        [
            (
                "sec-1-basics",
                [
                    (
                        "lec-1-overview",
                        {
                            "mp4": [("https://example.test/v/lec1.mp4", "Overview")],
                            "srt": [("https://example.test/s/lec1_en.srt", "Overview_en")],
                        },
                    ),
                    (
                        "lec-2-architecture",
                        {
                            "mp4": [("https://example.test/v/lec2.mp4", "Architecture")],
                        },
                    ),
                ],
            ),
            (
                "sec-2-setup",
                [
                    (
                        "lec-3-installation",
                        {
                            "html": [(f"{IN_MEMORY_MARKER}<p>Install instructions</p>", "Installation Guide")],
                            "pdf": [("https://example.test/d/setup.pdf", "Setup Guide")],
                        },
                    ),
                ],
            ),
        ],
    ),
    (
        "02-advanced-topics",
        [
            (
                "sec-1-deep-dive",
                [
                    (
                        "lec-1-deep",
                        {
                            "mp4": [("https://example.test/v/deep.mp4", "Deep Dive")],
                            "ipynb": [("https://example.test/n/deep.ipynb", "Exercise Notebook")],
                        },
                    ),
                ],
            ),
        ],
    ),
]

# Syllabus with special characters in titles and names
SPECIAL_CHARS_SYLLABUS = [
    (
        "week:01/intro*test?",
        [
            (
                "section <1> | basics",
                [
                    (
                        "lecture \"one\" & two",
                        {
                            "mp4": [("https://example.test/v/special.mp4", "Introduction: Part 1 / Section A?")],
                        },
                    ),
                ],
            ),
        ],
    ),
]

EMPTY_SYLLABUS = []
