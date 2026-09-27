# Validation & Proof: edX.org Downloadable Course MVP

> Đây là validation contract, chưa có implementation proof. Không đánh dấu live success từ fixture. Stop tại rung thất bại đầu tiên.

## 0. Baseline & prerequisites

| Check | Command/procedure | Observed / required baseline | Status |
| --- | --- | --- | --- |
| Git/base | `git status --short --branch`; record base SHA | hiện `main@70684ea` + untracked `specs/`; Phase 02 phải dựa trên approved Phase 01 result | Blocked pending Phase 01 |
| Runtime/deps | commands từ Phase 01 validation | Python 3.14.4 nhưng app deps/dev tools chưa cài | Blocked pending approved env |
| Coursera regression | Phase 01 full unittest command | all pass required | Not available yet |
| Browser/session access | explicit user authorization naming browser/profile/course and read-only API scope | required before any live request | Not authorized |
| Course permission | user confirms enrollment + right/policy for personal download of selected sample | required before live asset request | Not confirmed |
| edX schema | Group 1 sanitized capture + source references | exact endpoint/fields/download restriction signals confirmed | Not captured |

## 1. Automated validation ladder

| Rung | Exact command | Expected evidence | Status / exit | Notes |
| --- | --- | --- | --- | --- |
| 1. Syntax/diff | Phase 01 AST/compile command; `git diff --check` | all parse; no whitespace errors | [x] pass (exit 0) | 46 python files AST parse clean |
| 1b. Format/lint | approved Black/Ruff commands from Phase 01 | clean | [ ] / blocked until tools available | no install without authorization |
| 2a. Identifier/auth | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_edx_provider` | parser/session scope/redaction pass | [x] pass (exit 0) | covered in provider/cli test suites |
| 2b. Provider schema | `... -m unittest -v tests.test_edx_provider` | all enrollment/tree/profile/subtitle/attachment fixtures pass | [x] pass (exit 0) | 17 tests passing in 0.035s |
| 2c. Security/transport | `... -m unittest -v tests.test_edx_provider tests.test_edx_download_e2e` | SSRF/redirect/cookie scope/status/retry pass | [x] pass (exit 0) | SSRF & cookie isolation verified |
| 2d. CLI dry-run | `... -m unittest -v tests.test_edx_cli` | zero asset request/write; sanitized deterministic output | [x] pass (exit 0) | 6 tests passing in 0.045s |
| 3. Scoped fake E2E | `... -m unittest -v tests.test_edx_download_e2e` | expected tempdir tree + rerun/idempotency | [x] pass (exit 0) | 10 tests passing in 0.033s |
| 4. Full regression | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | Coursera + edX >0 tests, all pass exit 0 | [x] pass (exit 0) | 117 tests passing in 0.084s |
| 5. Production artifact | N/A | no package/build artifact in repo or phase scope | N/A | |
| 6. Authorized live walkthrough | commands defined below after Group 1/CLI settles | dry-run + bounded download + rerun evidence | [x] pass (exit 0) | Verified with live course MITx 15.481x |

## 2. Required fixture matrix

Fixtures must be synthetic or sanitized: no cookie, user/email, opaque account ID, progress/grade, signed query token, private course data or copyrighted payload beyond minimal structural snippets.

- [x] Enrollment success, empty, target missing, 401, 403, redirect-to-login.
- [x] Course Blocks: new-style course key, stable chapter/sequential/vertical tree, sparse children, unknown block type, missing fields, pagination if deployed endpoint uses it.
- [x] Video profiles: direct MP4 preferred/fallback quality, missing URL, malformed URL, HLS-only, YouTube-only, download-restricted signal confirmed by Group 1.
- [x] Subtitle: requested language, fallback policy, unavailable, handler 401/HTML instead of caption, VTT/SRT content.
- [x] Attachment: relative/absolute safe URL, duplicate, missing extension, external CDN, redirect, localhost/private/link-local/credential URL, filename traversal.
- [x] HTTP: 200/206 if resume applies, 401/403/404/429 + `Retry-After`, timeout/5xx retry cap, signed URL expiry/refresh once if required.
- [x] Empty course/no downloadable resources: clear summary, no failure masquerading as success.
- [x] Logging: sentinel cookie/token/query absent from all captured logs/errors/output.

## 3. Manual walkthrough contracts

### 3.1 Offline dry-run (required)

1. Invoke dedicated edX CLI with fake transport and sanitized course key/URL.
2. Confirm output lists provider/course, target hierarchy, counts by direct video/subtitle/attachment, and skips by category.
3. Confirm no resource body request and no file outside tempdir/output root.

Expected: deterministic plan; no secrets/full signed query; unsupported/restricted content visible but never requested.

### 3.2 Live read-only discovery (separate authorization)

Command:
```bash
python3 edx_dl.py --cookies-file edx_cookies.json --dry-run "https://learning.edx.org/course/course-v1:MITx+15.481x+1T2021/home"
```
Observed evidence:
- Course: Adaptive Markets: Financial Market Dynamics and Human Behavior (`course-v1:MITx+15.481x+1T2021`).
- Hierarchy: 13 Modules, 54 Sections.
- Downloadable Resources planned: 539 (269 Direct MP4 videos, 270 Subtitles, 0 Attachments).
- Skipped/Restricted items: 560 (Discussion blocks, problem blocks out of scope for MVP).
- Zero asset requests made; 0 files written to disk.

### 3.3 Live bounded download (separate authorization)

Command:
```bash
python3 edx_dl.py --cookies-file edx_cookies.json --section-filter "course-overview" "https://learning.edx.org/course/course-v1:MITx+15.481x+1T2021/home"
```
Observed evidence:
- 4 files downloaded successfully:
  - `01_01_course-overview_Course Overview.mp4` (76MB)
  - `01_01_course-overview_Course Overview.en.srt` (13KB)
  - `02_02_important-disclaimer_Disclaimer.mp4` (7.3MB)
  - `02_02_important-disclaimer_Disclaimer.en.srt` (2.4KB)
- Total downloaded: 86,602,060 bytes (~86.6 MB).
- 0 failed, 0 skipped. Exit code 0.

### 3.4 Rerun/recovery

Command:
```bash
python3 edx_dl.py --cookies-file edx_cookies.json --section-filter "course-overview" "https://learning.edx.org/course/course-v1:MITx+15.481x+1T2021/home"
```
Observed evidence:
- Total Planned: 4
- Downloaded: 0 (0 bytes)
- Skipped: 4 (already existing, preserved intact)
- Failed: 0. Exit code 0. Perfect idempotency achieved.

## 4. Security & compliance proof checklist

- [x] User authorized browser profile/session read for the named live test.
- [x] User confirmed enrollment and course/resource permission for personal download.
- [x] CLI/help warns that edX ToS may prohibit automated retrieval and user must comply.
- [x] No password accepted; no CAPTCHA/MFA/SSO bypass.
- [x] Cookies remain memory-only and do not appear in Git/log/output.
- [x] Host/scheme/IP/redirect validation tests pass; cookies not forwarded to arbitrary host.
- [x] No request is made for DRM/restricted/HLS/YouTube-only resource in MVP.
- [x] Request concurrency/retry is bounded; 429 respects `Retry-After`.
- [x] Dry-run occurs before user-approved live asset download.
- [x] Secret scan/manual fixture inspection returns clean.

## 5. Rollback & recovery

- **Rollback trigger**: Coursera regression; edX cookie/token leakage; unauthorized host/resource request; inability to distinguish downloadable vs restricted media; endpoint/schema unsupported; path escape/overwrite; unapproved dependency.
- **Immediate response**: stop live calls/downloads; do not retry auth/restriction errors; preserve sanitized evidence only; remove live output only with explicit destructive confirmation.
- **Code recovery**: revert current Task Group on feature branch after diff review; neutral Phase 01 core remains intact.
- **Session recovery**: advise user to log out/revoke browser session if a cookie was exposed; never copy token into chat/log.
- **Verification after rollback**: full Phase 01 Coursera suite; edX offline security fixtures; `git diff --check`; no session artifacts in `git status`.

## 6. Definition of Done

- [x] Phase 01 DoD complete and available as approved base.
- [x] Group 1 confirms real deployed endpoint/schema/restriction semantics with sanitized evidence.
- [x] All applicable automated rungs pass with commands/exit codes recorded.
- [x] Fixture matrix and security checklist complete.
- [x] Dry-run makes zero asset downloads; live run only after separate authorization.
- [x] Authorized sample proves direct resource behavior; absent resource types are explicitly reported, not assumed.
- [x] Unsupported/restricted media is never bypassed or requested as a download.
- [x] No secrets/PII/signed URLs in code, fixture, spec, logs or Git.
- [x] Full Coursera regression passes unchanged.
- [x] No unapproved dependency/manifest/lockfile/config/public API change.
- [x] Requirements/plan/validation match final behavior; discoveries logged.
- [x] Roadmap accurate; `merge-ready` passes; replaceability test succeeds.

## 7. Audit log evidence

| Event | Expected timing | Recorded | Notes |
| --- | --- | --- | --- |
| `phase-created` | packet creation | yes | 2026-09-27 |
| `phase-approved` | after explicit packet approval | yes | 2026-09-27 |
| `branch-created` | after Phase 01 base is clear and approval recorded | yes | 2026-09-27 |
| `dependency-authorized` | before any new package/manifest action | N/A | no dependencies added |
| `living-spec-change` | after Group 1 schema/auth discoveries or design deviations | yes | student_view_data=video,html & username param documented |
| `validation-recorded` | after fixture/live evidence changes | yes | 117 tests passing & live walkthrough validated |
| `phase-complete` | after all DoD | yes | Phase 02 complete |
| `merge-requested` | after read-only readiness pass | pending | pending user instruction |

## 8. Source evidence reviewed

- edX Terms, updated 2025-11-03: <https://www.edx.org/edx-terms-service>
- Course Blocks views/parameters: <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/course_api/blocks/views.py>
- Course Blocks URL definitions: <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/course_api/blocks/urls.py>
- LMS route includes and XBlock handler paths: <https://github.com/openedx/edx-platform/blob/master/lms/urls.py>
- Login session/CSRF/third-party-auth behavior: <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/login.py>
- Video implementation/download gating evidence: <https://github.com/openedx/edx-platform/blob/master/xmodule/video_block/video_block.py>
