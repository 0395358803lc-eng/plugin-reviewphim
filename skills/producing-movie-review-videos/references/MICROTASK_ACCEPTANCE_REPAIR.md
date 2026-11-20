# MICROTASK_ACCEPTANCE_REPAIR — QC từng microtask, báo cáo gói, sửa có giới hạn

**ĐỌC `WORKFLOW_CONSISTENCY_V1312.md` TRƯỚC.** **Thay thế quy tắc xin duyệt sửa từng issue nhỏ của bản cũ:** đọc SMART_BATCH_APPROVAL.md trước. **QC từng microtask** là bắt buộc; **QC tổng hợp của gói** là báo cáo ưu tiên cho người dùng. Mọi TASK_ID P00/G01–G15 có `acceptance_criteria` đo được (2–6 tiêu chí), `criterion_id`, `expected`, `actual`, `test_method`, `required_evidence`, `evidence_refs`, `blocking=true/false`, kết quả `PASS/FAIL/NOT_VERIFIED/BLOCKED`. Không lấy log `exit=0` hay có file làm bằng chứng chất lượng nội dung.

## Trước khi thực hiện

Khi trình `WORK_PACKAGE_ID`, đưa phạm vi, machine `deviceId`, `FILM_DIR`, `JOB_DIR`, nguồn/đầu ra, `plan_hash`, task IDs/pattern, quyền ghi, giới hạn batch và phương thức QC. Không cần trình xin duyệt từng Mnn/Bxxx đã nằm rõ trong gói được user đồng ý. Trước khi chạy từng task kiểm tra approval_ref của **gói** còn hiệu lực cho task đó.

## Sau từng task

- Kiểm output thật, canonical JOB_DIR, sha256/bytes, input_hashes, output_hashes, source_hash, đủ segment_id/scene_id/beat_id, không trùng/mất lô, continuity/narrative/technical QC khi phù hợp.
- Ghi `qc/microtasks/<safe_TASK_ID>/acceptance.v<attempt>.json` và `.md` trong JOB_DIR khi có quyền; không ghi đè bản cũ. Trường: `schema_version`, `TASK_ID`, `WORK_PACKAGE_ID`, `device_id`, `film_dir`, `job_dir`, `attempt`, `approved_scope`, `approval_ref`, `acceptance_criteria`, `checks_passed`, `checks_total`, `QC_STATUS`, `issues`, `next_action`, `report_sha256`, `report_time`.
- Cập nhật `logs/microtask_state.json`, `logs/microtask_ledger.jsonl` append-only, snapshot atomic. Mỗi batch chỉ COMPLETE sau QC PASS thật. `PASS` → **tự làm task kế trong cùng gói** khi còn thời gian và đúng dependency; **không** xin phê duyệt từng task PASS.
- Trạng thái chuẩn: `PASS`, `NEEDS_FIX`, `NOT_VERIFIED`, `BLOCKED`, `PARTIAL`, `WAITING_FOR_JOB`, `WAITING_FOR_AUDIO_UPLOAD`, `WAITING_FOR_HUMAN_APPROVAL`. Không đánh đồng chưa có human approval với lỗi QC: nội bộ có thể PASS nhưng package còn chờ `G05_SCRIPT/G07_VOICE/G10_PILOT`. Không biến thiếu audio/clip ChatGPT thành PASS. G04/G08 cần ảnh/clip thực, G03 dịch trực tiếp, G14 technical/story/visual QC độc lập.

## NEEDS_FIX và repair budget

Mỗi lỗi ghi `issue_id`, `severity=BLOCKING/MAJOR/MINOR`, `failed_criteria`, `expected`, `actual`, `evidence_refs`, `suggested_fix`, `verification_plan`, `status=OPEN`.

**Tự sửa nội bộ** khi (a) đã được khai rõ trong `repair_budget` của gói và người dùng duyệt; (b) thao tác cục bộ có thể đảo ngược, chỉ ghi JOB_DIR, không ảnh hưởng phim/logo gốc, workspace cũ hay sản phẩm đã duyệt; (c) dữ kiện đầu vào có thật; (d) tối đa 2 lần/`issue_id` **và không vượt tổng `repair_budget.total` của gói (tối đa 4, mặc định 0)**. `issue_id` mới không được dùng để né trần sửa. Lưu snapshot trước sửa, `repair_plan_hash`, `repaired_issue_ids`, `repair_approval_ref=package approval`, hành động sửa và `recheck` cả lỗi lẫn các tiêu chí đã PASS có nguy cơ hồi quy. Không xin phê duyệt lại các sửa chữa nhỏ nằm trong scope.

**Phải dừng** tại `NEEDS_FIX/BLOCKED` và trình phê duyệt **gói sửa riêng** nếu thao tác **ngoài phạm vi**, vượt 2 lần, không đảo ngược, phải **không tải/cài** mới khi chưa có quyền, thay model/backend, GPU.PLAN, truy cập root khác, sửa/ghi đè nguồn, phải **không xóa** G15 khi chưa có phép, thay đổi nội dung kịch bản/giọng/pilot đã được người dùng duyệt. Không tự bỏ gate hoặc bịa bằng chứng. Khi thiếu audio/video, ghi `NOT_VERIFIED` hoặc `WAITING_FOR_AUDIO_UPLOAD` và yêu cầu người dùng upload thật, không coi đó là lỗi kỹ thuật cần sửa.

## Nghiệm thu gói

`PACKAGE_PASS` chỉ khi mọi TASK_ID bắt buộc PASS, coverage đủ, Qxx và gate người dùng đã đáp ứng. Chỉ báo một `QC tổng hợp của gói`: bao nhiêu task/batch đạt, output+hash, thay đổi/sửa chữa, cảnh báo, các tiêu chí chưa chứng minh. QC nội bộ tồn tại để truy xuất nhưng không nhân số nút phê duyệt. Chưa hoàn tất thì báo trạng thái thực `PARTIAL/WAITING_FOR_HUMAN_APPROVAL/WAITING_FOR_AUDIO_UPLOAD/WAITING_FOR_JOB/BLOCKED` và nút phù hợp; chỉ khi user chủ động resume và quyền còn hiệu lực mới dùng nút **Tiếp tục gói** theo SMART_BATCH_APPROVAL.md; không phê duyệt lại các task đã nằm trong scope.

Ngăn task khác ngoài package scope, không tự chạy nền. G05 duyệt kịch bản, G07 giọng và G10 pilot là quyết định của người dùng; G15 xóa riêng. Chỉ xác nhận ChatGPT đã nghe khi user thực sự upload audio và ChatGPT nghe/đối chiếu được.
