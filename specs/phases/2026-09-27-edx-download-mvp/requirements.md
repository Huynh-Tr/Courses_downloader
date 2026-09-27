# Feature Contract: edX.org Downloadable Course MVP

> **Decision gate:** Không code/live-login/live-download trước khi Phase 01 Done, packet này được duyệt và Group 1 xác minh endpoint/schema bằng fixture đã sanitize. “Authorized access” không đồng nghĩa mọi nội dung được phép sao chép; downloader chỉ xử lý resource có download URL hợp lệ và không bypass restriction.

## 1. Context, goal & outcome

- **Roadmap**: Phase 02 trong `specs/constitution/roadmap.md`.
- **Cơ hội**: mở rộng downloader từ Coursera sang edX.org mà không sao chép file-transfer/naming logic hoặc làm hỏng behavior Coursera.
- **Primary actor**: người học đăng nhập hợp lệ trên edX.org, đã ghi danh khóa học và có quyền cá nhân đối với resource được nền tảng/khóa học cho tải.
- **Outcome**: CLI nhận một internal course key hoặc URL course-run `learning.edx.org`, import phiên browser hiện có, hiển thị dry-run manifest, rồi tải video MP4 trực tiếp không restricted, subtitle/transcript và downloadable attachment vào cây thư mục ổn định bằng shared workflow.
- **Success evidence**:
  - offline fixtures mô phỏng enrollment + Course Blocks + sequence/HTML/resource responses;
  - restricted/locked/DRM/HLS/YouTube-only resource được skip với reason, không bypass;
  - live walkthrough riêng trên một course mẫu được người dùng xác nhận quyền, tải ít nhất một resource được phép và rerun idempotent.

## 2. Decisions already set by user (2026-09-27)

- Phạm vi MVP: **chỉ edX.org** (bao gồm learner host chính thức cần thiết như `learning.edx.org`, không phải mọi Open edX site).
- Xác thực: **phiên trình duyệt hiện có**, không username/password.
- Nội dung MVP: **video + phụ đề + tệp đính kèm**.
- Compatibility: Coursera **giữ nguyên tuyệt đối**; edX không được làm đổi legacy CLI/API/output.

## 3. In scope — contractual requirements

| ID | Requirement / behavior | Actor & input | Expected output / state | Acceptance evidence |
| --- | --- | --- | --- | --- |
| E1 | Parse/validate edX identifier | internal `course-v1:...` key hoặc URL course-run thuộc allowlist edX.org | canonical course key; marketing URL không map được thì hướng dẫn list/resolve, không scrape mù | parser/lookup fixture tests |
| E2 | Import browser session | browser name/profile path theo interface được chốt ở Group 1 | session có cookies cần thiết trong memory; không log/lưu password/cookie | fake cookie importer tests + sentinel log test |
| E3 | Verify authenticated enrollment | session + course key | course chỉ tiếp tục nếu enrollment/blocks response cho user hiện tại; 401/403 rõ ràng | mocked 200/401/403 tests |
| E4 | Discover course tree | Course Blocks API/learner endpoints đã xác minh | neutral manifest có stable chapter/sequential/vertical ordering; chỉ visible blocks | sanitized fixture snapshot |
| E5 | Select downloadable video | video block data | ưu tiên direct HTTPS MP4 profile theo quality policy; restricted/`only_on_web`/DRM/HLS/YouTube-only không bị bypass và được skip reason | profile matrix tests |
| E6 | Discover subtitles | transcript metadata/handler URL | track theo requested language; extension/content validated; unavailable được report | transcript fixture tests |
| E7 | Discover attachments | learner-visible HTML/unit response có explicit downloadable links | chỉ HTTPS attachment allowlisted/validated; safe filename/type; không crawl ngoài unit/course | link fixture + SSRF/path tests |
| E8 | Preview/dry-run | canonical course + session | in manifest/path/resource count/skip reasons mà không tải asset | CLI test proves zero asset requests/writes |
| E9 | Download via shared core | confirmed manifest + output/options | hierarchy/naming/skip/overwrite/resume/error semantics reuse Phase 01; file dở không được coi complete | fake/live resource tests |
| E10 | Bounded requests/retries | API/resource failures | 401/403 no retry; 404 skip/report; 429 respects `Retry-After`; transient timeout/5xx limited | mock call-count/timing tests (sleep patched) |
| E11 | Compliance guardrails | all runs | visible warning/responsibility notice; no bypass path; personal-use scope | CLI/help + code-path tests |
| E12 | Coursera isolation | full legacy suite | no Coursera contract delta | Phase 01 regression pass |

## 4. Non-functional requirements

