# WORK_PACKAGE_FINAL — REVIEW_PHIM v1.3.12

## Thông tin phiên và quyền

- `WORK_PACKAGE_ID` / `plan_hash` / `approval_ref` / `deviceId` / `JOB_DIR` / source hash: `[đã đối chiếu]`.
- Scope (stages, task IDs, bounded batch ranges) và trạng thái mỗi task: `[n/N]`.
- Mô tả quyền network/reuse/install/backend/read/write, chứng cứ GPU-FIRST: `[mốc/hash]`.
- Human gate G05_SCRIPT/G07_VOICE/G10_PILOT: `[APPROVED / WAITING_FOR_HUMAN_APPROVAL / N/A]`.

## Nghiệm thu tổng hợp

| Nhóm | Bằng chứng và kết quả |
|---|---|
| Microtask QC | PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED + report hashes/lineage |
| Package QC | PACKAGE_PASS / PARTIAL / WAITING_FOR_JOB / WAITING_FOR_AUDIO_UPLOAD / WAITING_FOR_HUMAN_APPROVAL / BLOCKED |
| Video kỹ thuật G14 | `TECHNICAL_STATUS` PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED |
| Story QC G14 | `STORY_STATUS` PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED |
| Visual QC G14 | `VISUAL_EDITING_STATUS` PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED |
| File đầu ra | MP4/ZIP/manifest, byte, SHA-256, đường dẫn thực |
| Repair | số lần/issue, tổng sửa so với budget, evidence/recheck |
| Cần người dùng | phê duyệt script/voice/pilot, upload audio, hoặc scope mới |

**G15:** `DELIVERY_PASS` sau khi đủ MP4/ZIP/hash; `DELETE_NOT_REQUESTED/DELETE_DECLINED` hoàn toàn hợp lệ. Chỉ `G15_DELETE` độc lập với file list cụ thể mới cho xóa trong JOB_DIR, không đụng phim/logo gốc.

**Resume:** có `work_package_state.json`, `work_package_ledger.jsonl`, `microtask_ledger.jsonl`; lock quyền sở hữu rõ. Nếu PARTIAL, nút `Tiếp tục gói` chỉ khởi tạo lượt mới theo plan_hash cũ, không phải approval mới và không chạy nền.
