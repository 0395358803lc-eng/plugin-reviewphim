# MICROTASK_ORCHESTRATION — G01–G15: thực hiện nhiều task sau một lần phê duyệt gói

**ĐỌC `WORKFLOW_CONSISTENCY_V1312.md` TRƯỚC**, sau đó **ƯU TIÊN SMART_BATCH_APPROVAL.md.** Microtask `Gxx.Mnn[.Bxxx]` là đơn vị **thực thi, checkpoint và QC**, không phải đơn vị phê duyệt; mọi lệnh cũ “1 click = 1 task”, “không tự chạy task tiếp theo”, “dừng sau mỗi PASS để duyệt B tiếp” không còn hiệu lực **bên trong WORK_PACKAGE_ID đã được duyệt**. Bên ngoài gói **không được chạy bất kỳ task mới**. QC nội bộ theo `MICROTASK_ACCEPTANCE_REPAIR.md`.

## Điều phối

1. Đề xuất gói hữu hạn với `WORK_PACKAGE_ID`, `plan_hash`, `deviceId`, FILM_DIR/JOB_DIR, source_hash, allowlist các Mnn/Bxxx, root, budget, đầu ra/tiêu chí QC và hard gates. Nút **Phê duyệt gói <ID>** dùng `GenUI.issueNewTurn` và ID thật.
2. Trong mỗi lượt người dùng kích hoạt, sau khi đã được duyệt, thực hiện nhiều microtask liên tiếp có checkpoint từng task; `PASS` → **task tiếp theo trong gói**. Người dùng không phải bấm lại sau mỗi QC PASS; không xin phê duyệt từng batch. Mỗi batch vẫn độc lập có `start_id`, `end_id`, `input_hash`, `output_hash`, coverage, lineage.
3. `PARTIAL` / `WAITING_FOR_JOB` khi một lượt High không đủ: lưu `microtask_state.json`, `microtask_ledger.jsonl`, `work_package_state.json`, và trình nút **Tiếp tục gói** cho lượt mới; không phê duyệt lại các tác vụ cũ, cũng không tự chạy nền hoặc tự gửi lượt mới.
4. `NEEDS_FIX`: trong `repair_budget` có thể tự sửa tối đa hai lần/issue và tối đa 4 lần/gói (hoặc thấp hơn đã duyệt), có recheck; `WAITING_FOR_HUMAN_APPROVAL` (kịch bản/giọng/pilot) dừng riêng; ngoài phạm vi, thiếu chứng cứ, mất quyền, sai hash hay cổng người dùng chưa duyệt → dừng đúng gate. Không dùng nút nút giả hay placeholder. Không nhảy qua Q01–Q15.

## Ngân sách microtask nội bộ (giới hạn chất lượng, không giới hạn số lần bấm)

- G03: tối đa **40 segment** hoặc **1.000 từ** nguồn/lô, lấy giới hạn đến trước; ChatGPT phải thực sự đọc và tự dịch từng segment.
- G04: tối đa **8 scene** hoặc 24 ảnh/chuỗi visual/lô; G05: tối đa 4 đoạn REVIEW/lô; G06/G08: tối đa **12 beat**/lô; G07: tối đa 12 WAV/lô; G09: tối đa 12 beat EDL/lô.
- G11/G12/G13/G14 chia chunk hữu hạn; không gộp hàng trăm cảnh vào một lệnh không thể kiểm soát. Có thể làm nhiều batch *cùng một gói* trước khi báo người dùng.
- Mỗi batch ghi `schema_version`, `project_id`, `device_id`, `film_dir`, `job_dir`, `source_hash`, `stage_id`, `microtask_id`, `batch_id`, `WORK_PACKAGE_ID`, `plan_hash`, `approval_ref`, `input_hashes`, `output_hashes`, `qc_status`, `start_id`, `end_id`, `count_expected`, `count_actual`, `next_task_id`, `updated_at`.

## Bảng microtask nội bộ 15 giai đoạn (giữ thứ tự và gate)

