# Execution Plan: edX.org Downloadable Course MVP

> **One Group, One Turn.** Packet approval chỉ cho phép tạo local branch rồi dừng. Live browser/session/API/download là external access cần authorization riêng và không được suy ra từ spec approval.

## 0. Preconditions

- [x] Constitution/roadmap/brownfield inventory drafted.
- [ ] Phase 01 neutral core hoàn tất và base commit/branch được user chỉ định.
- [ ] edX requirements được user duyệt.
- [x] `specs/LOGGING.md` available.
- [ ] `phase-approved` recorded after explicit approval.
- [ ] Branch `feature/2026-09-27-edx-download-mvp` created from approved Phase 01 base; nếu Phase 01 chưa merge vào `main`, dừng hỏi base.
- [ ] User separately authorizes exact browser profile/session read and one live course/API target.
- [ ] No dependency/manifest changes; nếu browser cookie import không khả thi bằng stack hiện tại, dừng tại decision gate.
- [ ] Authorized sample course has at least one explicitly downloadable non-DRM direct resource; otherwise walkthrough expected outcome đổi thành validated skip-only và MVP demo course cần mẫu khác.

## Group 1 — Read-only endpoint/auth spike & sanitized contract fixtures

- **Objective**: xác minh reality của edX.org trước khi thiết kế parser; không tải course assets và không viết production code.
- **Likely files**: chỉ `specs/` evidence ở lượt discovery; fixture chỉ được tạo ở lượt execution sau khi user duyệt việc sanitize/ghi test data.
- **Steps**:
  1. Inspect browser-cookie capability hiện có (`rookiepy`/optional `browser_cookie3`) và target OS/browser; không cài package.
  2. Với authorization riêng, tạo session in-memory từ browser profile, gọi tối thiểu enrollment/course blocks/learner endpoint cần thiết cho đúng một course; không gọi asset URLs.
  3. Capture chỉ schema/field names và synthetic/sanitized values; loại cookie, user ID/email, signed query, opaque private URLs, grades/progress.
  4. Xác nhận exact deployed endpoint prefix, redirects, CSRF/session needs, host allowlist, pagination/tree relation, video/subtitle/attachment download indicators và restricted-media signal.
  5. Update requirements/validation nếu source assumptions sai; ghi `living-spec-change`; dừng nếu Terms/course policy hoặc access không cho phép.
- **Acceptance**: có redacted schema contract đủ để parser test offline; secret scanner/manual inspection clean; không asset download; không production/dependency/Git state ngoài specs authorized changes.
- **Verification**:
  - schema/fixture redaction checklist;
  - `git diff -- specs/` và `git diff --check`;
  - targeted secret scan nếu fixture được phép tạo;
  - request log chỉ hostname/path/status, không query/cookie.
- **Audit events**: external-access authorization scope trong notes; `living-spec-change` nếu assumption thay đổi; `validation-recorded` khi evidence material được ghi.
- **Stop**: báo endpoint/schema/browser feasibility và decision gates; chờ Group 2.

## Group 2 — Offline edX provider parser

- **Objective**: chuyển sanitized enrollment/blocks/unit fixtures thành neutral manifest, không live network/filesystem ngoài tempdir.
- **Likely files**: provider module/package mới (tên theo cấu trúc Phase 01), `tests/fixtures/edx_*`, `tests/test_edx_provider.py`.
- **Steps**:
  1. Implement canonical course key/learning URL validation và enrollment-based mapping.
  2. Implement HTTP client interface với explicit base/allowed hosts, status/error classification, URL redaction; test bằng fake transport.
  3. Parse tree stable order và resource candidates.
  4. Select direct MP4 profile; parse subtitle tracks; extract only explicit attachment links.
  5. Mark restricted/unsupported/unsafe resources bằng structured skip reason; không tạo fallback bypass.
  6. Add sparse/unknown/malformed/401/403/404/429/5xx/redirect/SSRF fixtures.
- **Acceptance**: deterministic manifest snapshot; zero live requests; no cookie fields in manifest; all unsafe/restricted media excluded with reason; no dependency change.
- **Verification**: scoped unittest → full Phase 01+02 offline suite → AST/compile → diff check.
- **Audit event**: `living-spec-change` nếu schema/data model khác; `validation-recorded`.
- **Stop**: báo supported fields/profiles và skipped matrix; chờ Group 3.

