# Execution Plan: Phase 03 — Entrypoint & Authentication Simplification

## Task Groups

### Group 1 — Core Entrypoint Isolation & Secret Redaction
- Remove `sys.argv` mutation in `coursera_dl.py:download_coursera_course`.
- Pass explicit `cmd` list directly to `main_f(cmd)`.
- Make `coursera_dl._cli_main(argv=None)` accept an optional argv slice.
- Sanitize debug logging in `coursera_dl.py:create_session` and `cookies.py:prepare_auth_headers`.
- Verification: Unit tests in `tests/test_entrypoints_and_auth.py` verifying `sys.argv` immutability and secret token redaction.

### Group 2 — Unified Cookie Loading & Browser Auth Consolidation
- Implement universal `load_cookies_from_file` and `get_cookie_jar` in `cookies.py` supporting Netscape and JSON formats.
- Implement unified `load_cookies_from_browser` in `cookies.py` with `rookiepy` and `browser_cookie3` fallback.
- Delegate `edx_provider.py` and `general.py` cookie loading to `cookies.py` while preserving existing signatures.
- Verification: Unit tests for JSON/Netscape cookie loading and browser fallback.

### Group 3 — URL-to-Slug Harmonization & Platform Detection
- Implement `extract_slug_from_url` in `general.py` supporting direct slugs, learn URLs, query params, subpaths.
- Maintain `urltoclassname` in `general.py` and `extract_course_slug` in `coursera_dl.py` delegating to it.
- Implement `detect_platform` in `general.py` classifying `coursera`, `edx`, or `unknown`.
- Verification: Unit tests for URL variants, slug passthrough, and platform detection.

### Group 4 — Unified CLI Dispatcher (`coursedownloader.py`)
- Implement `coursedownloader.py` with `main(argv=None)`.
- Support subcommands: `coursera`, `edx`.
- Support auto-detection of platform based on URL/course key.
- Provide top-level `--help` and `--version`.
- Verification: CLI dispatch tests covering subcommands, auto-detection, help, and error handling.

### Group 5 — Full Regression & Closeout
- Execute complete test suite (117+ baseline tests + Phase 03 tests).
- Run AST parse verification on all repository Python files.
- Run `git diff --check`.
- Record validation and audit log evidence.
