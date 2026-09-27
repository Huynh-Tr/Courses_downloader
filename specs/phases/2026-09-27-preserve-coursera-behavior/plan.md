# Execution Plan: Preserve Coursera Behavior & Neutral Download Core

> **One Group, One Turn.** Sau khi packet được duyệt, SDD chỉ tạo branch local rồi dừng. Mỗi Group cần authorization riêng để triển khai; không tự chuyển sang Group kế.

## 0. Preconditions

- [x] Constitution và Brownfield inventory đã được draft.
- [x] Feature contract được người dùng duyệt (2026-09-27).
- [x] `specs/LOGGING.md` tồn tại.
- [x] `phase-approved` được append sau approval (2026-09-27T08:13:58Z).
- [x] Branch `feature/2026-09-27-preserve-coursera-behavior` được scaffold tạo từ `main` sau approval.
- [x] Base/protected branch policy: `main`, không sửa trực tiếp.
- [x] Baseline read-only: Python 3.14.4; AST parse 16 files pass; CLI fail vì thiếu `bs4`; 0 tests; Ruff/Black chưa cài.
- [x] Bootstrap/install dependencies: không phát sinh cho Phase 01, toàn bộ test suite dùng stdlib unittest và shims.
- [x] Không cần dependency mới về mặt thiết kế cho Group 1–3; dùng stdlib tests.

## Group 1 — Characterization safety net

- **Objective**: khóa contract hiện tại trước khi đổi production seam.
- **Likely files**: `tests/` mới; fixture sanitized dưới `tests/fixtures/`; không sửa production trừ tối thiểu seam import nếu được phê duyệt trong cùng Group.
- **Steps**:
  1. Tạo test network guard và helper args/fake downloader/tempdir.
  2. Test `extract_course_slug`, `general.urltoclassname`, `clean_filename`, naming helpers, `skip_format_url`, `is_course_complete`.
  3. Test `parse_args` defaults/aliases/normalized values mà không chạm auth/network; capture `SystemExit` hợp lệ.
  4. Test `_iter_modules`/`_walk_modules` exact order/relative paths trên legacy tuple fixture.
  5. Test `_handle_resource`: existing, overwrite, resume, skip-download, in-memory, URL skipping và error collection.
  6. Test sequential/parallel wrapper và native Range/206/416/timeout bằng mocks; không sleep thật.
- **Acceptance**: tests mô tả rõ protected contract và pass trên baseline code (ngoại trừ bug/behavior được ghi rõ là known baseline, không “sửa để test pass”).
- **Verification**:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`
  - AST parse command trong `validation.md`
  - `git diff --check`
  - network guard chứng minh không có request thật.
- **Audit event**: `validation-recorded` khi baseline test evidence được ghi.
- **Stop**: báo số tests, files, known behaviors/bugs đã khóa, command/exit; chờ Group 2.

## Group 2 — Neutral model + legacy adapter

- **Objective**: tạo schema provider-neutral, chuyển legacy Coursera tuples sang manifest mà chưa đổi parser/API/public entrypoint.
- **Likely files**: module model/adapter mới (tên quyết định khi code, ví dụ `models.py`/`manifest.py`); test adapter; có thể export nội bộ từ `extractors.py` nhưng không đổi public signature.
- **Steps**:
  1. Định nghĩa immutable records bằng stdlib, validate required fields/order/source kind.
  2. Viết adapter một chiều `legacy Coursera tuple → CourseManifest`.
  3. Chuyển snapshot tests thành equivalence: flattened neutral manifest phải khớp legacy traversal cho mọi fixture/options áp dụng.
  4. Không thay `CourseraExtractor.get_modules()` return type và không ghi filesystem.
- **Acceptance**: adapter deterministic; malformed input fail rõ; Coursera public/import/tuple contract không đổi; suite Group 1 vẫn pass.
- **Verification**: scoped adapter tests → full unittest → AST parse → `git diff --check`.
- **Audit event**: `living-spec-change` chỉ nếu schema thực tế lệch requirements; nêu lý do trước/đồng thời update spec.
- **Stop**: báo model/schema, equivalence evidence và remaining coupling; chờ Group 3.

## Group 3 — Shared planning/workflow seam

- **Objective**: dùng neutral manifest để lập download plan/tên path chung, đồng thời giữ legacy Coursera facade.
- **Likely files**: `workflow.py`; neutral model/adapter module; tests; tối thiểu wiring trong `coursera_dl.py` nếu cần.
- **Steps**:
  1. Tách pure “manifest → planned resources/relative paths” khỏi filesystem/download execution.
  2. Cho `CourseraDownloader` facade gọi shared planner/executor hoặc adapter, giữ constructor/method/attributes public.
  3. Loại duplication/nesting chỉ trong traversal/path seam; không sửa unrelated bugs.
  4. Chạy exact before/after path + fake downloader equivalence, gồm options matrix đã khóa.
- **Acceptance**: same Coursera files/downloader calls/status lists trên fixtures; neutral workflow là seam Phase 02 có thể reuse; không thêm network pass/dependency.
- **Verification**: scoped workflow tests → full unittest → AST parse → optional Ruff/Black chỉ nếu tools đã có/được cho phép → diff inspection.
- **Audit event**: `validation-recorded`; `living-spec-change` nếu cần.
- **Stop**: báo code delta (files/line/complexity), compatibility evidence, deferred items; chờ Group 4.

## Group 4 — Regression, docs & Living Spec sync

- **Objective**: chứng minh phase hoàn tất, không triển khai edX.
- **Likely files**: phase `validation.md`, constitution/roadmap nếu facts đổi; README chỉ khi phase được mở rộng và user duyệt.
- **Steps**:
  1. Chạy full offline ladder từ fresh approved environment.
  2. Chạy import/CLI `--version`/help smoke; live Coursera walkthrough chỉ với approval/session riêng.
  3. Inspect `git diff`, dependency/manifest/public API delta; xác nhận không ngoài scope.
  4. Sync Living Spec; chỉ đánh roadmap Done khi DoD pass.
  5. Chạy `sdd-scaffold.sh merge-ready 2026-09-27-preserve-coursera-behavior main` (read-only).
- **Acceptance**: tất cả proof áp dụng được green; spec đủ để agent mới bắt đầu Phase 02.
- **Audit event**: `validation-recorded`, rồi `phase-complete`/`merge-requested` chỉ nếu đủ điều kiện.
- **Stop**: yêu cầu review/merge instruction riêng; không commit/merge/push tự động.

## Decision / scope change log

| Date | Group | Change discovered | Spec updated | Approval / evidence |
| --- | --- | --- | --- | --- |
| 2026-09-27 | Planning | First slice dùng stdlib tests, không mặc định thêm pytest/responses | requirements/plan/validation | Dependency policy + repo baseline; chờ packet approval |
