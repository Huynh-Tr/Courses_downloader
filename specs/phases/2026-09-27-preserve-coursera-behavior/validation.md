# Validation & Proof: Preserve Coursera Behavior & Neutral Download Core

> Status hiện tại là **draft/baseline**, không phải phase đã pass. Mỗi ô green cần command thật, exit code và evidence cập nhật sau implementation.

## 0. Baseline trước thay đổi

| Check | Exact command / procedure | Observed baseline | Date / environment |
| --- | --- | --- | --- |
| Git context | `git status --short --branch && git log -1 --oneline` | trước scaffold: clean `main...origin/main`, `70684ea`; sau scaffold chỉ `?? specs/` | 2026-09-27, `/home/ubuntu/Coursera_downloader` |
| Runtime | `python3 --version`; `python --version` | Python 3.14.4 exit 0; `python` không tồn tại exit 127 | 2026-09-27 |
| Syntax | Python script dùng `ast.parse` cho root `*.py` với `PYTHONDONTWRITEBYTECODE=1` | parsed 16 files, exit 0 | 2026-09-27 |
| CLI health | `PYTHONDONTWRITEBYTECODE=1 python3 coursera_dl.py --version` | fail exit 1: `ModuleNotFoundError: No module named 'bs4'` | 2026-09-27; dependencies chưa cài |
| Tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v` | 0 tests, exit 5 (`NO TESTS RAN`) | 2026-09-27 |
| Lint/format | `ruff check .`; `black --check .` | executable không cài, exit 127 cho cả hai | 2026-09-27 |
| Critical behavior | read-only code inventory + protected contract table | chưa có executable proof | `brownfield-notes.md` |

**Baseline conclusion**: chỉ syntax parsing xanh. Không tuyên bố app/test healthy. Không được cài dependencies nếu chưa có authorization command cụ thể.

## 1. Automated validation ladder

| Rung | Exact command | Expected evidence | Status / exit | Notes |
| --- | --- | --- | --- | --- |
| 1. Syntax | `PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'` (AST-parse 17 root + 11 tests files) | tất cả 28 Python files parse thành công | Passed, exit 0 (2026-09-27) | zero syntax errors |
| 1b. Diff hygiene | `git diff --check` | không whitespace error | Passed, exit 0 (2026-09-27) | không có trailing whitespace |
| 1c. Format | `black --check .` | clean | Blocked (tool absent) | chỉ cài khi authorized; nếu CI/tool policy chọn khác, update spec |
| 1d. Lint | `ruff check .` | no errors theo config | Blocked (tool absent) | như trên |
| 2. Type/compile | `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q ...` hoặc AST script không sinh bytecode | success | Passed via AST parse | không dirty bytecode |
| 3a. Pure contract | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pure_helpers tests.test_cli_contract -v` | all pass (36 tests) | Passed, exit 0 (2026-09-27) | covers slug/url, filename, formatting, CLI flags/defaults |
| 3b. Workflow contract | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_workflow_traversal tests.test_workflow_resource_policy tests.test_downloaders_contract tests.test_shared_planning -v` | all pass (34 tests) | Passed, exit 0 (2026-09-27) | covers hierarchy, overwrite/resume/skip, parallel, native & shared planning seam |
| 3c. Neutral adapter | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_manifest_adapter -v` | exact equivalence pass (12 tests) | Passed, exit 0 (2026-09-27) | models.py: immutability, round-trip, traversal equivalence |
| 3d. Network guard | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_network_guard -v` | unmocked socket connect raises RuntimeError | Passed, exit 0 (2026-09-27) | socket.socket.connect blocked |
| 4. Full regression | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | 83 tests, 0 failures, 0 errors, exit 0 | Passed, exit 0 (2026-09-27) | Ran 83 tests in 0.047s |
| 5. CLI/import smoke | `PYTHONDONTWRITEBYTECODE=1 python3 coursera_dl.py --version` plus import/signature checks | legacy version/entrypoints work | Baseline blocked by missing deps | approved environment required |
| 6. Production artifact | N/A | repo không có package/build artifact và phase không tạo | N/A | không tạo manifest/build opportunistically |

## 2. Required contract matrix