## Group 3 — Browser-session adapter + dry-run CLI

- **Objective**: expose authorized session/discovery through dedicated edX CLI with mandatory/obvious dry-run path, still no asset implementation beyond shared fake tests.
- **Likely files**: thin edX entrypoint, provider auth adapter, CLI tests/help docs in scoped files.
- **Steps**:
  1. Add browser-session importer for only browser(s)/OS verified in Group 1; error clearly for unsupported profile.
  2. Build dedicated CLI arguments without touching legacy Coursera positional parsing.
  3. Implement `--dry-run` summary/path plan/skip reasons; strip sensitive query strings.
  4. Add one-time/session compliance notice and confirmation behavior suitable for noninteractive tests.
  5. Ensure session cookies stay memory-only and are scoped by domain; no `data.bin` mutation.
- **Acceptance**: CLI dry-run makes discovery calls only, performs zero asset requests/writes, prints deterministic sanitized summary, and Coursera full suite passes.
- **Verification**: CLI tests with fake importer/transport; captured logs sentinel check; full unittest; diff/public-surface inspection.
- **Audit event**: dependency/manifest authorization only if unavoidable (otherwise none); `validation-recorded`.
- **Stop**: present dry-run evidence and exact live authorization request; wait before Group 4.

## Group 4 — Shared download integration

- **Objective**: feed confirmed manifest into Phase 01 shared planner/executor for direct MP4, subtitle and attachment resources only.
- **Likely files**: provider mapping/wiring, shared workflow only where generic extension is required, scoped tests.
- **Steps**:
  1. Map resource kind/extension/filename metadata to shared plan without provider-specific filesystem writes.
  2. Enforce host/scheme/redirect checks immediately before request; avoid forwarding cookies to untrusted CDN/attachment hosts.
  3. Implement partial/atomic completion policy compatible with shared core; preserve existing complete files and approved resume behavior.
  4. Classify/report per-resource success/skip/failure; bounded retry with 401/403 no retry and 429 handling.
  5. Test rerun/idempotency, expiring signed URL refresh-once behavior if Group 1 proves it necessary.
- **Acceptance**: fake end-to-end course produces exact expected files; restricted/unsupported resources make no asset call; one resource failure does not corrupt completed outputs; Coursera regression remains green.
- **Verification**: scoped fake E2E → full unittest → AST/lint/format if available → tempdir tree snapshot → `git diff --check`.
- **Audit event**: `validation-recorded`; Living Spec if actual retry/partial semantics differ.
- **Stop**: report offline evidence; request separate live walkthrough authorization if not already current/specific.

## Group 5 — Authorized live walkthrough & closeout

- **Objective**: prove one thin real edX.org path and finish Living Spec; no scope expansion.
- **Likely files**: `validation.md`, audit log, roadmap after proof; production fixes only through a separately scoped repeat of Group 4 if live evidence reveals defect.
- **Steps**:
  1. Reconfirm exact course, browser/profile access, output directory and ToS/course permission with user.
  2. Run dry-run; user/maintainer checks counts/paths/skips.
  3. Download a bounded sample or course as authorized; verify direct resource, subtitle and attachment where available.
  4. Rerun to verify existing-file/idempotent behavior; inspect logs for redaction.
  5. Full Coursera+edX regression, spec sync, roadmap status, `merge-ready`.
- **Acceptance**: authorized sample evidence, no restricted request/bypass, no secret persisted/logged, rerun safe, full regression green.
- **Verification**: exact commands/status/output counts recorded in validation; filesystem tree/hash sample; `git status`/diff scope; merge-ready.
- **Audit events**: `validation-recorded`; `phase-complete` and `merge-requested` only when DoD green.
- **Stop**: ask for separate review/commit/merge/push instructions as applicable; never perform automatically.

## Decision / scope change log

| Date | Group | Change discovered | Spec updated | Approval / evidence |
| --- | --- | --- | --- | --- |
| 2026-09-27 | Planning | HLS/YouTube/third-party streams deferred; direct MP4 only | requirements/plan/validation | No approved media dependency; user chose video but not bypass/dependency |
| 2026-09-27 | Planning | `only_on_web` cannot be assumed universal from current Open edX source | requirements | Source verification; Group 1 must confirm actual edX.org schema |
| 2026-09-27 | Planning | Live endpoint/auth spike separated from implementation | plan | API deployment/schema and browser importer are unresolved facts |
