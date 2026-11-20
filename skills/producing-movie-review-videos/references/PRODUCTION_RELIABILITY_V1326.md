# REVIEW_PHIM v1.3.26 — vận hành và khôi phục

Áp dụng khi gói mới được duyệt `execution_mode=PRODUCTION_FIRST_V1325`.
Tên mode/module v1325 được giữ để tương thích; không tự sửa checkpoint Legacy.
Production First → User Review → Targeted Revision. Không dùng Q01–Q15.

## Gói được duyệt

Gói `work-package.v2` chứa WORK_PACKAGE_ID, deviceId, JOB_DIR tuyệt đối,
SOURCE_MOVIE, SHA-256 nguồn thật, allowed_stages/task_ids theo thứ tự P00–G15,
G11A/G11B, allowed_read_roots, allowed_write_roots, stage_outputs không trùng,
allowed_executables_and_models, install_budget, repair_budget, human_gates,
creative_delegations. `ffprobe`/`ffmpeg` hoặc đường dẫn executable chính xác phải
có trong danh sách được duyệt khi kiểm MP4. Thiếu công cụ/quyền không tự cài.
Plan hash bao gồm mọi cấu hình và đường dẫn. Khi cần phụ thuộc ngoài nguồn phim,
khai báo `stage_inputs: {stage: {absolute_path: sha256}}`, `production_config`
và `stage_config` để không tái dùng đầu ra từ cấu hình khác.

Mỗi `stage_outputs[stage]` là danh sách file bắt buộc. G15 phải có MP4 cuối và
các sidecar trong phạm vi (metadata, thumbnail, EDL…). Runner kiểm bytes thật,
không rỗng, đường dẫn/hash; mọi MP4 phải qua FFprobe container/video/duration
và FFmpeg giải mã toàn bộ video/audio. Không kiểm nội dung, mỹ thuật hay giọng.
Không tin `technical_ready`, `lock_verified` hay boolean thumbnail từ executor.

`repair_budget` dùng `per_issue` tối đa 2, `total` tối đa 4, `allowed_kinds`
liệt kê chính xác loại được phép: `transient`, `connection`, `missing_output`,
`invalid_media`, `executor`. `permission` luôn dừng để host giải quyết quyền thật.
Ngân sách tính theo stage, không đổi tên lỗi để reset bộ đếm.

Host xác thực tin nhắn duyệt rồi gọi `one_approval_dispatch_v1321.approve_and_start`.
Hàm tạo khóa độc quyền ở `JOB_DIR/logs/work_package.lock`; owner, package/device,
plan_hash phải khớp file thật trước mọi thao tác ghi hoặc resume. Không xóa/cướp
khóa của tiến trình khác. Khóa cũ còn tồn tại: kiểm tiến trình và xin chủ khóa
release qua `release_lock`; không tự takeover. Khóa bị mất: chỉ host có quyền
khôi phục dùng `recover_missing_lock` sau khi kiểm thực tế không còn writer,
có recovery_ref; tạo độc quyền vẫn thất bại nếu một phiên khác đã tạo khóa.

## Chạy bằng host hoặc CLI

Python không tự gọi công cụ nội bộ ChatGPT. Host cung cấp callback executor thật
cho `run_until_hinge(plan,state,executor,session_owner=owner,persist=True)`.
Callback chạy đồng bộ trong phạm vi được duyệt; `DONE`/`WARNING` phải trả outputs
gồm relative_path/sha256. Runner kiểm bằng chứng, ghi ledger rồi tiếp tục.
Không có worker thật thì không có chạy nền giữa các lượt chat.

Với host gọi công cụ từng bước, các lệnh dưới đây đều cần
`--plan <approved_plan.json> --owner <authenticated-session-owner>`:

| Lệnh | Cách sử dụng |
|---|---|
| `init --approved-state <running.json>` | Khởi tạo duy nhất một lần từ trạng thái đã xác thực và khóa thật. |
| `next` | Lấy task tiếp theo hoặc ghi WAITING_USER khi proposal đã có. |
| `start` | Ghi intent trước khi host thực thi task; ngăn dispatch trùng sau mất phiên. |
| `record --result <result.json>` | Nộp kết quả task thật, bắt buộc task_id và plan_hash khớp; kiểm outputs/MP4. |
| `retry` | FAILED → RUNNING trong ngân sách và loại lỗi được duyệt. Sau đó host thực thi task. |
| `recover --evidence <inspection.json>` | Đối chiếu worker đã dừng sau mất phiên; ghi FAILED loại connection, sau đó retry. |
| `resume --action <wait_reason> --user-ref <message> --evidence <evidence.json>` | Tiếp tục đúng gói sau hành động người dùng thật. |
| `import --result <records.json> --evidence <expected_inputs.json>` | Nhập DONE có schema/provenance và file thật khớp, không sửa bản ghi gốc. |
| `review --action ACCEPTED --user-ref <message> --notes <feedback>` | Chốt đúng version/hash đã bàn giao và ghi ledger. |
| `review --action REVISION_REQUESTED --targets G14 --user-ref <message> --notes <feedback>` | Khoanh vùng stage/file bị ảnh hưởng, giữ bản cũ. |
| `revision-plan` | In JSON đề xuất revision cụ thể để người dùng duyệt. Host lưu vào file trong scope. |
| `revision-start --previous-plan <old.json> --approved-state <new-running.json>` | Dùng plan mới, khóa mới cùng JOB_DIR; tái dùng các stage không đổi. |

Ví dụ lệnh trên máy đã duyệt:

