## Chọn chế độ trước khi đọc

**PRODUCTION_FIRST_V1325 đã được duyệt:** dùng
[PRODUCTION_FIRST_AUTONOMOUS_V1325](PRODUCTION_FIRST_AUTONOMOUS_V1325.md) và
[PRODUCTION_RELIABILITY_V1326](PRODUCTION_RELIABILITY_V1326.md).
Không dùng QC/PASS, duyệt từng scene/beat/WAV/shot/batch, web crosscheck hay ba trục
G14 dưới đây để chặn tiến độ. Chỉ kiểm file thực dùng được, hash, lỗi chương trình
và quyền thao tác. Không ghi đè bản cũ; xóa cần phê duyệt xóa riêng.
Các chi tiết kỹ thuật sản xuất vẫn có thể tham khảo, nhưng điều phối và nghiệm thu
tuân theo chính sách Production First. Không tự suy diễn ủy quyền sáng tạo.

## Nhánh Legacy — quy tắc dưới đây chỉ điều phối gói chế độ cũ

<details>
<summary>Hướng dẫn lịch sử; không áp cho Production First</summary>

# SESSION_ORCHESTRATION — REVIEW_PHIM v1.3.12: package state và resume

**QUY TẮC ƯU TIÊN:** `WORKFLOW_CONSISTENCY_V1312.md` về P00/G01–G15, state, human gates và chống trùng; `SMART_BATCH_APPROVAL.md` về quyền gói; `MICROTASK_ACCEPTANCE_REPAIR.md` về QC; `GPU_FIRST_APPROVAL.md` GPU-FIRST; `WORKSPACE_REUSE_POLICY.md` reuse an toàn. `WORK_PACKAGE_ID` được người dùng duyệt, microtask là đơn vị nội bộ. Không tự phê duyệt.

## P00 — thứ tự chuẩn (không bỏ quyền)

1. **Chọn máy:** gọi `mcp__Remote_Desktop_Commander__list_devices`, xác minh `deviceId`. 2. **Chọn phim:** `FILM_DIR`, kiểm file `SOURCE_MOVIE` read-only, nhiều phim hỏi chọn. 3. **Logo:** chọn `LOGO_DIR` hoặc không logo; không tự dùng logo TUA PHIM CÓ GU. 4. **Scaffold:** trình một gói tạo thư mục `JOB_DIR=FILM_DIR\REVIEW_PHIM_WORKSPACE\<safe-project-id>` và chỉ tạo sau phê duyệt. Trước JOB_DIR, QC/phê duyệt ghi trong chat; sau khi có quyền ghi mới lưu ledger. 5. **Kiểm tra phần cứng** và workspace reuse read-only: CPU/RAM/GPU/VRAM/OS/disk, root cùng deviceId đã được duyệt, không thực thi/smoke trước quyền riêng. 6. **Trình danh sách cài đặt** đủ 11 ID `A01–A08/O01–O03` với nguồn/version/hash/ABI/VRAM/giấy phép/budget, tối ưu GPU; gộp nhóm verify/reuse/install **đã có thông số cố định và được duyệt rõ**; không tự điền UNKNOWN rồi cài. GPU.PLAN chỉ nghiên cứu, GPU.RUNTIME cần quyền cài thực. Không tự chạy G01.

## Vào/tiếp tục phiên

- Kiểm `approval_ref` là tin nhắn người dùng thật, `WORK_PACKAGE_ID`, `schema_version`, canonical `plan_hash`, source_hash, `deviceId`, `JOB_DIR`, read/write roots, `task_ids`/`bounded_batches` hữu hạn và mọi human gate. `WORK_PACKAGE_ID` không được tự mở rộng bằng một approval cũ của Mnn/Bxxx.
- Kiểm `logs/work_package_state.json`, `logs/work_package_ledger.jsonl`, `logs/microtask_state.json`, `logs/microtask_ledger.jsonl`, các QC reports; nếu phiên cũ chưa có work_package_state, **legacy inventory** read-only, không coi microtask PASS là phê duyệt package mới. Không sửa/migrate làm mất log cũ.
- Trước RUNNING, lock file `logs/work_package.lock` bằng atomic exclusive create và owner_run_id; có lock khác → `BLOCKED`, không auto-steal/kill. Mỗi task có idempotency event ID (`plan_hash`, `task_id`, input hash, attempt); QC PASS và output hash khớp thì skip, không chạy lại.
- Trong một lượt chat có thể làm nhiều Mnn/Bxxx đã được duyệt, QC và checkpoint từng task. Nếu chưa đủ thì `PARTIAL` + nút **Tiếp tục gói** qua `GenUI.issueNewTurn`; lượt mới không cần phê duyệt lại *cùng phạm vi* nhưng phải so hash, lock, gate và quyền. Không tự chạy nền hoặc tự gửi lượt mới.

## Human gates, QC và chờ thật

- G04 cần `FILM_UNDERSTANDING_READY` mới đề xuất G05; G05 đòi `G05_SCRIPT` người dùng duyệt trước G06; G07 đòi `G07_VOICE` trước TTS hàng loạt; G08 `SHOT_SELECTION_READY` trước G09; G09 chỉ EDL/preview; G10 có pilot và `G10_PILOT` người dùng duyệt trước full render G11.
- Chờ quyết định thật: `WAITING_FOR_HUMAN_APPROVAL`; chờ audio user upload `WAITING_FOR_AUDIO_UPLOAD`; chờ process local `WAITING_FOR_JOB`; mất kết nối/source hash/approval mismatch `BLOCKED`; thiếu bằng chứng `NOT_VERIFIED`. G14 technical/story/visual QC riêng; không PASS khi chưa thực sự xem/nghe. G15 bàn giao (`DELIVERY_PASS`) có thể PASS dù `DELETE_NOT_REQUESTED`; xóa cần G15_DELETE riêng theo path và QC hậu xóa.
- G05 vẫn cần phê duyệt riêng từ người dùng cho kịch bản hoàn chỉnh; nếu G04 chưa đạt FILM_UNDERSTANDING_READY thì không đề xuất chạy G05. G15 file deletion không tự thuộc package delivery.

## Ranh giới dữ liệu

`JOB_DIR` là root DUY NHẤT để ghi output/cache/temp/log; phim gốc, logo và workspace reuse chỉ đọc. Dùng binary đã được duyệt qua đường dẫn tuyệt đối; `cwd`, TEMP/TMP, HF_HOME, HUGGINGFACE_HUB_CACHE, XDG_CACHE_HOME, TORCH_HOME, PIP_CACHE_DIR, PYTHONPYCACHEPREFIX, npm_config_cache, COREPACK_HOME, PLAYWRIGHT_BROWSERS_PATH đều trỏ JOB_DIR. Không quét PATH/ổ C: global, không tải/cài/đổi backend/driver/OS/PATH/mở port khi thiếu phép. Lỗi hoặc chưa đo phải báo UNKNOWN/NOT_VERIFIED/BLOCKED, không tuyên bố hoàn tất.

## Báo cáo

Chỉ kết luận `PACKAGE_PASS` khi toàn bộ microtask/QA và human gate PASS. Một bảng **QC tổng hợp của gói**: `WORK_PACKAGE_ID | n/N đã QC PASS | pending/human gate | output + hashes | repair_count | status | quyết định cần người dùng`. Không trình 30 nút B001–B030. Chỉ một nút cho **Phê duyệt gói**, **Tiếp tục gói**, hoặc quyết định human gate thực; nếu cần mở scope phải trình package plan mới.

</details>
