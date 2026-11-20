---
name: one-click-review-execution
description: Use alongside producing-movie-review-videos whenever REVIEW_PHIM plans, approves, resumes, or executes a work package; turns one approved plan into immediate scoped execution without a second deployment approval.
---

## Production First v1.3.27

Khi gói đã duyệt chọn `PRODUCTION_FIRST_V1325`, đọc
[chính sách chuẩn](../producing-movie-review-videos/references/PRODUCTION_FIRST_AUTONOMOUS_V1325.md)
và [khôi phục v1.3.26](../producing-movie-review-videos/references/PRODUCTION_RELIABILITY_V1326.md).
Dùng `project_flow_v1325.py`; không lấy QC=PASS, cổng duyệt hay vòng sửa lỗi
thẩm mỹ trong nhánh Legacy dưới đây làm điều kiện chuyển bước.
Chỉ dừng khi thiếu đầu ra dùng được, quyền hoặc đầu vào thiết yếu.

## Legacy — chỉ điều phối gói cũ

<details><summary>Quy tắc lịch sử</summary>



# REVIEW_PHIM v1.3.25 — ONE APPROVAL → PRODUCTION FIRST AUTO FLOW


**GÓI MỚI v1.3.25:** Nếu `execution_mode=PRODUCTION_FIRST_V1325` đã được user duyệt trong gói, sau `approve_and_start` gọi ngay executor cho task đầu theo `tools/project_flow_v1325.py::run_until_hinge` và `workflow_integrity_v1323.py` (mode route); không chạy vòng QC hay sinh phê duyệt từng stage. Có thể chạy tất cả stage đủ quyền trong cùng lượt; checkpoint cho resume. Dừng đúng `WAITING_USER` (quyền/hình người dùng copy), `FAILED` (không có output kỹ thuật), hoặc `FINAL_REVIEW` sau G15. **Không giả remote execution:** callback là hành động của ChatGPT với các công cụ được cấp quyền, không có chức năng tự gọi MCP từ Python. `G15_DELETE`, nguồn và cài mới vẫn cần quyền. Đọc [PRODUCTION_FIRST_AUTONOMOUS_V1325](../producing-movie-review-videos/references/PRODUCTION_FIRST_AUTONOMOUS_V1325.md). Các đoạn QC/gate bên dưới chỉ áp dụng gói legacy không chọn mode mới.

**BẮT BUỘC ÁP DỤNG** khi người dùng khởi động, phê duyệt hay tiếp tục `REVIEW_PHIM`. Quy tắc này có **ưu tiên cao hơn** mọi hướng dẫn cũ trong `WORKFLOW_CONSISTENCY_V1312.md`, `SMART_BATCH_APPROVAL.md`, `SESSION_ORCHESTRATION.md`, `MICROTASK_ORCHESTRATION.md` và `WORK_PACKAGE_BRIEF.md` **chỉ về việc tách “phê duyệt kế hoạch” / “cho phép triển khai” thành hai lần bấm**. Không làm thay đổi 15 giai đoạn, G11A/G11B, yêu cầu kiểm tra, QA, quyền truy cập hoặc các human gates.

Đọc và áp dụng cùng chính sách [ONE_APPROVAL_START_POLICY_V1321](../producing-movie-review-videos/references/ONE_APPROVAL_START_POLICY_V1321.md). Đây là đặc tả ưu tiên của quá trình duyệt gói. Không được kết luận chạy xong chỉ vì đã phê duyệt.

**CÁCH LÀM CHUẨN**