```powershell
python tools/project_flow_cli_v1325.py next --plan D:\REVIEW_JOB\approved_plan.json --owner session-A
python tools/project_flow_cli_v1325.py start --plan D:\REVIEW_JOB\approved_plan.json --owner session-A
# Host gọi đúng công cụ thực thi task và lưu result.json trong JOB_DIR.
python tools/project_flow_cli_v1325.py record --plan D:\REVIEW_JOB\approved_plan.json --owner session-A --result D:\REVIEW_JOB\result.json
```

Inspection cho `recover` là record do host kiểm tiến trình thật cung cấp:
source=`host_process_inspection`, inspection_ref, plan_hash, owner, task_id,
active=false. Không suy đoán worker đã dừng chỉ từ thời gian chờ. Nếu worker đã
hoàn thành và còn output, dùng `record` cho task đang inflight để khỏi chạy lại.
Callback API tương ứng: `recover_interrupted(...,verify_inactive=host_inspector)`.

## Chờ sáng tạo và thumbnail

G05_SCRIPT/G07_VOICE/G10_PILOT/G11A_METADATA/G11B_THUMBNAIL được xét **sau** khi
proposal tồn tại. Có creative_delegations hợp lệ thì tiếp tục. Không có quyền
thì WAITING_USER trước khi dùng kết quả; resume giữ nguyên proposal DONE.
G07 trong gói không ủy quyền bắt buộc khai báo `stage_proposals.G07` là danh sách
file giọng mẫu, tách khỏi `stage_outputs.G07` của WAV toàn phần. `next` trả
phase=proposal: executor chỉ tạo mẫu và trả PROPOSAL_READY + outputs. Runner
lưu mẫu rồi WAITING_USER/G07_VOICE. Resume sau duyệt trả phase=execute cho
cùng task G07, dùng mẫu đã lưu để làm TTS toàn phần; không tạo lại mẫu.
Các stage sáng tạo khác cũng hỗ trợ stage_proposals nếu proposal cần tách
khỏi đầu ra cuối. Không tạo task hoặc phê duyệt vi mô mới.

G11B trả WAITING_USER/USER_IMAGE_PLACEMENT cùng generation_ref và
thumbnail_sha256 nếu có hash ảnh tạo. ChatGPT cung cấp ảnh thật để tải và một
đích Windows tuyệt đối trong JOB_DIR, ví dụ `D:\REVIEW_JOB\assets\youtube_thumbnail.png`.
Người dùng tự chép đúng PNG/JPG. Không tự truyền và không gọi tạo ảnh lại.
Evidence resume chứa title, image_name, image_sha256, relative_path tùy chọn,
approval với source=user_message, action=G11B_THUMBNAIL, approval_ref,
title_sha256, user_confirmed_placement=true, user_selected_file.
Runner gọi verify_drop lại trên file thật; không nhận riêng status=FILE_ACCEPTED.
Cùng một xác nhận chép+duyệt giải quyết cả cổng ảnh và thao tác thủ công.
Runner ghi DONE G11B từ evidence rồi G12 dùng đúng relative_path/hash đó.

## Trạng thái và ledger

Task: PENDING, RUNNING, DONE, WARNING, FAILED, WAITING_USER. Package: PACKAGE_DONE
khi hết phạm vi chưa có G15. Project: FINAL_REVIEW (project_status=PROJECT_FINAL_REVIEW),
ACCEPTED, REVISION_REQUESTED. PACKAGE_DONE không phải nghiệm thu phim.
work_package_state và workflow_integrity route Production First về project_flow;
không dùng transition PACKAGE_PASS/QC cũ cho chế độ này.

`logs/project_flow_v1325.jsonl` là ledger append-only có sequence, hash chain,
timestamp, event và state đầy đủ. Ghi ledger/fsync trước snapshot JSON atomic.
Snapshot bị mất/lỗi sau khi event đã ghi: read_checkpoint khôi phục từ ledger.
Ledger bị cắt giữa một record hoặc đổi hash: chặn, không tự truncate/sửa lịch sử.
TASK_STARTED còn inflight sau ngắt phiên phải được host kiểm worker/output trước
record hoặc recover; không âm thầm chạy lại. Không tự nâng checkpoint Legacy
thiếu schema/provenance thành DONE. Gói mới dùng ledger mới hoặc revision chuẩn.

## Revision

`propose_revision` tạo WORK_PACKAGE_ID/version mới và các đường dẫn
`revisions/rN/...` cho stage bị ảnh hưởng; không ghi đè output cũ. Mặc định mọi
stage sau target là phụ thuộc để tránh dùng kết quả lỗi thời. Gói có
`stage_dependencies` đã duyệt có thể mô tả đồ thị cụ thể để bỏ qua phần không
liên quan; chỉ cho cạnh trỏ về stage trước. G14 chỉ kéo G14/G15, không khởi động
lại P00. G11A có thể kéo thumbnail/intro/final mà giữ render G11.

Sau khi người dùng duyệt plan revision cụ thể, host dừng writer, release khóa
cũ do chính owner sở hữu và approve_and_start gói mới. `begin_revision` kiểm
plan đúng đề xuất, nhập phần DONE không ảnh hưởng, giữ previous_deliveries.
Kết quả dựng mới phải giải mã được trước FINAL_REVIEW; không tạo vòng QC mới.

## Giới hạn nghiệm thu

Test v1.3.26 kiểm điều phối P00–G15 bằng callback tại máy và video MP4 thực có
thể giải mã, retry/resume/khóa/hash/tái dùng/thumbnail/revision. Fixture các
stage nghiệp vụ không chứng minh đã chạy ASR/TTS/ImageGen/MCP hoặc làm review
một phim thật. Nghiệm thu nội dung thành phẩm luôn thuộc người dùng.
