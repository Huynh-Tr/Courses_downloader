# Ranh giới kỹ thuật & kiến trúc

> “Observed” mô tả code hiện tại; “approved target” là kiến trúc đích của các phase đã nêu, không tự động cho phép sửa code.

## 1. Stack quan sát được và đích đã định

| Concern | Observed now | Approved target | Evidence / owner |
| --- | --- | --- | --- |
| Language & runtime | 16 module Python phẳng; `pyproject.toml` target Python 3.10–3.13, README nói 3.6+, máy hiện có Python 3.14.4 | Python >=3.10; xác minh compatibility 3.10–3.13 trước khi đổi support matrix | `pyproject.toml:1-9`, `README.md:53-59`; runtime baseline 2026-09-27 |
| CLI / Python API | `configargparse`; entrypoint `coursera_dl.py`; public wrapper `download_coursera_course()` | Giữ nguyên toàn bộ Coursera surface; edX thêm subcommand/entry rõ ràng, không làm đổi parsing legacy | `commandline.py:46-571`, `coursera_dl.py:277-445`; user decision 2026-09-27 |
| GUI | PyQt5, GUI dựng argv rồi gọi `main_f()` | Chưa mở rộng GUI cho edX trong MVP; GUI Coursera là protected behavior | `maingui.py:62-495` |
| HTTP / parsing | `requests`, BeautifulSoup, JSON API wrappers | Session riêng theo provider; provider adapter trả manifest trung lập cho workflow chung | `coursera_dl.py:84-159`, `extractors.py:23-265` |
| Download / storage | Filesystem local; native streaming hoặc wget/curl/aria2/axel; thread pool | Reuse download primitives và semantics đã kiểm chứng; atomic partial-file policy cho capability mới nếu không làm đổi Coursera | `downloaders.py:30-505`, `parallel.py:39-73`, `workflow.py:264-405` |
| Local state | `data.bin` pickle được track; cookie files được gitignore; cache Coursera dưới `PATH_CACHE` | Không thêm database/migration; edX browser session ở memory trong MVP; fixture được sanitize | `localdb.py:12-89`, `.gitignore:7-10`, tracked `data.bin` |
| Tests | Không có test/config test; `unittest discover` tìm 0 test | Dùng stdlib `unittest` + mocks/fixtures trước; dependency test mới chỉ khi có phase + approval riêng | baseline 2026-09-27 |
| Build, lint, format | Black/Ruff chỉ có config; executable không cài trong môi trường hiện tại | AST/compile + unittest là baseline không dependency; dùng Ruff/Black khi toolchain dev được duyệt/cài | `pyproject.toml:1-14`; baseline 2026-09-27 |
| CI / packaging | Không CI, không package metadata/console entry point | Ngoài scope hai phase hiện tại; phase riêng nếu cần | repository inventory |

## 2. Kiến trúc đích và invariants

- **CLI boundary**: CLI chỉ parse/validate input và dispatch provider; business logic không phụ thuộc `sys.argv` toàn cục.
- **Provider boundary**: mỗi provider chịu trách nhiệm tạo authenticated session, resolve course identifier, duyệt outline và chuẩn hóa resource metadata. Provider không quyết định tên file vật lý hoặc concurrency.
- **Neutral manifest**: provider trả cây `Course → Module → Lesson/Unit → Resource` với stable order, title/slug, resource kind, extension, URL hoặc in-memory payload, và metadata cần thiết cho subtitle/video quality.
- **Download boundary**: workflow chung chịu trách nhiệm safe path, naming, skip/overwrite/resume, bounded concurrency, retry/error collection và filesystem writes.
- **Compatibility adapter**: Coursera legacy tuples/args có thể được bọc bởi adapter; phase refactor đầu tiên không buộc rewrite parser `api.py`/`extractors.py`.
- **External input**: URL, slug, filename, redirect, response schema và content length đều được validate trước khi ghi file.
- **Data integrity**: output path không được escape output root; file dở có trạng thái phân biệt; existing complete file không bị ghi đè nếu người dùng không chọn overwrite.
- **Error handling**: lỗi auth/course/resource phân loại được; 401/403 không retry như transient; 429/5xx retry giới hạn và tôn trọng `Retry-After`; secret không xuất hiện trong log.
- **No cross-provider leakage**: cookie/session Coursera và edX không dùng chung; cookie chỉ gắn vào request tới host được phép.

