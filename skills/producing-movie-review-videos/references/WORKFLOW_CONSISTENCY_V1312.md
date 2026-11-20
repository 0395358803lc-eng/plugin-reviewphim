# WORKFLOW_CONSISTENCY_V1312 — Hợp đồng điều phối thống nhất REVIEW_PHIM v1.3.12

**BẮT BUỘC ĐỌC ĐẦU TIÊN** trước P00 và mọi công đoạn G01–G15. Đây là hợp đồng hành vi hiện hành cho việc chọn máy, phê duyệt theo gói, trạng thái, rollback/recovery, thứ tự pilot/full render và nghiệm thu. `tools/work_package_state.py` là bộ **kiểm chứng thuần Python stdlib**, không phải daemon hay quyền chạy lệnh; không tự cài/chạy nếu môi trường người dùng chưa cho phép.

## 1. Thứ tự ưu tiên không mâu thuẫn

1. **Yêu cầu và giới hạn phê duyệt thực tế của người dùng**, ranh giới phim gốc/logo/workspace, quyền mạng/tải/cài/xóa, bảo vệ dữ liệu, GPU-FIRST, ChatGPT trực tiếp dịch và chỉ thực sự nghe/xem bằng chứng khi được hỗ trợ, G05/G07/G10 human approval và QC/Q01–Q15 là bất biến. Không tài liệu nào được phép nới lỏng.
2. `WORKFLOW_CONSISTENCY_V1312.md` quyết định **thứ tự công việc, phân loại human gates, state machine, khôi phục và cách hiểu xung đột**. `SMART_BATCH_APPROVAL.md` quyết định **granularity của phê duyệt và scope**. `MICROTASK_ACCEPTANCE_REPAIR.md` quyết định **QC từng task, bounded repair**. `WORKSPACE_REUSE_POLICY.md` và `GPU_FIRST_APPROVAL.md` vẫn quyết định **an toàn reuse/GPU**, nhưng các nút phê duyệt cùng loại có thể nhóm nếu tất cả phạm vi đã biết và đã được duyệt tường minh.
3. `WORKFLOW.md`, `INSTALLATION_CATALOG.md`, `MODEL_ROLE_POLICY.md`, `DEFAULTS_AND_TOOLS.md`, `ACCEPTANCE_QC.md`, `WORKSPACE_BOOTSTRAP.md`, `JOB_BRIEF.md`, `FINAL_REPORT.md` giữ dữ liệu nghiệp vụ/biểu mẫu và các ràng buộc không mâu thuẫn. **Bỏ qua các câu lịch sử** kiểu “duyệt từng Mnn/Bxxx”, “dừng sau QC PASS từng task”, “cấm reuse từ workspace cũ”, “phải cài mới mỗi JOB_DIR”, “luôn xin duyệt từng ID đã xác định”, hoặc “mỗi Gxx phải có nút riêng” **khi và chỉ khi** có gói đã duyệt chính xác bao trùm. Không được hiểu ưu tiên là cho phép tự cài, tự sửa dữ liệu ngoài phạm vi hay vượt cổng sáng tạo.

Bảng đối chiếu xung đột đã kiểm: `WORKFLOW.md` câu Gxx/phê duyệt riêng → Gxx có QC riêng nhưng **Mnn không cần click**; `INSTALLATION_CATALOG.md` nút từng Axx → **có thể nhóm Axx đã chốt**; `DEFAULTS_AND_TOOLS.md` cấm reuse → **reuse workspace cũ đúng deviceId/root có kiểm chứng**; `MODEL_ROLE_POLICY.md` các bước model plan/install → **có thể chung một package chỉ nếu đầu vào cài đặt đã xác định đầy đủ**; `WORKSPACE_BOOTSTRAP.md` hỏi logo sau scaffold → bước lựa chọn logo linh hoạt, nhưng **chỉ đọc nguồn đã chọn và chỉ ghi JOB_DIR sau duyệt**. Từng hướng dẫn không mâu thuẫn vẫn giữ.

## 2. P00 — thứ tự chuẩn, tránh lặp phê duyệt

