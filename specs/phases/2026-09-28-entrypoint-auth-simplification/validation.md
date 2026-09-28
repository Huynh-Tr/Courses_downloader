# Validation & Proof: Phase 03 — Entrypoint & Authentication Simplification

## Automated Validation Ladder

| Rung | Command | Expected Evidence | Status |
|---|---|---|---|
| 1. Syntax/diff | AST compile check; `git diff --check` | All parse clean; zero whitespace errors | [x] pass (exit 0, 49 files clean) |
| 2a. Sys.argv immutability | `python3 -m unittest -v tests.test_entrypoints_and_auth.TestSysArgvImmutability` | `sys.argv` remains untouched across calls | [x] pass (exit 0) |
| 2b. Secret redaction | `python3 -m unittest -v tests.test_entrypoints_and_auth.TestSecretRedaction` | Sentinel tokens absent from debug logs | [x] pass (exit 0) |
| 2c. Cookie loading | `python3 -m unittest -v tests.test_entrypoints_and_auth.TestUniversalCookieLoading` | Netscape and JSON files loaded correctly | [x] pass (exit 0) |
| 2d. Slug & platform | `python3 -m unittest -v tests.test_entrypoints_and_auth.TestUrlAndSlugHarmonization` | URL parsing and platform detection clean | [x] pass (exit 0) |
| 3. CLI Dispatcher | `python3 -m unittest -v tests.test_entrypoints_and_auth.TestUnifiedDispatcher` | Subcommands and auto-detection pass | [x] pass (exit 0) |
| 4. Full Regression | `python3 -m unittest discover tests -v` | All tests pass exit 0 (134 tests) | [x] pass (exit 0, 134/134 passed in 0.097s) |

## Definition of Done
- [x] No function mutates `sys.argv`.
- [x] Secrets (CAUTH, cookies) are redacted from logs.
- [x] Cookies loaded seamlessly from Netscape and JSON files.
- [x] URL-to-slug extraction harmonized with backward compatibility.
- [x] Unified CLI dispatcher `coursedownloader.py` operational.
- [x] Full regression passes with 0 failures, 0 errors, and zero network sockets.
