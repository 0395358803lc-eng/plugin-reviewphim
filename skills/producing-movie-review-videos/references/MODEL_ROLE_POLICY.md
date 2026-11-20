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

# MODEL_ROLE_POLICY — Phân vai AI, khóa model và xác minh hình ảnh (v1.3.8)

**Ưu tiên áp dụng** cùng `SKILL.md`, `APPROVAL_TRANSLATION_AUDIO.md`, `INSTALLATION_CATALOG.md`, `GPU_FIRST_APPROVAL.md`, `FILM_UNDERSTANDING.md`, `SCENE_MATCHING.md` và QC microtask. Không thay số lượng ID cài đặt, nguồn phim, phạm vi `JOB_DIR` hoặc quyền phê duyệt. Quy tắc này làm rõ G03/G04/G08, không cho phép cài đặt mới.

## G03 — Chỉ ChatGPT trực tiếp dịch

- G02 được phép chạy Faster-Whisper (A04) ở chế độ ASR/transcribe để sinh transcript lời thoại **gốc**; **không** `task=translate`.
- G03 chính ChatGPT đọc `analysis/transcript_original.jsonl` **đầy đủ theo batch đã duyệt** và trực tiếp dịch sang tiếng Việt trong phiên chat. **Không** sử dụng model dịch khác local/API, phần mềm dịch, script tự dịch, dịch máy, Gemini, LLM local hay gọi dịch vụ ngoài.
- Giữ `segment_id`, `start`, `end`, nhân vật, tên riêng, nội dung gốc và bản dịch; checksum, coverage, đoạn chưa nghe xác minh được lưu vào QC. Python chỉ hỗ trợ chia/ghép/ghi/kiểm chứng dữ liệu; không sáng tác câu dịch. Thiếu lô thì `PARTIAL/NOT_VERIFIED`, không kết luận G03 đạt.
- Kết luận cần nghe: trích audio sau phê duyệt và yêu cầu người dùng gửi file vào chat; chưa có audio thì `WAITING_FOR_AUDIO_UPLOAD`.

## O01/O02 — Quy trình chọn model chuẩn theo từng máy

- **O01** = Qwen-VL vision local / inference; **O02** = CLIP hoặc embedding local / retrieval. **Cả hai đều là tùy chọn và không tự kích hoạt**. `ChatGPT` trực tiếp đọc hình/chọn shot ngay cả khi không có O01/O02; nếu kênh hình không dùng được, báo `BLOCKED/NOT_VERIFIED` chứ không thay bằng nhận định AI local.
- Chỉ sau P00 hardware profile CPU, RAM, GPU, VRAM, OS/ABI và dung lượng trống, lập `MODEL_SELECTION_PLAN` cho từng ID tùy chọn được yêu cầu. Trình **đầy đủ**: `ID`, nhiệm vụ G04/G08, **model_id** (repo/tên checkpoint cụ thể), **revision** (tag/commit cố định), **sha256** của gói/weights được tải hoặc danh sách từng file có checksum, `license`, nguồn chính thức, `quantization`, `backend`, dependencies được khóa, `precision`, batch/threads, RAM/VRAM tối thiểu/dự trù, dung lượng tải + giải nén + cache + dự phòng, `JOB_DIR` đích, rủi ro, lệnh smoke test và tiêu chí QC.
- Không tự lựa chọn một checkpoint theo tên chung `Qwen-VL`/`CLIP` rồi tải. Không điền giả `revision`/`sha256`/VRAM. Nếu dữ liệu chưa kiểm chứng thì ghi `UNKNOWN`, trình **phê duyệt kế hoạch xác minh** chỉ đọc trước; không có quyền tải/cài suy ra từ việc lập kế hoạch.
- Duyệt riêng `P00.O01.MODEL_PLAN` / `P00.O02.MODEL_PLAN`, rồi mới `P00.O01.MODEL_INSTALL` / `P00.O02.MODEL_INSTALL` với phiên bản, hash, nguồn, dung lượng cố định; mỗi bước là microtask riêng. `approval_id` phải chỉ đến phê duyệt thật. Không tự mở rộng A01–A08/O01–O03 hoặc dùng cache/runtime ngoài `JOB_DIR`.
- Sau cài, ghi `models/model_selection_manifest.json`: `model_id`, `revision`, `sha256`, `quantization`, `backend`, `precision`, `device`, `VRAM`, `model_approved` (chỉ true khi có `approval_id`), `approval_id`, `installation_status`, `smoke_test_status`, `job_dir` và đường dẫn bằng chứng log/hash. Chỉ ghi `GPU_READY` khi inference GPU đã smoke PASS. Nếu không hỗ trợ/không đạt bộ nhớ, giải thích và xin duyệt phương án khác hoặc CPU fallback; không tự thay checkpoint/precision.
- `MODEL_SELECTION_PLAN` là thiết kế theo máy, không phải cơ chế máy tự chọn model lúc chạy. Không cài khi người dùng chưa phê duyệt cụ thể.