| Giai đoạn | Công việc nội bộ đã liệt kê trong gói, không trình một nút cho mỗi Mnn | Gate |
|---|---|---|
| **G01 — Nguồn phim** | `M01` hash/read-only và chỗ ghi; `M02` FFprobe/codec/timing; `M03` mẫu visual source; `M04` QC manifest | Q01 media_probe/source_timeline/source_profile đầy đủ |
| **G02 — Transcript nguồn** | `M01` trích audio/chia lô; `M02.Bxxx` Faster-Whisper ASR; `M03` rà flags; `M04` ghép JSONL và QC; `M03.Rxxx` nghe khi cần | Q02 transcript đủ coverage, không đoán câu thiếu |
| **G03 — ChatGPT tự dịch** | `M01` phân lô/hash; `M02.Bxxx` ChatGPT dịch trực tiếp; `M03.Bxxx` đối chiếu/gỡ lỗi; `M04` gộp transcript; `M05.Rxxx` nghe khi mơ hồ | Q03 gốc↔dịch đủ segment/timecode, không model dịch |
| **G04 — Hiểu phim** | `M01` scene index; `M02.Bxxx` frames/contact sheets; `M03.Bxxx` ChatGPT xem; `M04.Bxxx` đối chiếu transcript; `M05` story map QC; `M06.Rxxx` chứng cứ bổ sung | Q04 FILM_UNDERSTANDING_READY |
| **G05 — Viết REVIEW** | `M01` outline/evidence; `M02.Bxxx` soạn review; `M03.Bxxx` QC logic/cảm xúc; `M04` ghép TTS script; `M05` người dùng duyệt bản hoàn chỉnh | Q05 REVIEW_STORY_READY, user duyệt kịch bản |
| **G06 — Chia beats** | `M01` khóa script đã duyệt; `M02.Bxxx` chia beat/event; `M03` ghép toàn text; `M04` kiểm coverage | Q06 đủ narration không biến dạng |
| **G07 — Giọng đọc** | `M01` chọn giọng/config; `M02` mẫu giọng người dùng duyệt; `M03.Bxxx` TTS WAV; `M04.Bxxx` QC WAV; `M05` aggregate | Q07 user duyệt giọng, WAV sạch |
| **G08 — Tìm cảnh** | `M01` beat→scene index; `M02.Bxxx` tìm candidates; `M03.Bxxx` ChatGPT xem/hard-reject; `M04.Bxxx` chọn/dự phòng; `M05` shot_map QC | Q08 SHOT_SELECTION_READY |
| **G09 — EDL & preview** | `M01` WAV/FPS/schema; `M02.Bxxx` EDL từng beat; `M03` pacing continuity; `M04` Remotion smoke; `M05` tạo preview/pilot ngắn hữu hạn; `M06` kiểm preview, không render full | Q09 EDIT_PLAN_READY, preview cho G10 |
| **G10 — Pilot** | `M01` chọn đoạn; `M02` dựng pilot theo EDL+WAV thật; `M03` ChatGPT xem/nghe kiểm; `M04` người dùng duyệt pilot/style hoặc gói sửa; khi chờ ghi WAITING_FOR_HUMAN_APPROVAL | Q10 pilot được người dùng duyệt trước full render |
| **G11 — Chất lượng hình** | `M01` transform/preset; `M02.Bxxx` before-after kiểm; `M03.Bxxx` full render chunks/upscale sau duyệt G10; `M04` ghép master+QC | Q11 full output đúng transform và codec/crop |
| **G12 — Intro & logo** | `M01` logo/brand; `M02` mẫu overlay; `M03.Bxxx` áp intro/logo; `M04` QC vị trí/âm | Q12 đúng nhận diện đã duyệt |
| **G13 — Nhạc & mix** | `M01` cue/license; `M02` A/B mix; `M03.Bxxx` ducking; `M04` merge LUFS/peak; `M05` QC có/không nhạc | Q13 không lấn voice, nguồn nhạc hợp lệ |
| **G14 — Nghiệm thu** | `M01` hash/ffprobe/decode; `M02.Bxxx` story/QC; `M03.Bxxx` visual/QC; `M04.Rxxx` clip nghe/xem; `M05` tổng hợp; `M06.Rxxx` recheck | Q14 technical/story/visual đều có bằng chứng |
| **G15 — Bàn giao** | `M01` inventory/hash; `M02` ZIP/manifest; `M03` kiểm file và đánh dấu DELIVERY_PASS; `M04` đề xuất file xóa tùy chọn (không xóa); `M05` chỉ thực hiện G15_DELETE sau quyền xóa riêng | Q15 bàn giao không phụ thuộc DELETE_NOT_REQUESTED; xóa là tùy chọn |

## Các trường hợp bắt buộc

- G03 nhiều lô: một package đủ segment range được duyệt cho `G03.M02.B001`, `G03.M02.B002` và QC tương ứng; không xin duyệt từng batch. Nếu user chỉ duyệt B001 từ quy trình cũ, không tự suy rộng sang B002.
- G04/G08 cần ChatGPT xem chứng cứ thật; G14 cần audio thật khi mức QC yêu cầu. `WAITING_FOR_AUDIO_UPLOAD` → người dùng gửi clip lên chat; không đánh dấu PASS bằng metadata.
- G09 render chưa xong → `WAITING_FOR_JOB`, nút tiếp tục/kiểm tra, không hứa đang chạy ChatGPT nền. Sai source_hash/plan_hash/deviceId → BLOCKED.
- `QC_STATUS=PASS` của task không thay human gate G05/G07/G10 và quyền xóa G15. G05_SCRIPT trước G06, G07_VOICE trước TTS hàng loạt, G10_PILOT trước full render G11. Mất phiên/double click phải dùng work_package.lock; không tự chạy nền.

## Báo cáo giao diện

**Trước gói:** roadmap 3–6 nhóm đầu việc; một nút `Phê duyệt gói`; không trải hàng chục nút Mnn. **Sau gói:** `WORK_PACKAGE_ID`, tổng số batch PASS/N, output, QC errors, các quyền còn thiếu. Khi dở: một nút `Tiếp tục gói`. Khi vượt scope: một nút duyệt gói sửa/nâng phạm vi. Không dùng phê duyệt `Gxx.Mnn` làm mặc định.