1. Xác minh `deviceId` qua `Remote Desktop Commander`, tìm `FILM_DIR`, xác định `SOURCE_MOVIE` chính xác. Chọn `LOGO_DIR` hoặc không logo; có thể hỏi logo sau scaffold nếu chưa có thông tin, **không mặc định** logo kênh khác.
2. **Đề xuất scaffold** và chỉ sau một phê duyệt thật mới tạo `JOB_DIR=FILM_DIR\REVIEW_PHIM_WORKSPACE\<safe-project-id>`. Trước khi có JOB_DIR, lưu approval và QC trong **chat**, không giả tồn tại `logs/`/hash. Sau scaffold ghi provenance phê duyệt từ chat vào JOB_DIR.
3. **Gói kiểm kê chỉ đọc** P00: CPU/RAM/GPU/VRAM/Windows/arch/disk, đối chiếu 11 ID `A01–A08/O01–O03` trong các root workspace cũ **đã được duyệt trên cùng deviceId**; không chạy executable, smoke, import, infer hay tải trong pha metadata.
4. Trình **bảng đầy đủ 11 ID** với version/checksum/nguồn/ABI/backend/VRAM/budget/license/trạng thái. `REUSE_READY` chỉ khi bằng chứng/smoke đã hợp lệ và riêng **quyền reuse** được phê duyệt; `FOUND_NOT_VERIFIED` cần smoke **đã liệt kê**; `MISSING`/`INCOMPATIBLE` chỉ cài khi nguồn, version, hash, target, dung lượng, backend và quyền ghi đã khóa trong gói. Nhóm nhiều mục **không thể** biến một hàng UNKNOWN thành quyền tự xác minh rồi cài tùy ý. Optional O01–O03 không tự thành bắt buộc.
5. GPU-FIRST: Nếu thiếu cuBLAS/cuDNN/CUDA/model GPU, `GPU_STATUS=GPU_NEEDS_SETUP` → `GPU_APPROVAL`. Khi chưa có version/nguồn/hash, chỉ duyệt `GPU.PLAN` (nghiên cứu read-only), **sau đó** trình `GPU.RUNTIME` mới. Nếu trước khi người dùng duyệt đã biết đầy đủ thông tin cả hai hành động độc lập, có thể trình **một package** nêu rõ `PLAN` và `RUNTIME`, giới hạn cài chính xác; không suy từ “duyệt PLAN” thành quyền cài. CPU fallback cần quyền riêng khi GPU chưa phù hợp; không đụng OS/driver/PATH.
6. P00 hoàn thành **không tự chạy G01** trừ khi G01 đã được nêu riêng, có điều kiện đầu vào/gate hợp lệ và được người dùng duyệt trong một package.

## 3. G01–G15 — giai đoạn, deliverable, cổng quyết định

| G | Nhiệm vụ và đầu ra tối thiểu | Cổng/điểm dừng bắt buộc |
|---|---|---|
| G01 | Probe/hash/timing, visual source profile, media manifest | Q01 nguồn và thời gian có chứng cứ |
| G02 | Audio source, Faster-Whisper ASR + VAD, transcript/ASR flags, coverage | Q02, không coi ASR là dịch |
| G03 | ChatGPT tự đọc toàn bộ và dịch từng segment/timecode, coverage/flags | Q03, clip cần nghe phải upload chat; không dùng model/script dịch |
| G04 | Scene index, contact sheet, chuỗi motion, characters, story/event/evidence | Q04=`FILM_UNDERSTANDING_READY`, không bịa verified visual |
| G05 | REVIEW kịch bản sáu bước + evidence map | Q05=`REVIEW_STORY_READY` **và** người dùng duyệt kịch bản (`G05_SCRIPT`); pending=`WAITING_FOR_HUMAN_APPROVAL` |
| G06 | Beat map khôi phục 100% bản TTS đã duyệt | Q06 chỉ sau `G05_SCRIPT` |
| G07 | Chọn giọng + sample A/B, WAV theo beat, QC phát âm | Trước chạy hàng loạt cần người dùng duyệt giọng (`G07_VOICE`); Q07, không tự mặc định Trúc Ly |
| G08 | Shot candidates, inspected evidence, hard reject sai actor/action, shot map | Q08=`SHOT_SELECTION_READY` trước G09 |
| G09 | EDL nguồn sự thật, timeline draft/project Remotion, smoke, **preview/pilot bounded** (không full render hàng loạt) | Q09=`EDIT_PLAN_READY` và pilot assets sẵn để G10 xét; draft MP4 ở đây chỉ là preview/clip ngắn đã duyệt |
| G10 | Dựng pilot đại diện bằng EDL+WAV thực, nghe/xem QC và trình quyết định | `G10_PILOT` chỉ được người dùng approve; chưa approve=`WAITING_FOR_HUMAN_APPROVAL`; không tự khởi chạy full render |
| G11 | Render full video thành chunks và visual transforms/upscale đã duyệt, đối chiếu before/after | Q11 sau G10 pilot approved; không tự đánh đồng upscale với native Full HD |
| G12 | Intro/logo/brand safe area, QC đồng bộ timeline | Q12; thương hiệu/brand config phải được duyệt nếu chưa có |
| G13 | Nhạc có nguồn/license rõ, mix ducking/voice-only A/B, QC LUFS/peak | Q13, không tự tải nhạc mới ngoài package |
| G14 | FFprobe/decode, inspect clip + audio thật, kiểm story/visual/technical | Q14 với `TECHNICAL_STATUS`, `STORY_STATUS`, `VISUAL_EDITING_STATUS` đều PASS trước sẵn sàng xuất bản; thiếu nghe/xem NOT_VERIFIED |
| G15 | Bàn giao MP4/ZIP/manifest/SHA-256, `DELIVERY_PASS` | **Không bắt buộc xóa.** `DELETE_NOT_REQUESTED`/`DELETE_DECLINED` không làm Q15 fail; G15.M05 xóa chỉ khi danh sách file cụ thể đã được phê duyệt độc lập |

