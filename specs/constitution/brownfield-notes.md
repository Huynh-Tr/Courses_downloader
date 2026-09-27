# Brownfield Discovery & Safety Net Notes

## 1. Mục tiêu refactor

- **Target flow**: CLI/Python API `coursera_dl.py` → auth/session → `CourseraExtractor` → legacy module tuples → `CourseraDownloader` → native/external downloader; GUI tiếp tục gọi cùng legacy CLI flow.
- **Pain point quan sát được**:
  - không có test nào nhưng core có nhiều nhánh network/filesystem và global state;
  - provider-specific parsing/auth/CLI trộn với workflow chung;
  - duplication URL→slug và CAUTH extraction;
  - các module lớn (`api.py` 1.829 dòng, `define.py` 1.002 dòng, `commandline.py` 571 dòng);
  - một số global side effect (`sys.argv`, `os.chdir`, import-time local/remote config) làm code khó test/reuse;
  - manifest chứa dependency cũ/không rõ còn dùng, nhưng chưa có bằng chứng đủ để xóa.
- **Protected behavior**: tương thích tuyệt đối theo quyết định người dùng ngày 2026-09-27; xem bảng dưới.
- **Không nhắm tới trong phase bảo toàn Coursera**: edX implementation, UI redesign, telemetry redesign, dependency cleanup, package layout migration, đổi CLI/API/output, sửa mọi bug quan sát được trong một lần.

## 2. Inventory (observed facts)

| Area | Observed fact | Evidence | Confidence |
| --- | --- | --- | --- |
| Git | `main` theo dõi `origin/main`; baseline commit `70684ea`; trước scaffold tree sạch | `git status --short --branch`, `git log -1` | High |
| Runtime | Python source phẳng, 16 file/7.247 dòng; config Black/Ruff target 3.10–3.13; runtime máy là Python 3.14.4 | `pyproject.toml:1-14`; `wc -l`; baseline command | High |
| Entrypoints | CLI/Python API tại `coursera_dl.py`; GUI tại `maingui.py` | `coursera_dl.py:277-445`, `maingui.py:487-495` | High |
| CLI | `configargparse` định nghĩa legacy flags/defaults; config local `coursera-dl.conf` nếu có | `commandline.py:32-571` | High |
| Coursera discovery | JSON syllabus được parse thành module/lesson/item tuples; content type dispatch nằm trong một hàm 177 dòng | `extractors.py:50-265` | High |
| Download workflow | Naming/hierarchy/filter/skip/write/hook/playlists nằm trong `workflow.py` | `workflow.py:43-405` | High |
| File transfer | Native `requests` hoặc wget/curl/aria2/axel; timeout 30s, timeout retry 1 ở wrapper | `downloaders.py:18-19,30-505` | High |
| Parallelism | `multiprocessing.dummy.Pool` khi `--jobs > 1` | `coursera_dl.py:205-210`, `parallel.py:54-73` | High |
| State | File local; `data.bin` pickle được track; cookie files/output được ignore | `localdb.py:12-89`, `.gitignore:1-17`, `git ls-files data.bin` | High |
| Tests/CI | Không có tests/CI/Makefile/tox; `unittest discover` chạy 0 test | repository scan; baseline 2026-09-27 | High |
| Dependencies | `requirements.txt` hard-pin phần lớn runtime/GUI packages; `pyproject.toml` không phải package manifest đầy đủ | `requirements.txt:1-16`, `pyproject.toml:1-14` | High |
| Platform | GUI/cookie modules có Windows-specific behavior; CLI core phần lớn cross-platform | `edge_cookies.py`, `locked_cookie.py`, `general.py:38,67-109` | High |
| External systems | Coursera APIs/CDN; GUI gọi Firebase và ipinfo | `define.py:11-162`, `livedb.py:12-129` | High |

## 3. Runtime flow hiện tại

```text
CLI URL shortcut / legacy flags
  -> parse_args
  -> create_session (CAUTH / browser / Edge / cookie file / login)
  -> optional specialization expansion
  -> CourseraExtractor.get_modules
  -> CourseraOnDemand/API parsing
  -> legacy module/section/lecture/resource tuples
  -> CourseraDownloader.download_modules
  -> ConsecutiveDownloader | ParallelDownloader
  -> NativeDownloader | wget/curl/aria2/axel
  -> filesystem + optional playlists/hooks
```

GUI đọc/ghi `data.bin`, dùng `rookiepy` lấy CAUTH, dựng legacy argv rồi gọi `main_f(cmd)` đồng bộ (`maingui.py:364-480`). GUI cũng kết nối Firebase/ipinfo trong background (`maingui.py:97,258-281`, `livedb.py:76-120`).

## 4. Protected Coursera contract

