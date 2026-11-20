# REVIEW_PHIM v1.3.21 — ONE_APPROVAL_START_POLICY (lập kế hoạch + triển khai một nút)

> **v1.3.25 — PRODUCTION_FIRST_V1325:** Với gói mới đã duyệt mode này, ưu tiên [PRODUCTION_FIRST_AUTONOMOUS_V1325.md](PRODUCTION_FIRST_AUTONOMOUS_V1325.md). Các Qxx/QC thẩm mỹ, nghe/xem, web và phê duyệt sáng tạo giữa giai đoạn trong tài liệu dưới đây là **LEGACY-ONLY**; mode mới dùng DONE đầu ra kỹ thuật và chờ user nghiệm thu cuối. Giữ nguyên quyền thiết bị/source/install/delete và thao tác chép thumbnail thật.


## Mục tiêu và phạm vi ưu tiên

Thay hai lượt **(a) phê duyệt kế hoạch** và **(b) phê duyệt/ra lệnh triển khai cùng chính kế hoạch** bằng **một lần phê duyệt gói**. Các bước kỹ thuật `PROPOSED → APPROVED → RUNNING` vẫn tồn tại trong state machine để có dấu vết; `APPROVED → RUNNING` là **chuyển trạng thái nội bộ không cần thêm tin nhắn phê duyệt hay một nút START thứ hai**. Hướng dẫn này ghi đè ví dụ cũ bắt người dùng ấn thêm “triển khai”, nhưng **không** ghi đè hợp đồng quyền, xác minh, stop conditions, phê duyệt nội dung hay QC.

## 1. Kế hoạch và quyền triển khai nằm chung một gói

- Thực hiện preflight read-only theo quyền đã có, tái dùng evidence/hardware/runtime/checkpoints còn hợp lệ. Không chạy lại P00 đã PASS hoặc scan/đo lại toàn phim khi không cần; không yêu cầu người dùng chọn lại máy/phim/thư mục đã xác minh trong cùng phiên.
- Tạo ngay `work-package.v2` có `WORK_PACKAGE_ID`, `deviceId`, `JOB_DIR`, `SOURCE_MOVIE`, `source_hash`, `allowed_stages`, danh sách `task_ids`/`bounded_batches` hữu hạn, read/write roots, `allowed_executables_and_models`, danh mục `install_budget` định danh có version+sha+bytes+license hoặc rỗng, `repair_budget`, `expected_outputs`, `acceptance_criteria`, `stop_conditions`, `human_gates`, canonical `plan_hash`.
- Tối đa **một bản trình duyệt trước khi chạy phạm vi có thể xác định**: hiển thị hành động sẽ thực thi ngay, đường dẫn máy, gói, hash, ngân sách và điểm dừng cần người duyệt. Không trình bản nháp kế hoạch rồi xin một nút riêng cho triển khai cùng phạm vi.
- Label chính xác dễ hiểu: **“PHÊ DUYỆT VÀ CHẠY GÓI”**; payload tương thích `APPROVE_PACKAGE` và bao gồm plan hash thật. Không tự coi từ “đồng ý” không đủ tham chiếu là quyền mở rộng scope; đối chiếu user message thật.

## 2. Khi nhận phê duyệt — thực thi trong cùng lượt chat