Với dự án cũ đã render full trong G09: giữ tệp đó như **draft chưa phát hành**, không render lại nếu hash/QC hợp lệ, nhưng **không** coi việc tồn tại MP4 là người dùng đã duyệt pilot hay G14 PASS. G11 chỉ thay đổi/sản xuất full sau `G10_PILOT`.

## 4. Gói phê duyệt hữu hạn, hash, session state, nhân sự

- `WORK_PACKAGE_ID` là đơn vị phê duyệt. Cần `schema_version=work-package.v2`, `deviceId`, canonical Windows `JOB_DIR`/source, `source_hash` đã có (P00 read-only chưa đo được dùng `UNKNOWN` có điều kiện), `allowed_stages`, **task_ids cụ thể hoặc `bounded_batches` `{stem,start,end}` hữu hạn** không wildcard/TBD, `allowed_read_roots`, `allowed_write_roots`, `allowed_executables_and_models`, `install_budget` đầy đủ, `repair_budget={per_issue,total,allowed_kinds}`, `human_gates`, `expected_outputs`, `acceptance_criteria`, `stop_conditions`.
- `plan_hash` = SHA-256 trên UTF-8 JSON canonical `json.dumps(plan,ensure_ascii=False,sort_keys=True,separators=(',', ':'),allow_nan=False)` **không** chứa chính trường `plan_hash`; số thực NaN/Inf, wildcard, cấp quyền cài “UNKNOWN” đều bị từ chối. Trước hash kiểm `deviceId`, path normalized/canonical, link/junction, source, root, checksum, stage và giới hạn. Mọi thay đổi plan hành động, model, target, source, license hoặc ngân sách → hash mới + **phê duyệt gói mới**.
- `approval_ref` chỉ hợp lệ nếu trỏ tới tin nhắn người dùng đã thật sự bấm/gửi đúng `WORK_PACKAGE_ID` + `plan_hash` + device/root + scope. Click `Tiếp tục gói` **không** phải phê duyệt mới, chỉ yêu cầu làm tiếp theo quyền đã tồn tại. Approval một TASK_ID trước v1.3.12 không tự rộng thành package.
- Trạng thái chuẩn: `PROPOSED → APPROVED → RUNNING → {PARTIAL, WAITING_FOR_JOB, WAITING_FOR_AUDIO_UPLOAD, WAITING_FOR_HUMAN_APPROVAL, NEEDS_FIX, NOT_VERIFIED, BLOCKED, PACKAGE_PASS}`. `PACKAGE_PASS` và `CANCELLED` terminal. Từ paused → `RUNNING` chỉ qua resume được người dùng chủ động kích hoạt, khớp context/hash và đã giải quyết dependency (nếu có). Không tự chạy nền giữa các lượt chat; **không tự chạy nền** nghĩa là mọi lượt tiếp theo phải do người dùng kích hoạt.
- Mỗi task lưu input/output hashes và `QC_STATUS`, `logs/microtask_ledger.jsonl`, `qc/microtasks/<TASK_ID>/acceptance.vN.json`; mỗi gói lưu `logs/work_package_ledger.jsonl`/`state.json`. `PACKAGE_PASS` chỉ khi toàn bộ task trong scope có QC PASS, không thiếu coverage, final package QC PASS, **human gates có chứng cứ phê duyệt riêng**. Một task PASS không tự mở một human gate.
- Human gates nội dung `G05_SCRIPT`, `G07_VOICE`, `G10_PILOT`; `G15_DELETE` chỉ dành cho tập file xóa cụ thể. Chờ người dùng thì `WAITING_FOR_HUMAN_APPROVAL` chứ không phải `NOT_VERIFIED`/`PARTIAL` tùy tiện. Khi chọn/thay đổi nội dung đã duyệt phải cập nhật hash và invalidate downstream có phụ thuộc, không ghi đè output đã được user chấp thuận.