## 3. Dependency & change policy

- Trước dependency mới: nêu nhu cầu, phương án không dependency, license/maintenance/security impact, rồi nhận phê duyệt bằng văn bản và ghi `dependency-authorized`.
- Không chạy `pip`, tạo/regenerate manifest/lockfile hoặc sửa `requirements.txt`/`pyproject.toml` nếu Task Group chưa nêu và chưa được người dùng cho phép riêng.
- Không đổi public CLI/API/config, output contract, telemetry, GUI, schema hoặc deployment ngoài scope phase.
- edX MVP ưu tiên `requests`, stdlib cookie handling, JSON/HTML parsing sẵn có. Playwright/Selenium, `yt-dlp`, SDK Open edX hoặc browser automation không được thêm mặc định.

## 4. Explicit non-choices

- ❌ Không phá DRM, giải mã media, bypass paywall/enrollment/CAPTCHA/anti-bot hoặc giả lập quyền cao hơn.
- ❌ Không nhận username/password edX trong CLI hoặc lưu browser session vào repo/config mặc định.
- ❌ Không support mọi Open edX deployment trong MVP; chỉ `edx.org`/`learning.edx.org`.
- ❌ Không tải quiz/exam/problem answers, grades, submissions, discussion/private learner data trong edX MVP.
- ❌ Không rewrite `api.py` 1.829 dòng hoặc thay toàn bộ tuple model trong một phase.
- ❌ Không đổi GUI sang framework khác, không thêm ORM/database, không tạo service/web API.
- ❌ Không xóa dependency/Windows module chỉ vì static scan nói “unused”; cần test và phase/approval riêng.
- ❌ Không dùng `--no-check-certificate`/`-k` cho capability mới và không tắt auth/validation để làm path chạy được.

## 5. Câu hỏi kỹ thuật mở

- [ ] Xác minh browser-cookie library nào hiện có thể đọc cookie edX.org trên các OS mục tiêu mà không yêu cầu lưu password; nếu dependency hiện tại không đủ, trình phương án và xin approval.
- [ ] Chụp và sanitize một course outline/sequence fixture thực tế từ tài khoản được phép để xác nhận endpoint/schema edX hiện hành trước Group 2.
- [ ] Quyết định CLI edX cuối cùng sau spike: `python coursera_dl.py edx <url>` hay entry module riêng; cả hai phải không làm mơ hồ legacy positional course slug.
- [ ] Xác định browser/OS bắt buộc cho walkthrough live đầu tiên; unit test phải độc lập OS/browser.
- [ ] Kiểm tra điều khoản/permission của khóa học mẫu và chỉ chạy live download khi người dùng xác nhận quyền tải cá nhân.

## 6. Manifest & lockfile policy

- **Approved language/runtime**: Python >=3.10; target thực tế cần xác minh trên 3.10–3.13.
- **Approved package manager/build tool**: chưa phê duyệt thao tác state-changing; repository hiện dùng `requirements.txt` theo hướng dẫn `pip`.
- **Manifest/config quan sát được**: `requirements.txt`, `pyproject.toml`; không có lockfile.
- [x] Brownfield: chỉ inspect và document; không regenerate/overwrite.
- Mọi thay đổi hai file trên cần nằm trong packet, có rollback và `manifest-authorized`/`dependency-authorized` trước khi thực hiện.
- **Unapproved**: Poetry, uv, Pipenv, Conda manifest, `pip-compile`, lockfile generator, package conversion.

## 7. Git workflow policy

- **Base branch**: `main`.
- **Protected branch**: `main`; không commit/push trực tiếp, không force-push.
- **Feature branch**: `feature/YYYY-MM-DD-phase-slug`, chỉ tạo sau khi packet tương ứng được người dùng duyệt rõ ràng.
- **Commit policy**: mỗi commit cần yêu cầu rõ ràng; không commit tự động. Commit do Claude tạo phải có attribution được hệ thống yêu cầu.
- **Merge policy**: cần lệnh merge riêng sau validation và `merge-ready`.
- **Push policy**: cần lệnh push riêng; approval commit/merge không bao gồm push.
- **Merge method/reviewer**: chưa quyết định; mặc định không tự suy đoán.
