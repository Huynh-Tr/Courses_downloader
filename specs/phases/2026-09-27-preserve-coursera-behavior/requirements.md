# Feature Contract: Preserve Coursera Behavior & Neutral Download Core

> **Decision gate:** Packet này phải được duyệt trước khi tạo branch hoặc sửa production/test code. “Giữ nguyên tuyệt đối” là quyết định sản phẩm; bugfix có thể quan sát cần packet/approval riêng, không lẫn vào refactor.

## 1. Context, goal & outcome

- **Roadmap**: Phase 01 trong `specs/constitution/roadmap.md`.
- **Vấn đề**: core chưa có test; provider discovery, legacy tuples, naming, download policy và CLI/GUI coupling khiến việc rút gọn hoặc thêm edX có nguy cơ regression cao.
- **Actor**: maintainer/coding agent; người dùng Coursera hiện tại là bên được bảo vệ.
- **Outcome**:
  1. offline characterization suite khóa các contract Coursera ưu tiên;
  2. một neutral course-resource model và adapter từ legacy Coursera tuples;
  3. workflow chung có thể duyệt neutral model nhưng tạo cùng output/calls như trước;
  4. code được rút gọn ở đúng seam (traversal/naming/policy), không đổi public surface.
- **Success evidence**: exact-path snapshots, fake downloader calls, CLI parse matrix, tempdir behavior, before/after fixture manifest equality và full offline regression đều pass.

## 2. In scope — contractual requirements

| ID | Requirement / behavior | Actor & input | Expected output / state | Acceptance evidence |
| --- | --- | --- | --- | --- |
| R1 | Characterize pure contracts | URL/slug, filenames, formats, mtime boundary | Kết quả hiện tại được khóa, gồm edge cases | unit table tests |
| R2 | Characterize CLI contract | legacy args/config-free input | aliases, defaults, normalized lists, validation/exit giữ nguyên | parser snapshot matrix |
| R3 | Characterize hierarchy/naming | sanitized Coursera module tuple fixture + args | exact relative module/section/file paths và stable order như hiện tại | manifest snapshot |
| R4 | Characterize write policy | fake downloader + tempdir + existing/missing files | overwrite/resume/skip/in-memory/skip-download/callback semantics giữ nguyên | isolated workflow tests |
| R5 | Characterize transfer wrappers | fake sequential/parallel/native responses | callback, join, Range, 206/416, timeout retry count giữ nguyên | mock tests |
| R6 | Introduce neutral immutable model | adapter nhận legacy tuples | `Course/Module/Section/Resource` (hoặc tên tương đương) không chứa Coursera HTTP/API details | model + adapter tests |
| R7 | Reuse workflow | neutral model đi qua traversal/download seam | cùng relative paths và downloader invocation với fixture legacy | before/after equivalence test |
| R8 | Keep compatibility | CLI, GUI command path, Python wrapper, output tree, logs/errors được bảo vệ | không breaking change; legacy entrypoints vẫn tồn tại | import/signature + parser + fixture regression |
| R9 | Bounded simplification | traversal/model seam liên quan trực tiếp | giảm duplication/nesting/global coupling có số liệu; không đổi behavior để giảm dòng | diff + complexity note |
| R10 | No external writes/network in tests | full offline test run | không truy cập Coursera/Firebase/ipinfo/browser profile; chỉ tempdir | network guard/mocks + test output |

## 3. Non-functional requirements

- **Security**: fixture không chứa CAUTH/cookie/token/PII; test redacts secrets; không đọc browser profile hoặc `data.bin` thật.
- **Performance**: không làm giảm parallelism hay thêm network pass; neutral adaptation O(number of resources), stable order.
- **Compatibility**:
  - giữ tên/signature/import path của `main_f`, `download_coursera_course`, `CourseraExtractor`, `CourseraDownloader`, downloader classes và legacy flags;
  - giữ exact relative path, numbering, default options, file-format selection, overwrite/resume/skip và callback/error collection trong phạm vi đã test;
  - không thay manifest/dependency ở phase này nếu chưa có authorization bổ sung.
- **Observability**: test failure phải cho biết contract/path/resource bị lệch; production logging không được tăng độ nhạy cảm.
- **Portability**: suite nền tảng lõi chạy không cần Windows API, GUI/display, browser hoặc live network.

## 4. Out of scope

