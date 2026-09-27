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
| 1. Syntax/diff | Phase 01 AST/compile command; `git diff --check` | all parse; no whitespace errors | [ ] | no bytecode dirt |
| 1b. Format/lint | approved Black/Ruff commands from Phase 01 | clean | [ ] / blocked until tools available | no install without authorization |
| 2a. Identifier/auth | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_edx_identifiers tests.test_edx_auth` | parser/session scope/redaction pass | [ ] | exact modules sync after implementation |
| 2b. Provider schema | `... -m unittest -v tests.test_edx_provider` | all enrollment/tree/profile/subtitle/attachment fixtures pass | [ ] | no network |
| 2c. Security/transport | `... -m unittest -v tests.test_edx_security tests.test_edx_transport` | SSRF/redirect/cookie scope/status/retry pass | [ ] | sleep/network patched |
| 2d. CLI dry-run | `... -m unittest -v tests.test_edx_cli` | zero asset request/write; sanitized deterministic output | [ ] | |
| 3. Scoped fake E2E | `... -m unittest -v tests.test_edx_download_e2e` | expected tempdir tree + rerun/idempotency | [ ] | direct resources only |
| 4. Full regression | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | Coursera + edX >0 tests, all pass exit 0 | [ ] | record count/duration |
| 5. Production artifact | N/A | no package/build artifact in repo or phase scope | N/A | |
| 6. Authorized live walkthrough | commands defined below after Group 1/CLI settles | dry-run + bounded download + rerun evidence | [ ] | external, separate authorization |

## 2. Required fixture matrix

Fixtures must be synthetic or sanitized: no cookie, user/email, opaque account ID, progress/grade, signed query token, private course data or copyrighted payload beyond minimal structural snippets.

- [ ] Enrollment success, empty, target missing, 401, 403, redirect-to-login.
- [ ] Course Blocks: new-style course key, stable chapter/sequential/vertical tree, sparse children, unknown block type, missing fields, pagination if deployed endpoint uses it.
- [ ] Video profiles: direct MP4 preferred/fallback quality, missing URL, malformed URL, HLS-only, YouTube-only, download-restricted signal confirmed by Group 1.
- [ ] Subtitle: requested language, fallback policy, unavailable, handler 401/HTML instead of caption, VTT/SRT content.
- [ ] Attachment: relative/absolute safe URL, duplicate, missing extension, external CDN, redirect, localhost/private/link-local/credential URL, filename traversal.
- [ ] HTTP: 200/206 if resume applies, 401/403/404/429 + `Retry-After`, timeout/5xx retry cap, signed URL expiry/refresh once if required.
- [ ] Empty course/no downloadable resources: clear summary, no failure masquerading as success.
- [ ] Logging: sentinel cookie/token/query absent from all captured logs/errors/output.

## 3. Manual walkthrough contracts

### 3.1 Offline dry-run (required)

1. Invoke dedicated edX CLI with fake transport and sanitized course key/URL.
2. Confirm output lists provider/course, target hierarchy, counts by direct video/subtitle/attachment, and skips by category.
3. Confirm no resource body request and no file outside tempdir/output root.

Expected: deterministic plan; no secrets/full signed query; unsupported/restricted content visible but never requested.

### 3.2 Live read-only discovery (separate authorization)

Exact command is **TBD until Group 1 locks CLI**. It must use `--dry-run`, one official edX course and one explicitly named browser/profile. Evidence records only sanitized counts/status/host paths.

Expected:
- valid session → course tree discovered;
- expired session → actionable auth error;
- no asset URL fetched during dry-run;
- no cookie persisted/logged.

### 3.3 Live bounded download (separate authorization)

Exact command is **TBD until Group 3/4 locks CLI**. Start with one module/resource limit if implemented; otherwise use a small authorized course.

Expected:
- at least one direct downloadable resource fetched when course provides one;
- subtitle/attachment verified only if sample course provides them (absence is not fabricated success; choose another sample if each required content type must be proved);
- restricted/HLS/YouTube-only resource skipped with explicit reason;
- output remains inside `<path>/edx/<course>/`.

### 3.4 Rerun/recovery

Rerun same command with same output. Expected complete files skipped/preserved, partial behavior matches contract, no duplicate/collision corruption, summary accurate.

## 4. Security & compliance proof checklist

- [ ] User authorized browser profile/session read for the named live test.
- [ ] User confirmed enrollment and course/resource permission for personal download.
- [ ] CLI/help warns that edX ToS may prohibit automated retrieval and user must comply.
- [ ] No password accepted; no CAPTCHA/MFA/SSO bypass.
- [ ] Cookies remain memory-only and do not appear in Git/log/output.
- [ ] Host/scheme/IP/redirect validation tests pass; cookies not forwarded to arbitrary host.
- [ ] No request is made for DRM/restricted/HLS/YouTube-only resource in MVP.
- [ ] Request concurrency/retry is bounded; 429 respects `Retry-After`.
- [ ] Dry-run occurs before user-approved live asset download.
- [ ] Secret scan/manual fixture inspection returns clean.

## 5. Rollback & recovery

- **Rollback trigger**: Coursera regression; edX cookie/token leakage; unauthorized host/resource request; inability to distinguish downloadable vs restricted media; endpoint/schema unsupported; path escape/overwrite; unapproved dependency.
- **Immediate response**: stop live calls/downloads; do not retry auth/restriction errors; preserve sanitized evidence only; remove live output only with explicit destructive confirmation.
- **Code recovery**: revert current Task Group on feature branch after diff review; neutral Phase 01 core remains intact.
- **Session recovery**: advise user to log out/revoke browser session if a cookie was exposed; never copy token into chat/log.
- **Verification after rollback**: full Phase 01 Coursera suite; edX offline security fixtures; `git diff --check`; no session artifacts in `git status`.

## 6. Definition of Done

- [ ] Phase 01 DoD complete and available as approved base.
- [ ] Group 1 confirms real deployed endpoint/schema/restriction semantics with sanitized evidence.
- [ ] All applicable automated rungs pass with commands/exit codes recorded.
- [ ] Fixture matrix and security checklist complete.
- [ ] Dry-run makes zero asset downloads; live run only after separate authorization.
- [ ] Authorized sample proves direct resource behavior; absent resource types are explicitly reported, not assumed.
- [ ] Unsupported/restricted media is never bypassed or requested as a download.
- [ ] No secrets/PII/signed URLs in code, fixture, spec, logs or Git.
- [ ] Full Coursera regression passes unchanged.
- [ ] No unapproved dependency/manifest/lockfile/config/public API change.
- [ ] Requirements/plan/validation match final behavior; discoveries logged.
- [ ] Roadmap accurate; `merge-ready` passes; replaceability test succeeds.

## 7. Audit log evidence

| Event | Expected timing | Recorded | Notes |
| --- | --- | --- | --- |
| `phase-created` | packet creation | yes | 2026-09-27 |
| `phase-approved` | after explicit packet approval | no | |
| `branch-created` | after Phase 01 base is clear and approval recorded | no | |
| `dependency-authorized` | before any new package/manifest action | N/A/currently none | stop if required |
| `living-spec-change` | after Group 1 schema/auth discoveries or design deviations | no | likely applicable |
| `validation-recorded` | after fixture/live evidence changes | no | |
| `phase-complete` | after all DoD | no | |
| `merge-requested` | after read-only readiness pass | no | separate gate |

## 8. Source evidence reviewed

- edX Terms, updated 2025-11-03: <https://www.edx.org/edx-terms-service>
- Course Blocks views/parameters: <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/course_api/blocks/views.py>
- Course Blocks URL definitions: <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/course_api/blocks/urls.py>
- LMS route includes and XBlock handler paths: <https://github.com/openedx/edx-platform/blob/master/lms/urls.py>
- Login session/CSRF/third-party-auth behavior: <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/login.py>
- Video implementation/download gating evidence: <https://github.com/openedx/edx-platform/blob/master/xmodule/video_block/video_block.py>