## 5. Chống trùng, lỗi, resume và người dùng chỉ cần một nút

- Trước RUNNING, mở lock `JOB_DIR/logs/work_package.lock` theo **atomic exclusive create**. Lock chứa `owner_run_id`, deviceId, WORK_PACKAGE_ID, plan_hash. Cùng owner mới được release; lock tồn tại/không rõ tiến trình → `BLOCKED`, **không tự xóa, không cướp lock hoặc kill process**. Người dùng phê duyệt recovery riêng nếu cần mở khóa cũ sau khi kiểm log và xác nhận không còn job.
- Dedupe `event_id=SHA256(WORK_PACKAGE_ID|plan_hash|task_id|input_hashes|attempt)` trong ledger; nếu task `QC_STATUS=PASS` và output hash vẫn khớp → **skip, không chạy lại**. RUNNING bị gián đoạn chỉ được kiểm/chạy lại phần dở và không nhân đôi download, voice, render hay ghi đè. Two-click hoặc two-session không cùng chạy.
- Khi job CPU/GPU/render vẫn chạy ở máy từ xa: `WAITING_FOR_JOB` chỉ theo dõi sau click/được phép, không hứa agent chạy nền; chưa có output không gọi PASS. Nếu audio cần nghe, `WAITING_FOR_AUDIO_UPLOAD` + file path thực/link sandbox đã kiểm, không bịa nghe. Nếu cần user quyết định script/voice/pilot thì chờ human gate.
- `repair_budget` mặc định **0** khi không được duyệt; nếu đã nêu đích danh cho phép tối đa `per_issue=2`, `total<=4` (hoặc chặt hơn), `allowed_kinds` hữu hạn; patch đảo ngược được, QC lại/rollback trên JOB_DIR. Lỗi phát sinh vượt total, thay semantic, source, GPU/backend, cài/tải/xóa/đổi quyền → xin duyệt scope mới. Không tạo issue ID mới vô tận để né trần.
- Lúc resume bắt buộc đối chiếu approval, plan_hash, source_hash, hashes đầu vào, task ID, QC report, `deviceId`/`JOB_DIR`, lock và mọi human gate. Không mất nguồn cũ và không tự bịa trạng thái.

## 6. Cơ chế nhận diện workspace cũ (v1.3.11 → v1.3.12)

- Nếu chỉ có `microtask_state.json`/`microtask_ledger.jsonl` **mà không có** `work_package_state.json`: lập `LEGACY_INVENTORY` **read-only**, ghi trong chat hoặc file mới dưới JOB_DIR khi đã cho phép. Đối chiếu source hash, task ID, approval cũ, tiêu chí QC + evidence thật. Tệp PASS đủ chứng cứ ghi `LEGACY_EVIDENCE_VERIFIED`, không hợp lệ ghi `NOT_VERIFIED`; **không ghi đè log cũ**, không giả QC/PASS.
- Trình **phê duyệt một gói mới** với finite scope để tiếp tục. Task đã kiểm chứng có thể skip sau khi người dùng đã duyệt gói mới; approval microtask trước không cấp quyền mở rộng. Giữ `legacy_checkpoint_refs` và SHA-256 cũ để truy nguyên.
- Nếu workspace đã có work-package.v1, không tự chuyển schema tại chỗ; kiểm metadata read-only và tạo `work_package.v2` snapshot mới **sau quyền sửa/tiếp tục**, ghi lineage, không sửa mất lịch sử.

## 7. Tiêu chuẩn nghiệm thu v1.3.12

- 15 giai đoạn vẫn xuất đủ artifact cũ; thay đổi duy nhất ở thứ tự G09/G10 full-render/pilot, granularity phê duyệt, trạng thái và recovery. G14/Q14 kiểm ba chiều; G15 bàn giao độc lập xóa.
- Unit tests phải bao phủ: plan canonical, wrong approval, bounded batches, no double run, source hash mismatch, blocked human G05/G07/G10, G15 no delete by delivery, resume after paused, error budget total, legacy evidence read-only, lock contention. Bài thử chỉ kiểm policy/stdlib không xác nhận GPU/TTS/movie thật.