- ⛔ edX provider implementation hoặc edX live call (Phase 02).
- ⛔ Sửa những bug hiện có nếu việc sửa làm thay đổi output/exception/CLI behavior; chỉ ghi backlog.
- ⛔ Xóa/upgrade dependency, thay `requirements.txt`, tạo lockfile/package metadata hoặc cài tool.
- ⛔ Di chuyển toàn bộ source vào package, rewrite toàn bộ `api.py`/`define.py`, đổi framework GUI.
- ⛔ Telemetry/privacy migration, pickle migration, GUI threading, Windows support cleanup.
- ⛔ Live Coursera download nếu người dùng chưa cho phép và chưa cung cấp session/course thích hợp.
- ⛔ Chỉ tiêu “giảm X% dòng code”; code ngắn hơn nhưng khó hiểu/khó test không được chấp nhận.

## 5. Decisions & alternatives

| Decision | Chosen approach | Alternatives rejected/deferred | Rationale & consequence |
| --- | --- | --- | --- |
| D1 | Safety-net trước refactor | đổi cấu trúc rồi viết test | không có baseline test; tránh khóa nhầm behavior sau rewrite |
| D2 | stdlib `unittest`/mock/tempfile ở first slice | thêm pytest/responses ngay | không cần dependency/manifest authorization để bắt đầu |
| D3 | Adapter bọc legacy tuples vào neutral model | buộc Coursera parser sinh model mới ngay | giảm blast radius; cho phép equivalence proof |
| D4 | Workflow chung sở hữu path/naming/download policy | mỗi provider tự tải và đặt tên | tránh duplication và drift giữa Coursera/edX |
| D5 | Immutable typed records (`dataclass(frozen=True)` hoặc `NamedTuple`, chọn sau spike nhưng không external dep) | dict tự do hoặc `attrs` cũ | schema rõ, fixture comparison dễ; giữ external dependency khỏi model |
| D6 | Một seam/lát cắt mỗi Task Group | big-bang split module | rollback và review dễ hơn |
| D7 | Compatibility tuyệt đối trong phase | nhân cơ hội sửa CLI/GUI bugs | đúng quyết định người dùng; bugfix phải có contract riêng |

## 6. Data, interfaces & state changes

- **Data model đề xuất** (internal only; tên cuối có thể chỉnh trong Group 2 mà không đổi semantics):
  - `CourseManifest(provider, course_id, slug, title, modules)`
  - `Module(index, slug, title, sections)`
  - `Section(index, slug, title, resources/lessons)`
  - `Resource(index, kind, format, title, source, metadata)`
  - `source` là HTTPS URL hoặc explicit in-memory content type, không dùng magic string ở provider mới.
- **Migration**: không migration persisted data. Legacy Coursera tuple adapter là compatibility bridge.
- **Public interface**: không đổi. Neutral model/workflow ban đầu là internal API.
- **Filesystem**: chỉ test tempdir được ghi; production path behavior không đổi.
- **Failure behavior**: adapter từ chối malformed fixture bằng exception nội bộ rõ ràng; production legacy path không nhận schema mới cho tới khi equivalence tests pass.

## 7. Constraints, risks & edge cases

| Case / risk | Expected behavior | Evidence / mitigation |
| --- | --- | --- |
| Empty course/modules/sections/resources | không crash; kết quả/complete semantics được khóa theo hiện trạng | empty fixture tests |
| Duplicate titles/slugs | exact current naming/collision behavior được bảo toàn; không tự đổi tên ngoài contract | snapshot/tempdir tests |
| Unicode/forbidden/trailing characters | giữ `clean_filename` và unrestricted mode behavior | character table |
| Combined numbering, reverse/filter | stable numbering/order đúng current behavior | option matrix |
| Existing complete/partial file | skip/overwrite/resume invocation không đổi | fake downloader + byte fixtures |
| In-memory HTML | ghi UTF-8 và không gọi downloader | exact file content |
| Invalid/local/mailto resource URL | skip list và disable override giữ nguyên | URL matrix |
| Callback exception/failure | URL vào `failed_urls`; one failure không mất các result khác | fake callback tests |
| Parallel nondeterminism | deterministic manifest/path planning; callback semantics không giả định completion order nếu code hiện tại không đảm bảo | separated planning/execution tests |
| Environment thiếu dependencies | dừng và xin bootstrap authorization; không tự cài | validation baseline |
| Test accidentally hits network | fail fast | patch `Session.request`/socket ở suite core |

## 8. Approval gate

- **Đã chốt từ người dùng (2026-09-27)**: mức tương thích “giữ nguyên tuyệt đối”.
- **Chờ duyệt packet**: scope R1–R10, internal neutral model và Task Groups trong `plan.md`.
- **Không được suy diễn từ việc duyệt spec**: cài dependency, commit, merge, push hoặc live Coursera access.
- **Approved by / date**: chưa duyệt.
