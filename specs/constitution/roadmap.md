# Roadmap & lát cắt bàn giao

> **Trạng thái:** `[ ]` Planned · `[-]` In progress · `[x]` Done · `[!]` Blocked · `[~]` Paused/Superseded. Chỉ đánh Done khi `validation.md` có bằng chứng thật và `merge-ready` pass.

## Quy tắc roadmap

- Refactor Brownfield bắt đầu bằng characterization safety net; không tối ưu dựa trên cảm giác hoặc chỉ tiêu số dòng.
- Mỗi phase phải có outcome chạy được, rollback độc lập và không phá Coursera giữa các lát cắt.
- edX chỉ xử lý nội dung tài khoản được phép truy cập và nền tảng/khóa học cung cấp khả năng tải; không bypass restriction.
- Dependency, manifest, live login/download, commit, merge và push đều có decision gate riêng theo `tech-stack.md`.

## Các phase

- [x] **Phase 01 — Preserve Coursera Behavior & Neutral Download Core**  
  Packet: `specs/phases/2026-09-27-preserve-coursera-behavior/`
  - **Outcome / value**: có characterization suite cho contract Coursera quan trọng và một manifest/workflow trung lập để provider mới reuse mà không sao chép naming/download logic.
  - **Scope**: pure helpers, CLI parse contract, legacy tuple adapter, deterministic traversal, output/skip/overwrite/resume/error behavior; giữ public Coursera APIs/signatures.
  - **Dependencies / assumptions**: cần môi trường Python có dependencies hiện tại; không thêm package mặc định; bootstrap cần approval riêng.
  - **Acceptance**: fixture/tempdir tests khóa exact relative paths và downloader calls; full offline suite pass; live Coursera walkthrough tải thành công 1899 files (427MB) khóa Wharton Quantitative Modeling.
  - **Status**: Hoàn thành toàn diện (83 tests pass, live download pass exit 0, sẵn sàng cho Phase 02 edX).

- [x] **Phase 02 — edX.org Downloadable Course MVP**
  Packet: `specs/phases/2026-09-27-edx-download-mvp/`
  - **Outcome / value**: từ course key hoặc URL `learning.edx.org` và phiên browser hợp lệ, người dùng xem dry-run rồi tải được các video trực tiếp được phép tải, phụ đề và attachment mà khóa học công khai link tải.
  - **Scope**: chỉ edX.org/learning.edx.org; session cookie không password; Course Blocks/enrollment discovery được xác minh bằng fixture; CLI riêng mỏng; reuse neutral core Phase 01.
  - **Dependencies / assumptions**: Phase 01 Done; course mẫu cho phép personal download; endpoint/schema được spike xác nhận; không thêm `yt-dlp`/ffmpeg/Playwright trong MVP.
  - **Acceptance**: mocked API/resource suite pass; restricted/DRM/HLS/YouTube-only content được skip có reason; authorized live walkthrough tải ít nhất một resource được phép và chạy lại idempotent.
  - **Status**: Hoàn thành toàn diện (117 tests pass; live walkthrough xác thực trên khóa MITx 15.481x: 539 resources discovery, 4 files tải thành công 86.6MB, rerun idempotent pass).

- [x] **Phase 03 — Entrypoint & Authentication Simplification**
  - **Outcome / value**: bỏ global `sys.argv` mutation, hợp nhất URL→slug và cookie/session loading; secret không xuất hiện trong debug log; xây dựng unified dispatcher `coursedownloader.py`.
  - **Scope**: `coursera_dl.py`, `general.py`, `cookies.py`, `coursedownloader.py`; giữ alias/default/return/exit behavior đã test.
  - **Dependencies / assumptions**: Phase 01 safety net; edX auth lessons được ghi lại nếu Phase 02 hoàn tất.
  - **Acceptance**: gọi Python API nhiều lần không thay `sys.argv`; auth branches chạy bằng mocks; Coursera & edX CLI compatibility matrix pass (134 tests pass exit 0).
  - **Status**: Hoàn thành toàn diện (134 tests pass, sys.argv immutable, secret redaction, universal JSON/Netscape cookies, unified CLI).

- [ ] **Phase 04 — Coursera Parser Decomposition**
  - **Outcome / value**: chia các concern trong `api.py`/`extractors.py` thành module nhỏ theo API resource/content type, giảm duplication retry/link parsing mà không đổi manifest.
  - **Scope**: một content family mỗi packet con; không big-bang rewrite.
  - **Dependencies / assumptions**: sanitized syllabus fixtures và manifest snapshot của Phase 01.
  - **Acceptance**: trước/sau sinh cùng neutral manifest trên fixture; complexity/duplication delta được ghi trong validation.

- [ ] **Phase 05 — Local State, GUI & Privacy Hardening**
  - **Outcome / value**: xử lý `data.bin` pickle, import-time side effects, telemetry consent, remote HTML và GUI blocking theo phase nhỏ có migration/rollback.
  - **Scope**: `localdb.py`, `livedb.py`, `maingui.py`, Windows-only cookie modules; không trộn vào downloader feature.
  - **Dependencies / assumptions**: user chọn telemetry/state policy và platform support matrix.
  - **Acceptance**: no-secret migration test, GUI command-builder/thread smoke, opt-in network behavior và platform imports pass.

- [ ] **Phase 06 — Optional edX Media Extensions**
  - **Outcome / value**: hỗ trợ HLS/YouTube hoặc các Open edX instance khác nếu nhu cầu và quyền sử dụng được xác nhận.
  - **Scope**: từng capability là packet riêng; dependency/ToS review bắt buộc.
  - **Dependencies / assumptions**: MVP ổn định; phê duyệt `yt-dlp`/ffmpeg hoặc giải pháp khác.
  - **Acceptance**: explicit dependency authorization, fixture + live authorized sample, no DRM/access-control bypass.

## Replanning log

| Date | Phase | Thay đổi | Lý do / bằng chứng | Owner |
| --- | --- | --- | --- | --- |
| 2026-09-27 | Project | Chuyển yêu cầu rộng thành 6 thin slices; tạo packet chi tiết cho Phase 01 và 02 | Repository không có test, provider coupling cao; cần safety-net trước edX | SDD draft, chờ user review |
| 2026-09-27 | Phase 02 | MVP giới hạn edX.org, session browser, video trực tiếp + subtitle + attachment; giữ restricted/HLS/YouTube ngoài scope | Quyết định người dùng + không có dependency media được phê duyệt | User / SDD draft |
