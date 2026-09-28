# Phase 03 Requirements: Entrypoint & Authentication Simplification

## 1. Problem Statement
The codebase currently contains technical debt and security risks in its entrypoints and authentication handling:
1. `download_coursera_course` mutates global `sys.argv` directly, causing side effects when called from Python code, tests, or external modules.
2. Plaintext authentication tokens (`CAUTH`) are logged in debug mode in `coursera_dl.py` and `cookies.py`.
3. URL-to-slug parsing is duplicated between `general.py:urltoclassname` and `coursera_dl.py:extract_course_slug`.
4. Cookie file loading for Coursera in `cookies.py` only supports Netscape format, whereas users export JSON cookies from browser extensions.
5. Users have no unified CLI to download courses across Coursera and edX.

## 2. Scope & Boundaries
- **In scope**:
  - Remove all `sys.argv` mutations across the codebase.
  - Redact sensitive authentication tokens from logs (`CAUTH`, cookies).
  - Unify URL-to-slug extraction and add platform detection (`general.py`).
  - Support both JSON and Netscape cookie formats in `cookies.py`.
  - Create a unified CLI dispatcher `coursedownloader.py` with subcommand dispatch (`coursera`, `edx`) and domain auto-detection.
  - Preserve 100% backward compatibility for existing scripts, CLI arguments, and imports.
- **Out of scope**:
  - Decomposing the full Coursera syllabus parser (Phase 04).
  - SQLite/GUI rewrite (Phase 05).
  - Adding third-party download dependencies.

## 3. Requirements Matrix

| ID | Requirement | Target | Verification |
|---|---|---|---|
| R1 | Immutable `sys.argv` | `download_coursera_course` and `_cli_main` must not mutate `sys.argv` | Unit test checking `sys.argv` before and after invocation |
| R2 | Secret Redaction | `CAUTH` tokens and cookie headers must never be logged in plaintext | Debug log inspection test with sentinel secret |
| R3 | Unified Slug Extraction | Canonical slug extractor supporting slugs, learn URLs, query params, subpaths | Unit tests comparing expected slugs |
| R4 | Platform Detection | Detect whether an identifier or URL is `coursera`, `edx`, or `unknown` | Unit tests across URL and course key variants |
| R5 | Universal Cookie Loading | Support Netscape `.txt` and JSON `.json` in `cookies.py` | Unit tests loading Netscape and JSON cookie files |
| R6 | Unified CLI Dispatcher | `coursedownloader.py` dispatches to Coursera or edX cleanly | CLI dispatch unit tests |
| R7 | Standalone Compatibility | `coursera_dl.py` and `edx_dl.py` operate completely unchanged | Existing test suites pass without regression |
| R8 | Offline Security | Zero external network calls during unit tests | Network guard enforces offline execution |