1. Thu thập thông tin đã có, kiểm tra read-only theo quyền, dựng **một** `WORK_PACKAGE_ID` đầy đủ với `plan_hash`, `task_ids` hữu hạn, máy, phim, `JOB_DIR`, read/write roots, công cụ, mức cài đặt/sửa chữa, output, QC, stop conditions. Không tạo giai đoạn “duyệt thiết kế” riêng trước gói triển khai; lập kế hoạch + phạm vi triển khai nằm chung một bản trình duyệt.
2. Hiện **một lời mời phê duyệt**: “**PHÊ DUYỆT VÀ CHẠY GÓI**”, kèm mục tiêu, đầu vào, các hành động sẽ chạy và ranh giới quyền. Tin nhắn phê duyệt phải vẫn mang `action=APPROVE_PACKAGE` để tương thích `work_package_state.py`, cùng `WORK_PACKAGE_ID`, `deviceId`, `JOB_DIR`, `plan_hash`, nguồn và scope đã trình. Đây là **một phê duyệt có chủ ý để thực thi ngay**, không phải phê duyệt chỉ để tiếp tục lập kế hoạch.
3. **Trong chính lượt chat nhận phê duyệt**, kiểm lại provenance/plan/source/device/path, acquire `work_package.lock` một lần và xử lý nội bộ `PROPOSED → APPROVED → RUNNING`; **sau đó gọi công cụ thực thi những task đã được duyệt ngay**. Không hỏi “Có triển khai không?”, không xin `START`, không đẩy sang một mục “lập kế hoạch triển khai” khác. Dùng `tools/one_approval_dispatch_v1321.py` để kiểm chứng state contract nếu được phép chạy Python trên máy.
4. Chạy liên tiếp tất cả các task đủ điều kiện trong scope, QC và checkpoint nội bộ. `QC=PASS` + hash khớp thì skip thay vì hỏi chạy lại; không tự lặp thao tác trong hai phiên. Chỉ tạm dừng khi có blocker thật hoặc **human gate cần quyết định**. Việc bấm “Tiếp tục gói” với cùng `plan_hash` chỉ kích hoạt resume, không yêu cầu phê duyệt lại.
5. Nếu cần cài/tải/đổi backend chưa có bản liệt kê đủ checksum/licensing/budget, chỉ trình gói phần việc đã có quyền; phần mới cần **gói với scope/budget rõ**, không tự nới quyền. P00 read-only chưa có phim SHA có thể dùng UNKNOWN chỉ theo quy định P00 hiện hành; không lấy UNKNOWN làm quyền chạy G01–G15.

**VẪN CẦN NGƯỜI DÙNG QUYẾT ĐỊNH**: `G05_SCRIPT`, `G07_VOICE`, `G10_PILOT`, `G11A_METADATA`, `G11B_THUMBNAIL`, `G15_DELETE` và mọi thay đổi source/permission/installation không nằm trong gói duyệt. Không gọi các human gates này là bước “duyệt triển khai” trùng lặp. Không có phê duyệt từ tin nhắn thật → không chạy. Không tự chạy nền giữa các lượt ChatGPT; công việc dài tiếp diễn chỉ nếu tiến trình remote đã được cấp phép và quản lý đúng trạng thái.

**KẾT LUẬN KHÔNG ĐƯỢC PHÉP**: không được tuyên bố “đã triển khai” chỉ từ `APPROVED` hay `RUNNING`; cần log, output, QC thật; đối với media phải thực sự xem/nghe như chính sách v1.3.20.

## G04/G05 fast track (v1.3.22)

Khi scope có G04/G05, bắt buộc đọc `skills/producing-movie-review-videos/references/G04_G05_FAST_TRACK_V1322.md`: package mới dùng đúng `G04.FILM.UNDERSTANDING.FULL`/`G05.REVIEW.FULL`, một Q04/Q05 tổng thể, không chia G04/G05 thành Mnn/Bxxx hoặc hỏi duyệt từng cảnh/đoạn. Cơ chế một phê duyệt chạy ngay vẫn giữ; không bỏ human gate `G05_SCRIPT` hay quyền media.

## Unified dispatch (v1.3.23)

Sau khi `approve_and_start` nhận `STARTED`, trước **mỗi** lệnh thực thi phải dùng `skills/producing-movie-review-videos/tools/workflow_integrity_v1323.py::decide_dispatch` với plan hiện hành, state đã xác minh, task_id và session_owner; nếu `allowed=false` không được chạy task đó. Quy tắc này không thêm một click duyệt, chỉ hợp nhất guard. Q11A/Q11B từ gói trước được reuse với evidence và phê duyệt có hash còn hợp lệ, không bắt buộc stage trước nằm cùng `task_ids`. Mỗi stage chỉ có một Q tổng thể, không giả nghe/xem nhờ log. Trước `PACKAGE_PASS` dùng `validate_package_completion` và core transition, không suy ngược quyền duyệt nội dung.

## G11B manual thumbnail (v1.3.24)

Bắt buộc đọc `skills/producing-movie-review-videos/references/MANUAL_THUMBNAIL_HANDOFF_V1324.md`. ChatGPT tạo ảnh, người dùng tải rồi đặt vào một đích `JOB_DIR/assets/youtube_thumbnail.png`/JPG đúng định dạng; xác nhận **“ĐÃ CHÉP ẢNH VÀ DUYỆT G11B”** được kiểm theo tin nhắn thật và file/hash thật. Đây là human gate chọn ảnh G11B_THUMBNAIL, không phải phê duyệt triển khai lần 2. Không transfer tự động, không mở package/approval phụ chỉ vì đang chờ file; giữ `WAITING_FOR_HUMAN_APPROVAL` và substatus `WAITING_FOR_USER_IMAGE_PLACEMENT` cho đến khi người dùng đặt ảnh. Q11B/G12 vẫn cần QC và guard v1.3.23.

</details>