- **Security/auth**:
  - không nhận edX password; browser login/SSO/MFA diễn ra ngoài tool;
  - cookies chỉ ở memory trong MVP, không ghi log/spec/fixture/output;
  - allowlist scheme `https` và official edX learner/API hosts; attachment redirects được revalidate; chặn credential-in-URL, localhost, loopback, private/link-local/multicast/reserved IP và DNS rebinding ở mức thực tế;
  - không gửi edX cookies sang arbitrary attachment/CDN host. CDN URL công khai/signed thử không cookie trước; nếu provider yêu cầu cookie thì host phải nằm trong explicit allowlist được fixture/live spike chứng minh.
- **Compliance**: edX Terms (cập nhật 2025-11-03) giới hạn personal, non-commercial use và cấm spiders/crawlers cũng như circumvent access/copy controls. Feature này vì vậy phải opt-in, scoped một course, rate-limited, không auto-crawl catalog và không bảo đảm việc dùng tool phù hợp với mọi course/địa phương. Người dùng chịu trách nhiệm xác nhận quyền/điều khoản.
- **Performance/scale**: mặc định một course/run; bounded concurrency nhỏ (mặc định 1 cho live MVP cho tới khi rate behavior được chứng minh); pagination/depth có giới hạn; không fetch lại cùng block/resource trong một run.
- **Compatibility**: provider mới không đổi Coursera positional parsing; edX MVP dùng entrypoint/subcommand tách rõ; output root tách theo provider/course.
- **Observability**: summary gồm discovered/downloaded/skipped/failed và reason categories; URL log phải strip query/signature/token.
- **Schema resilience**: missing/unknown block/profile không crash toàn course; report unsupported; fixture contract tách parsing khỏi HTTP.

## 5. Out of scope

- ⛔ Mọi Open edX self-hosted domain; configurable arbitrary base URL.
- ⛔ Username/password/API login, browser automation, CAPTCHA/MFA/SSO automation, session persistence.
- ⛔ DRM, `only_on_web`, download-disabled, geoblocked, locked/gated hoặc inaccessible resources; không tìm endpoint ẩn để né restriction.
- ⛔ HLS (`.m3u8`), DASH, encrypted media, YouTube/Vimeo/third-party streaming trong MVP; không thêm `yt-dlp`/ffmpeg.
- ⛔ Quiz/exam/problem answers, grade/submission, discussion, notes, learner analytics, certificates, labs/notebooks.
- ⛔ Full HTML offline mirror, recursive link crawl, images/styles/scripts không phải explicit downloadable attachments.
- ⛔ Course catalog/bulk account crawling, multi-account, mass parallel download.
- ⛔ edX GUI integration; unified cross-provider CLI; list-all UI ngoài minimal course-key resolution cần thiết.
- ⛔ Thay Coursera parser/workflow ngoài seam Phase 01.

## 6. Decisions & alternatives

| Decision | Chosen approach | Alternatives rejected/deferred | Rationale & consequence |
| --- | --- | --- | --- |
| D1 | Cookie/session từ browser | password login/API token | tương thích SSO/MFA hơn, giảm secret handling |
| D2 | Chỉ official edX.org hosts | generic Open edX base URL | giảm auth/schema/ToS/test matrix |
| D3 | Primary discovery qua documented/source-backed Course Blocks/enrollment APIs, sau Group 1 spike | scrape dashboard/course HTML toàn diện | API tree dễ fixture/test hơn; không cam kết endpoint public/stable trước spike |
| D4 | Reuse neutral manifest/download workflow | `edx_dl.py` tự tải độc lập | tránh duplication và giữ semantics thống nhất |
| D5 | Direct MP4 only trong MVP | `yt-dlp`, ffmpeg, HLS/YouTube | không thêm dependency và tránh media-restriction ambiguity |
| D6 | Dry-run trước live asset download | tải ngay sau discovery | user kiểm tra scope, resource count và skips trước network/write lớn |
| D7 | Marketing URL chỉ được resolve qua authenticated enrollment/course metadata; nếu không map thì yêu cầu course key | scrape/search site hoặc đoán course key | tránh crawler/catalog behavior và mapping sai |
| D8 | Explicit attachment extraction từ learner-visible unit only | recursive crawler | bounded, auditable và giảm SSRF/data exfiltration |
| D9 | Dedicated edX CLI entry mỏng trong MVP; unified dispatch deferred | thêm positional platform detection vào legacy CLI ngay | bảo vệ absolute Coursera compatibility |

## 7. Data, interfaces & state