- [x] URL slug: valid Coursera URL, nested/query URL, raw GUI slug behavior, invalid URL (`tests/test_pure_helpers.py`).
- [x] Filename: ASCII, Unicode restricted/unrestricted, forbidden characters, trailing dots/spaces, length truncation (`tests/test_pure_helpers.py`).
- [x] Options: defaults, aliases, formats splitting, class-required flags, auth branch selection (`tests/test_cli_contract.py`).
- [x] Hierarchy: empty + multi-module/section/resource, reverse/filter, combined numbering, verbose dirs (`tests/test_workflow_traversal.py`).
- [x] Write policy: missing/existing, overwrite, resume, skip-download, in-memory UTF-8, disabled URL skipping (`tests/test_workflow_resource_policy.py`).
- [x] Transfer: sequential/parallel callback + join; Range/200/206/416; timeout retry exactly as current contract (`tests/test_downloaders_contract.py`).
- [x] Failure: malformed fixture, downloader exception/False, skipped/failed URL collection (`tests/test_workflow_resource_policy.py`).
- [x] Network guard: full unit suite fails if an unmocked external request/socket is attempted (`tests/test_network_guard.py`).

## 3. Manual / end-to-end walkthrough

| Scenario | Setup/action | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| Offline planning happy path | sanitized Coursera fixture → legacy adapter → neutral planner | exact expected relative paths/order, no network/write outside tempdir | 100% equivalence on single/multi/special-chars fixtures; 0 network calls | Passed (exit 0) |
| Invalid input | malformed tuple/resource/URL fixture | typed/clear error; no partial write | ValueError on corrupt/negative/missing fields; no files created | Passed (exit 0) |
| Empty course | empty fixture | no crash; explicit empty plan | returns empty list `[]`; exit 0 | Passed (exit 0) |
| Existing/resume | precreate complete/partial temp files | existing skipped; resume invocation/path matches legacy contract | skipped when no overwrite/resume; Range header sent on resume=True | Passed (exit 0) |
| Auth/security | run full test suite with fake cookies containing sentinel secret | sentinel absent from captured logs; no browser/live network | fake CAUTH secret parsed without leaking to logs; socket connects blocked | Passed (exit 0) |
| Live Coursera smoke | **Chỉ sau authorization riêng**: account/course permitted, disposable output path | behavior/path matches pre-refactor; no secret logged | Not authorized | Deferred/optional until approved |

## 4. Rollback & recovery

- **Rollback trigger**: any protected CLI/API/path/downloader-call difference; new unapproved dependency/manifest change; test network call; secret in fixture/log; regression suite failure.
- **Recovery**: stop current Group; revert only that Group’s local diff/branch after inspecting it and with required destructive-action confirmation; retain characterization tests/spec evidence; no data migration exists.
- **Post-rollback verification**: Group 1 characterization suite + AST parse + `git diff --check`; inspect worktree scope.

## 5. Definition of Done

- [x] Applicable ladder rungs record command, exit code, date/environment and concise output.
- [x] Required contract matrix covered by nontrivial tests.
- [x] Legacy Coursera public entrypoints/signatures/flags/defaults remain available.
- [x] Fixture equivalence proves exact output path/order/downloader invocation for scoped behavior.
- [x] No external request in unit suite; no cookie/token/PII in Git/log.
- [x] No unapproved dependency/manifest/lockfile/config/public API change.
- [x] Neutral workflow seam is documented enough for Phase 02 without replaying chat.
- [x] Requirements/plan match implementation; deviations logged.
- [x] Roadmap and audit log accurate.
- [x] `merge-ready` checks executed and phase ready for commit/merge review.

## 6. Audit log evidence

| Event | Expected timing | Recorded | Notes |
| --- | --- | --- | --- |
| `phase-created` | packet creation | yes | 2026-09-27T07:51:04Z |
| `phase-approved` | before branch | yes | 2026-09-27T08:13:58Z |
| `branch-created` | after approval | yes | 2026-09-27T08:13:58Z |
| `dependency-authorized` | before any install/manifest change | N/A | Không phát sinh dependency mới |
| `living-spec-change` | if decision changes | N/A | Không phát sinh thay đổi quyết định kiến trúc |
| `validation-recorded` | after material evidence | yes | Groups 1, 2, 3, 4 đã ghi nhận trong specs/LOGGING.md |
| `phase-complete` | after DoD | pending | Chờ chỉ thị commit & review merge từ người dùng |
| `merge-requested` | after readiness | pending | Chờ chỉ thị merge từ người dùng |
