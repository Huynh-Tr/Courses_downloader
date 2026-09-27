# Sứ mệnh & Giá trị dự án

> Đây là Constitution cho dự án Brownfield. Các phase chỉ được thay đổi hành vi khi hợp đồng phase nêu rõ và được duyệt.

## 1. Vấn đề, người dùng & giá trị

- **Người dùng chính**: người học đã đăng ký hợp lệ trên Coursera hoặc edX.org và muốn dùng tài liệu được tài khoản của họ cấp quyền để học ngoại tuyến.
- **Người dùng phụ**: maintainer cần mở rộng downloader mà không làm hỏng CLI, GUI, Python API, cấu trúc thư mục và khả năng resume hiện có.
- **Vấn đề hiện tại**: codebase có 16 module Python phẳng, 7.247 dòng, chưa có test tự động; logic Coursera, xác thực, CLI/GUI và workflow tải xuống liên kết chặt. Mở rộng trực tiếp sang nền tảng khác có nguy cơ nhân đôi code và gây regression.
- **Giá trị đề xuất**:
  1. xây safety net có thể chạy lặp lại để rút gọn/tối ưu từng seam nội bộ mà vẫn bảo toàn hợp đồng Coursera;
  2. tạo ranh giới provider đủ nhỏ để hỗ trợ tải video, phụ đề và tệp đính kèm từ một khóa học edX.org mà người dùng đã được cấp quyền.
- **Non-goals cấp dự án**:
  - không vượt paywall, enrollment, DRM, access control, CAPTCHA, anti-bot hoặc giới hạn nội dung của nền tảng;
  - không tải/thu thập đáp án, điểm, bài nộp, dữ liệu người học khác hoặc nội dung không được tài khoản hiện tại truy cập;
  - không phân phối lại nội dung khóa học, không hỗ trợ mass scraping hoặc tải hàng loạt nhiều tài khoản;
  - không viết lại toàn bộ ứng dụng trong một phase và không lấy số dòng code làm mục tiêu thay cho độ rõ ràng/khả năng kiểm chứng.

## 2. Tiêu chí thành công có thể quan sát

- **Tương thích Coursera**: toàn bộ contract được liệt kê trong `brownfield-notes.md` có characterization test; tất cả test đó vẫn pass sau mỗi refactor.
- **Rút gọn có kiểm soát**: mỗi lát cắt refactor phải loại bỏ ít nhất một duplication, global side effect, unused abstraction hoặc provider-specific coupling đã được chỉ rõ, nhưng không thay đổi CLI flags/defaults, Python API, cây thư mục/tên file, skip/overwrite/resume, parallelism hoặc thông báo/lỗi đã được bảo vệ.
- **Outcome edX MVP**: với một URL `learning.edx.org` hợp lệ và phiên trình duyệt đã đăng nhập, CLI tải được các video không DRM có URL tải trực tiếp, subtitle track và downloadable attachment, giữ thứ tự/hierarchy khóa học; chạy lại không phá file hoàn chỉnh.
- **Chất lượng/độ tin cậy**: unit/characterization tests không gọi mạng; fixture không chứa cookie/token/dữ liệu cá nhân; lỗi một resource được báo cáo rõ và không làm hỏng resource đã hoàn tất.
- **Vận hành/hiệu năng**: Coursera giữ nguyên `--jobs`, timeout/retry, resume và skip semantics hiện có; edX dùng concurrency có giới hạn và không tạo request ngoài nhu cầu duyệt outline/resource của một khóa học.
- **Nguồn bằng chứng**: lệnh và exit code trong từng `validation.md`, fixture tests, diff review, và walkthrough opt-in trên tài khoản/khóa học do người dùng sở hữu quyền truy cập.

## 3. Nguyên tắc sản phẩm & kỹ thuật

- Safety-net trước refactor; một Task Group mỗi lượt; dừng tại decision gate.
- Ưu tiên reuse workflow tải xuống chung thay vì sao chép một downloader riêng cho từng provider.
- Tách transport/CLI, provider discovery/authentication và file-transfer workflow; provider không tự ý ghi file ngoài output root.
- Không đổi hành vi Coursera để “làm sạch” code nếu chưa có requirement và approval riêng cho breaking change.
- Dùng fixture đã loại bỏ dữ liệu nhạy cảm để khóa schema; live network chỉ là walkthrough có chủ đích, không phải unit test.
- Một resource chỉ được tải khi tài khoản hiện tại được phép truy cập và nền tảng cung cấp URL tải hợp lệ; unsupported/DRM content phải được skip minh bạch.
- Quyết định chưa chắc chắn được ghi thành risk/open question, không bị che trong code hoặc fallback im lặng.

## 4. Baseline an toàn, bảo mật & riêng tư

- **Dữ liệu nhạy cảm**: Coursera `CAUTH`; cookie/session/CSRF của edX.org; browser profile; URL ký tạm thời; đường dẫn local; nội dung khóa học có bản quyền. Không ghi các giá trị này vào Git, fixture, log, exception text hoặc audit log.
- **Trust boundaries**: trình duyệt người dùng → cookie importer → `requests.Session` theo provider → API/LMS/CDN của provider → downloader → filesystem local. Redirect/CDN URL vẫn là input bên ngoài và phải được xác thực scheme/host trước khi tải.
- **Kiểm soát tối thiểu**:
  - chỉ HTTPS (trừ fixture test local không có network), giữ certificate verification;
  - session riêng theo provider; không gửi cookie edX sang Coursera hoặc host CDN không cần cookie;
  - không nhận/lưu password edX; không log cookie/token; cookie chỉ sống trong memory cho lần chạy MVP;
  - từ chối localhost, loopback, private/link-local address và scheme không an toàn khi xử lý resource URL;
  - tôn trọng HTTP 401/403/404/429, redirect policy và retry có giới hạn; không thử né chặn;
  - chỉ tải nội dung người dùng đã đăng ký và chỉ dùng cá nhân theo điều khoản nền tảng.
- **Phục hồi**: mọi phase code phải rollback được bằng cách quay lại commit/branch trước phase; không có migration dữ liệu. File tải dở không được coi là hoàn tất; chạy lại phải có đường resume/overwrite rõ ràng.