1. Đọc tin nhắn phê duyệt thực tế, xác minh `WORK_PACKAGE_ID`, `deviceId`, `JOB_DIR`, canonical `plan_hash` và provenance; kiểm manifest, source SHA, đường dẫn canonical, thiết bị, approved read/write roots, tool/model, install/repair budget, các human gates liên quan.
2. Đảm bảo **atomic lock** `JOB_DIR/logs/work_package.lock` trước khi phát lệnh, không chiếm lock người khác; phát hiện `RUNNING` cùng gói thì báo đang chạy và resume/check tiến trình theo quyền, không gọi lại command tạo file/voice/render.
3. Chuyển `PROPOSED → APPROVED → RUNNING` **nội bộ**; gọi tool thực thi task đầu tiên ngay sau đó, không thêm một tin nhắn `APPROVE_EXECUTION` hoặc nút “BẮT ĐẦU TRIỂN KHAI”. Bộ kiểm chuẩn: `tools/one_approval_dispatch_v1321.py`, gọi logic `work_package_state.transition()` hai lần trong **một transaction** sau khi đã acquire lock. Nếu lỗi thì ghi trạng thái chính xác/khôi phục theo quyền, không giả PASS.
4. Tiếp tục task thứ hai/thứ ba... trong cùng gói khi hợp lệ, chạy QC và ghi ledger/hash; **không dừng chờ mỗi microtask, mỗi trang transcript hay mỗi pha "lập kế hoạch" nội bộ**. Không được vượt giới hạn thời gian/context hay giả rằng ChatGPT làm việc nền; lưu `PARTIAL` và user chủ động “Tiếp tục gói” khi cần.
5. Tham số gói bị đổi (phim/hash, thiết bị, root, scope, model, cài đặt, mục tiêu, budget) thì bắt buộc có plan hash mới + phê duyệt gói mới. Không đòi phê duyệt lại vì công cụ đã PASS, vì đã kiểm trước, vì chuyển state nội bộ, hay vì một bước phụ không đổi scope.

## 3. Các trường hợp không thể tự động bấm chạy

- Chưa có gói hợp lệ/plan hash, phê duyệt không phải người dùng thật, thao tác ghi chưa được cho phép, hash nguồn khác, lock bị chiếm, tool chưa cài, không còn ngân sách sửa, hoặc khác device/root → `BLOCKED/NOT_VERIFIED` và báo lý do; không tự cấp phép.
- Install/update/download, kết nối ra ngoài, chuyển file media, xóa/tác động dữ liệu ngoài `JOB_DIR` **chỉ khi đã nằm đúng scope đã duyệt**; thiếu thông số cài đặt đầy đủ thì xin gói riêng đúng tài nguyên, không gom quyền vô hạn.
- **Không tự chạy nền** qua lượt chat; chỉ tiếp tục job đã được phê duyệt hoặc khi người dùng chủ động khởi động lượt tiếp theo.
- Không tự bỏ cổng duyệt **nội dung**: `G05_SCRIPT` (script), `G07_VOICE`, `G10_PILOT`, `G11A_METADATA`, `G11B_THUMBNAIL`; `G15_DELETE` riêng theo danh sách path. Có thể trình những quyết định có đầu ra cùng lúc để giảm tương tác nếu chúng đã được tạo đúng quyền, nhưng không hợp thức hóa một quyết định chưa xuất hiện.
- Không tự qua G04/G08 khi chưa xem hình/clip thật; khi thiếu media dùng ZIP handoff v1.3.20 và chờ upload, không tự báo ĐẠT; G14 kiểm cả technical/story/visual.

## 4. Gói cũ và kiểm chứng

- Áp dụng **cho gói mới v1.3.21**. Với gói `APPROVED` cũ có phê duyệt hợp lệ cùng plan hash/scope, người dùng yêu cầu “triển khai” hoặc “tiếp tục” có thể vào `RUNNING` mà không phải phê duyệt lại chính kế hoạch; vẫn kiểm lock, metadata, phê duyệt, điều kiện từng giai đoạn.
- Không sửa/đánh PASS lại checkpoint dự án cũ, đặc biệt những đoạn `NOT_VERIFIED`; không ghi đè log, không tự chuyển job terminal hoặc hợp thức hóa quyền còn thiếu.
- Test bắt buộc: đúng một approval dẫn đến RUNNING; wrong hash/device/source/root bị chặn; hai click không chạy trùng; lock cạnh tranh bị chặn; không nhảy qua G05/G07/G10/G11A/G11B/G15_DELETE; resume vẫn cần nguồn/plan và điều kiện ngoại lai đã giải quyết.

## 5. Báo cáo gọn

Sau mỗi lượt **nói kết quả thật**, không xin “duyệt triển khai” lại. Mẫu: `WORK_PACKAGE_ID | Đã thực thi n/N | QC PASS | Bị chặn bởi ... | Bước tiếp theo`. Một câu ngắn về tác vụ đang chạy ở máy chỉ khi có process thật. Nút tiếp theo là “Tiếp tục cùng gói” (chủ động khi dở) hoặc quyết định nội dung thực, không phải “phê duyệt triển khai” lặp.
