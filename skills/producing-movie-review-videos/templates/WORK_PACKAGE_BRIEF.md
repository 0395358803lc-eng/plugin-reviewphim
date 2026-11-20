# WORK_PACKAGE_BRIEF — REVIEW_PHIM v1.3.12

**Đề xuất một gói có quyền hữu hạn.** Nếu chưa có JOB_DIR, phê duyệt và QC scaffold trước hết được ghi trong chat; không bịa path/log.

| Trường | Nội dung điền từ bằng chứng thật |
|---|---|
| `WORK_PACKAGE_ID`, `schema_version` | `<ID>`, `work-package.v2` |
| `deviceId` / `FILM_DIR` / `SOURCE_MOVIE` | đường dẫn thực; nguồn phim readonly |
| `JOB_DIR` / `LOGO_DIR` | JOB_DIR chỉ ghi sau scaffold đã duyệt; logo hoặc không logo |
| `source_hash` | SHA-256 thực; P00 read-only chưa đo ghi UNKNOWN |
| `allowed_stages` | các stage hợp lệ, không tự gộp qua human gate |
| `task_ids` / `bounded_batches` | task cụ thể; `{stem,start,end}` có trần; không wildcard/TBD |
| `allowed_read_roots` / `allowed_write_roots` | root canonical, writable chỉ trong JOB_DIR |
| `allowed_executables_and_models` | phiên bản/checksum/backend đã kiểm chứng |
| `install_budget` | ID, source, version, SHA-256, bytes, target, license, network; unknown không cho phép cài |
| `repair_budget` | `per_issue=0,total=0` mặc định; tối đa 2/issue, 4/gói nếu duyệt |
| `expected_outputs` / `acceptance_criteria` | file/hashes/coverage/QC 2–6 tiêu chí mỗi task |
| `human_gates` / `stop_conditions` | G05_SCRIPT/G07_VOICE/G10_PILOT/G15_DELETE theo phạm vi |
| `plan_hash` | SHA-256 canonical JSON (không hash trường plan_hash) |
| `approval_ref` | chỉ có sau tin nhắn phê duyệt thật của user |

**Phê duyệt gói:** nút thật `GenUI.issueNewTurn` với `WORK_PACKAGE_ID`, `deviceId`, `JOB_DIR`, `plan_hash`, mô tả scope. Người dùng không phê duyệt phỏng đoán hoặc ngân sách UNKNOWN.

**P00:** báo đủ 11 ID `A01–A08/O01–O03` với `REUSE_READY/FOUND_NOT_VERIFIED/INCOMPATIBLE/MISSING/BLOCKED`. Có thể duyệt nhóm tên ID chính xác; GPU.PLAN và quyền cài GPU.RUNTIME chỉ được gộp nếu đủ thông số và được người dùng chấp nhận tường minh. Không chạy G01 từ P00 nếu chưa được duyệt G01.

**Human gate:** nếu package tạo bản script, voice hoặc pilot để xin quyết định, báo `WAITING_FOR_HUMAN_APPROVAL`; chỉ chạy các task phụ thuộc sau khi user đã duyệt. G09 pilot preview trước G10; G11 full render sau G10.