## G04/G08 — Model chỉ gợi ý; ChatGPT xác minh nội dung

- **G04**: A01/A03/A08 trích chỉ mục scene, contact sheet, ảnh/clip thực. O01 nếu đã duyệt chỉ thêm mô tả/nhãn đề xuất ở trạng thái `CANDIDATE`. Kết quả model, confidence, số frame trích hay `scene_id` **không tự động** tạo `VISUALLY_REVIEWED` hoặc bằng chứng ChatGPT đã xem.
- **G08**: O01/O02 nếu đã duyệt chỉ giúp truy hồi/rank `CANDIDATE`. Không cho phép model tự gán `VERIFIED_VISUAL` hay tự quyết `shot_map` cuối. Chấm cosine cao không khắc phục được sai actor/action/storyline/time domain.
- Để nâng lên `VERIFIED_VISUAL`, ChatGPT phải **thực sự nhìn** bằng chứng chuyển được tới kênh quan sát: `evidence_refs` tồn tại (đúng phim/hash, timestamp nguồn, ảnh/clip có thể kiểm), `inspected_by_chatgpt=true` sau khi xem, nhận diện actor/action/emotion/storyline, và `motion_verification=VERIFIED` cho claim hành động/camera liên tục (cần chuỗi frame hoặc clip); chỉ một ảnh tĩnh không đủ.
- Khi có nhiều người giống nhau, cảnh quá khứ/hiện tại, subtitle phủ mặt, clip mờ, không đủ motion, hoặc công cụ chỉ trả path/metadata: giữ `CANDIDATE`/`NEEDS_REVIEW`/`NOT_VERIFIED`, xuất `issue_id`, đề xuất kiểm chứng thêm có phê duyệt. Không dùng model để che lấp thiếu hình ảnh.
- **Gate `FILM_UNDERSTANDING_READY` (G04)** yêu cầu bằng chứng cho sự kiện cốt lõi, mạch truyện, tuyến thời gian và coverage thật. **Gate `SHOT_SELECTION_READY` (G08)** yêu cầu mọi critical beat có shot đúng phim/nhân vật/hành động, `VERIFIED_VISUAL`, nguồn timestamp hợp lệ và không còn orphan critical. Cả hai gate độc lập với `model_approved` và `smoke_test_status`, không tự vượt gate hoặc quyền duyệt microtask kế.
- QC phải ghi `model_suggestion_source` (nếu có), `human_observation` (ChatGPT), `evidence_refs`, `inspected_by_chatgpt`, `motion_verification`, `match_status`, `reason`, `approval_id` và `QC_STATUS`. Không dùng từ “100% đã xem” nếu chỉ lấy mẫu.

## Các giai đoạn còn lại

- G05/G06/G09/G10/G13/G14: ChatGPT xử lý lý luận/biên tập/QC trên chứng cứ; Remotion/FFmpeg là engine xử lý media, không phải model AI hình ảnh.
- G07: VieNeu-TTS A05 được dùng sau duyệt voice/model; G11: AI upscaler O03 chỉ dùng nếu duyệt riêng, còn FFmpeg Lanczos/unsharp là xử lý thuật toán không phải AI upscaling.
- Mọi task vẫn phải nghiệm thu `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED`; tự động sửa hoặc cài đặt bị cấm khi chưa phê duyệt.

</details>