- **Internal data**: dùng `CourseManifest` neutral của Phase 01; provider metadata tối thiểu có `block_id`, `block_type`, `downloadability`, `language`, `media_profile`, `requires_auth` nhưng không chứa cookie.
- **CLI contract draft** (tên cuối khóa trong Group 1 sau spike, không làm đổi legacy parser):
  ```text
  python3 edx_dl.py --browser <supported-browser> --path <dir> --dry-run <course-key-or-learning-url>
  python3 edx_dl.py --browser <supported-browser> --path <dir> <course-key-or-learning-url>
  ```
  Nếu codebase chọn subcommand/module khác, requirements vẫn giữ semantics và cần Living Spec update trước Group 3.
- **No persisted migration**: không database, không cookie file mặc định, không update `data.bin`.
- **Output**: `<path>/edx/<sanitized-course-slug-or-key>/...`; child path do shared planner tạo và không escape root.
- **Partial files**: implementation phải dùng explicit temp/partial marker hoặc shared resume policy; rename complete atomically khi có thể. Không overwrite complete file trừ option approved.
- **Failure categories**: `AUTH_REQUIRED`, `NOT_ENROLLED_OR_FORBIDDEN`, `COURSE_NOT_FOUND`, `RATE_LIMITED`, `SCHEMA_UNSUPPORTED`, `RESTRICTED_MEDIA`, `UNSUPPORTED_MEDIA`, `UNSAFE_URL`, `RESOURCE_FAILED`.

## 8. Edge cases & risks

| Case / risk | Expected behavior | Evidence / mitigation |
| --- | --- | --- |
| Expired/missing session | fail before asset download, hướng dẫn đăng nhập/retry; no password prompt | 401/redirect fixture |
| SSO/MFA account | browser session works if valid; tool không automate challenge | auth design |
| Marketing URL không map enrollment | no crawl/guess; list matching enrolled course IDs or request canonical key | lookup fixture |
| Legacy vs opaque course key | URL-encode safely; preserve canonical key | parser/API tests |
| Missing children/unknown XBlock | keep remaining tree, skip/report unknown block | sparse schema fixtures |
| Direct URL signed/expired | refresh metadata once if safe; otherwise report resource failure, no infinite retry | expiry fixture/call count |
| `only_on_web`, HLS, YouTube-only | skip with explicit restriction/unsupported reason | profile tests |
| Transcript returns HTML/login page | validate status/content before `.srt/.vtt`; treat auth failure | content-type fixture |
| Attachment points external/private host | reject unsafe target/redirect; never forward cookies blindly | SSRF/redirect tests |
| Duplicate titles/resources | stable index/path; avoid accidental overwrite; dedupe same canonical resource | manifest/path snapshot |
| Course changes mid-run | complete discovered manifest; summary notes failures; rerun rediscovers current tree | idempotency test |
| 429/5xx/timeouts | bounded retry, `Retry-After`, no burst | mocked clock/sleep |
| ToS/course license disallows automation/copy | do not run; dry-run notice and user responsibility | explicit live gate |

## 9. External evidence (verified 2026-09-27)

- edX Terms of Service last updated 2025-11-03: personal/non-commercial limited license; automated retrieval and circumvention restrictions: <https://www.edx.org/edx-terms-service>.
- Open edX Course Blocks view parameters/response: <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/course_api/blocks/views.py>.
- Current Course Blocks URL definitions include `v1/blocks/` and `v2/blocks/` under the courses API include; exact deployed prefix must be confirmed by Group 1: <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/course_api/blocks/urls.py>.
- Enrollment route include exists at `api/enrollment/v1/` and `v2/`: <https://github.com/openedx/edx-platform/blob/master/lms/urls.py>.
- Open edX login source shows CSRF-protected session login and third-party-auth restrictions, supporting the choice to avoid password automation: <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/login.py>.
- Video implementation shows direct profiles/transcript metadata and download gating, but current source did **not** verify the research claim that an `only_on_web` field is universally present. Group 1 must use an actual sanitized edX.org response before relying on any field: <https://github.com/openedx/edx-platform/blob/master/xmodule/video_block/video_block.py>.

## 10. Approval/open decision gate

- [x] Platform: edX.org only.
- [x] Auth: browser session only.
- [x] Content: video + subtitles + attachments.
- [x] Coursera compatibility: absolute.
- [ ] Phase 01 must be completed and merged/available as base before this phase branch.
- [ ] User must approve this packet and separately authorize browser profile access/live course test.
- [ ] Group 1 must identify supported browser importer(s) on target OS without adding dependency; if impossible, stop and present dependency/options.
- [ ] Group 1 must confirm actual edX.org host/endpoint/schema and direct-download indicators from an authorized sanitized fixture.
- **Approved by / date**: chưa duyệt.