| Contract cần giữ | Evidence hiện tại | Characterization proof phải có trước refactor liên quan |
| --- | --- | --- |
| Legacy CLI flags, aliases, defaults, config-file behavior và exit semantics | `commandline.py:32-571` | parse matrix/snapshot không network |
| URL shortcut + `download_coursera_course(course_url, output_path, cookies_file)` | `coursera_dl.py:363-445` | valid/invalid URL, default path/cookie, return value, argv isolation |
| Auth branches: CAUTH, browser, Edge fallback, Netscape cookie file, username/password | `coursera_dl.py:95-159` | mocked session/cookie tests; không log secret |
| Output hierarchy theo course/module/section | `workflow.py:148-232,286-328` | fixture manifest → exact relative path snapshot |
| File names `NN_slug[_title].ext` và combined `NN_NN_...` | `workflow.py:95-128` | exact naming table, truncation/sanitization |
| Existing file skip trừ overwrite; resume path vẫn được gọi | `workflow.py:345-397` | tempdir + fake downloader |
| `#inmemory#` HTML được ghi UTF-8 | `workflow.py:376-380` | exact bytes/text test |
| URL format skipping và `--disable-url-skipping` | `workflow.py:43-57,382-388` | valid/invalid/local/mailto matrix |
| `--jobs > 1` dùng parallel wrapper, còn 1 dùng sequential | `coursera_dl.py:205-210`, `parallel.py:39-73` | fake downloader/callback order + join |
| Native resume gửi `Range: bytes=N-`, chấp nhận 206/416 | `downloaders.py:396-477` | mocked response tests |
| Timeout 30s, retry một lần rồi skip ở wrapper | `downloaders.py:18-19,51-118` | fake timeout downloader call count/result |
| Subtitle selection/fallback hiện tại, gồm fallback English khi requested language vắng | `api.py:1266-1275` | sanitized lecture fixture |
| Specialization expansion | `coursera_dl.py:299-300`, `api.py:639-682` | mocked API response/order |
| Optional playlists/hooks/filters/reverse/quizzes/notebooks | `commandline.py`, `workflow.py`, `extractors.py` | parser + scoped fixture tests trước khi sửa các vùng này |
| Course-complete heuristic 30 ngày | `workflow.py:319-324`, `utils.py:188-205` | frozen time/boundary test |
| GUI input → legacy argv mapping và Resume path | `maingui.py:364-480` | unit test command builder sau khi tách seam; GUI smoke nếu thay GUI |

## 5. Baseline thực thi ngày 2026-09-27

| Command | Kết quả quan sát | State change |
| --- | --- | --- |
| `python --version` | command không tồn tại, exit 127 | none |
| `python3 --version` | Python 3.14.4, exit 0 | none |
| `PYTHONDONTWRITEBYTECODE=1 python3 coursera_dl.py --version` | `ModuleNotFoundError: No module named 'bs4'`, exit 1 trước khi parser chạy | none |
| AST parse tất cả root `*.py` bằng `python3` | Parse thành công 16 file, exit 0 | none |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v` | 0 tests; exit 5 (`NO TESTS RAN`) | none |
| `ruff check .` / `black --check .` | executable chưa cài, exit 127 | none |
| `git status --short --branch` trước scaffold | `main...origin/main`, clean | none |

**Kết luận baseline**: syntax parse được, nhưng chưa thể chạy app/test/lint trong môi trường hiện tại vì runtime dependencies/dev tools chưa cài. SDD không coi đây là green baseline và không tự chạy `pip install`.

## 6. Safety net cần tạo trước refactor

1. Dùng `unittest`, `unittest.mock`, `tempfile` và fixture local để không thêm dependency ở lát đầu.
2. Khóa pure contracts trước: URL/slug; filename cleaning/naming; resource format filtering; course-complete heuristic.
3. Khóa workflow bằng fake downloader/tempdir: hierarchy, existing/overwrite/resume, in-memory, failed/skipped collection, parallel wrapper.
4. Khóa auth/API bằng fake session và sanitized JSON fixture, không có live token/network.
5. Chỉ refactor seam đã có characterization proof; Coursera live smoke là bước opt-in riêng sau test offline.

## 7. Rủi ro & unknowns

| Risk / unknown | Impact | Evidence needed | Owner / next action |
| --- | --- | --- | --- |
| README nói Python 3.6+, config target 3.10+ và runtime 3.14 thiếu deps | High | test matrix 3.10–3.13; quyết định support floor | maintainer, phase riêng |
| Không có executable baseline do dependencies chưa cài | High | user-authorized environment/bootstrap command | user decision trước execution |
| `data.bin` là pickle được track, có thể chứa state/config nhạy cảm | High | inspect/sanitize migration plan; không dump secret vào spec | security phase riêng |
| CAUTH được log ở DEBUG | High | regression test redaction + approved fix | security phase riêng |
| GUI truyền `--cache-syllabus` nhưng parser không định nghĩa | Medium | GUI command-builder test; quyết định fix semantics | bugfix phase sau safety net |
| URL→slug và browser auth có nhiều implementation | Medium | shared characterization table | refactor slices sau safety net |
| `sys.argv`, `os.chdir`, import-time DB config gây global side effects | Medium | isolation tests | refactor slices |
| Một số dependency có vẻ unused/old | Medium | import tracing + platform smoke tests | dependency audit riêng, không xóa sớm |
| edX endpoint/schema có thể thay đổi và course content khác nhau | High | sanitized authorized fixture + contract tests | edX Group 1 |
| Terms/course policy có thể hạn chế automated download | High | user confirms course permission; downloader skips restricted content | user + maintainer |

## 8. Ranh giới refactor đầu tiên

- **Thin slice đầu**: chỉ thêm characterization safety net offline và một neutral resource model/adapter seam tối thiểu; chưa đổi legacy output hoặc xóa module/dependency.
- **Invariant sau slice**: mọi protected behavior được phase chọn vẫn cho cùng parse result, relative path, downloader invocation và error/skip collection như baseline đã fixture hóa.
- **Thứ tự bắt buộc**: Phase 01 safety net/refactor seam phải hoàn tất trước khi Phase 02 edX tích hợp vào workflow chung.
- **Decision date/approver**: đề xuất 2026-09-27; chờ người dùng duyệt phase packet trước khi tạo branch/code.
