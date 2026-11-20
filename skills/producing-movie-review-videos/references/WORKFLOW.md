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

# WORKFLOW — 15 giai đoạn sản xuất review phim

Áp dụng `SESSION_ORCHESTRATION.md`: chọn máy → chọn phim → scaffold workspace rỗng → chọn logo hoặc không logo → **kiểm tra phần cứng chỉ đọc** → trình đầy đủ danh mục cài A01–A08/O01–O03 với cấu hình tối ưu theo máy → duyệt cài → xin duyệt **riêng G01–G15**. Không chạy hàng loạt; không mặc định thời lượng, nguồn phim, logo, kênh hay ổ đĩa. `FILM_DIR` và `JOB_DIR=FILM_DIR\REVIEW_PHIM_WORKSPACE\<project-id>` là biến theo phiên. Mỗi giai đoạn hoàn tất phải có đầu ra thật, QC và dừng chờ duyệt giai đoạn kế. Quy tắc chia nhỏ đầu việc và nghiệm thu theo `MICROTASK_ORCHESTRATION.md` và `MICROTASK_ACCEPTANCE_REPAIR.md` luôn ưu tiên. Phân vai model AI và cổng xác minh tuân thủ `MODEL_ROLE_POLICY.md`.

## Giai đoạn 01 — Tiếp nhận và kiểm tra phim

Xác nhận đúng `SOURCE_MOVIE` và quyền chỉ đọc phim gốc; kiểm FFmpeg/FFprobe, GPU/CPU, dung lượng, codec, duration, timebase/FPS/VFR, ngôn ngữ, phụ đề cháy, audio/video offset và frame đầu–giữa–cuối. Chỉ ghi đầu ra trong `JOB_DIR`. **Đầu ra:** `analysis/media_probe.json`, `analysis/source_timeline.json`, biên bản nguồn và cảnh báo. Không phân tích hình sâu ở G01.

### Bổ sung v1.3 — Source Visual Profile

Sau khi G01 được duyệt, lấy mẫu thưa từ nhiều thời điểm để ghi `analysis/visual_source_profile.json`: `source_sha256`, `source_duration_s`, frame timestamps, active-picture/letterbox estimates, `subtitle_regions`, `burned_subtitle` (`YES/NO/UNKNOWN`), vùng text/title có nguy cơ crop, dải độ sáng, màu nếu FFprobe có metadata và `unknowns`. Không suy letterbox từ một frame tối; nếu không chắc thì `UNKNOWN`. G01 chỉ khảo sát nguồn, **không phân tích toàn phim thay G04**. Các file G01 cũ giữ nguyên.

## Giai đoạn 02 — Transcript tất cả lời thoại

FFmpeg trích audio được duyệt, Faster-Whisper local GPU/CPU fallback nhận dạng và gắn `segment_id`, start/end, ngôn ngữ, audio_kind. Đánh dấu đoạn không lời, xen kẽ ngôn ngữ, ASR gộp dài, lặp/ảo giác, quảng cáo, mất âm và timestamp vượt duration. VAD không đồng nghĩa không có biến cố hình ảnh. **Đầu ra:** `analysis/transcript_original.jsonl`, `analysis/asr_flags.json`, bản transcript đọc được và log. Không dùng mốc sai để suy ra sự kiện phim.

## Giai đoạn 03 — Dịch theo ngữ cảnh phim

**ChatGPT trực tiếp đọc toàn bộ** transcript nguồn `analysis/transcript_original.jsonl` theo các lô đã phê duyệt và tự dịch sang tiếng Việt trong hội thoại, **không dùng model dịch** local/API, dịch máy, công cụ/phần mềm dịch hoặc chế độ Whisper translate. Giữ nguyên `segment_id`, timestamp, quan hệ nhân vật, tên riêng và kiểm tra bao phủ từng lô. Video/ảnh/âm thanh người dùng gửi vào chat giúp giải quyết câu mơ hồ; không bịa câu; để `[CẦN ĐỐI CHIẾU ÂM THANH]` khi chưa thể kiểm chứng. Code chỉ chia lô, đọc/ghi và kiểm schema/hash/coverage; **không tự tạo câu dịch**. Phải tuân thủ `APPROVAL_TRANSLATION_AUDIO.md` và `MODEL_ROLE_POLICY.md`. **Đầu ra:** `analysis/transcript_vi.jsonl`, `analysis/translation_flags.json`, `transcript_vi.txt`, bảng source→translation.

## Giai đoạn 04 — Hiểu phim đa phương thức

**Bắt buộc đọc:** `references/FILM_UNDERSTANDING.md` và `references/EVIDENCE_SCHEMA.md`. Dùng PySceneDetect/FFmpeg lấy chỉ mục scene toàn phim, frame/contact sheet có timestamp, chuỗi hình/clip khi cần để ChatGPT trực tiếp đọc hình ảnh thật. Đối chiếu transcript; xác định tuyến nhân vật, biến cố không lời, hành động, biểu cảm, nguyên nhân/hậu quả, cao trào, thứ tự xuất hiện trên màn hình và thứ tự thời gian câu chuyện. Phân biệt quan sát, lời thoại, suy luận. Mỗi event trọng yếu có evidence hữu hình và trạng thái xác minh. **Đầu ra:** `analysis/scene_catalog.json`, `analysis/visual_events.json`, `analysis/story_map.json`, `analysis/characters.json`, `analysis/evidence_index.json`, `qc/g04_evidence_report.md`. **Gate `FILM_UNDERSTANDING_READY`:** không đề xuất G05 khi còn claim cốt lõi chỉ dựa vào suy đoán; nếu nguồn hình chưa xem được, báo `BLOCKED`. Chia batch/checkpoint cho phim dài; không tuyên bố 100% khi chỉ lấy mẫu.

Nếu O01 Qwen-VL được phê duyệt thì chỉ dùng để tạo gợi ý/candidate; `model_approved` không đồng nghĩa `VERIFIED_VISUAL`. ChatGPT phải xem ảnh/chuỗi/clip thật có `evidence_refs`, ghi `inspected_by_chatgpt` và `motion_verification` theo chứng cứ; chưa xem được thì `NEEDS_REVIEW` hoặc `NOT_VERIFIED`, không tự động nâng sự kiện lên verified chỉ bởi model.

### Bổ sung v1.3 — Giá trị biên tập của hình

Mỗi scene/shot được lập `analysis/visual_shot_profile.json` ngoài bộ `scene_catalog` và `visual_events` đang có. ChatGPT xem ảnh thật để mô tả `shot_type` (CLOSE_UP/MEDIUM/WIDE/DETAIL/...), chủ thể, biểu cảm quan sát, vật chứng, `visual_purpose`, `quality_flags`; chỉ nhận định `camera_motion` / hành động liên tục sau khi xem chuỗi frame hoặc clip, nếu không ghi `UNKNOWN`. Ghi `inspected_by_chatgpt`, bằng chứng có đường dẫn/timecode và trạng thái kiểm chứng. Bao phủ chỉ mục toàn phim không được quảng cáo là đã xem 100% frame. Gate `FILM_UNDERSTANDING_READY` vẫn xét sự kiện cốt lõi, không bị chặn bởi trường góc hình chưa rõ ở cảnh không quan trọng.

## Giai đoạn 05 — Viết REVIEW kể chuyện

**Bắt buộc đọc:** `references/REVIEW_STORYTELLING.md` và `references/EVIDENCE_SCHEMA.md`. Chỉ viết khi G04 đạt gate và người dùng duyệt G05 riêng. Dựng outline có `event_ids`, theo **6 bước bắt buộc**: chọn mở đầu tạo tò mò → giới thiệu nhân vật/hoàn cảnh → kể sự kiện bằng hành động/nguyên nhân → đẩy xung đột và cảm xúc có căn cứ → tạo câu hỏi/chuyển tiếp biến cố → tập trung cao trào và giải quyết. Từng đoạn dùng bối cảnh → hành động → động cơ → xung đột → phản ứng → hậu quả → chuyển tiếp tùy cần. Chuyển thoại thành lời kể ngôi ba tự nhiên, giữ truyện phi tuyến khi hợp lý, không sao chép transcript thô/không bịa. Phân biệt `FILM_FACT`, `CHARACTER_INFERENCE`, `NARRATOR_COMMENTARY`, `EXTERNAL_FACT`; mọi claim trọng yếu truy xuất G04. **Không mặc định thời lượng**; số từ và WAV thật quyết định kết quả. **Đầu ra:** `review/review_outline.json`, `review/review_ke_chuyen.txt`, `review/review_loi_binh_tts.txt`, `review/review_evidence_map.json`, `qc/g05_story_qc.md`. **Gate `REVIEW_STORY_READY`**; kịch bản chưa tự coi được người dùng duyệt.

### Bổ sung v1.3 — Visual intent tùy chọn, KHÔNG thay 6 bước

`review/review_outline.json` có thể thêm `visual_intent_hints` cho từng đoạn (`visual_moment_hint`, `required_emotion_on_screen`) liên kết `event_ids`; gợi ý này **không phải sự kiện mới** và không được làm thay lời kể để khớp clip đẹp. Khi thiếu hình, G08 báo thiếu/đề xuất minh họa hợp lệ. Giữ nguyên chính xác công thức sáu bước, gate `REVIEW_STORY_READY` và quyền người dùng duyệt G05.

## Giai đoạn 06 — Chia lời bình thành nhịp ý (beats)

Chia câu/mệnh đề đúng nội dung đã duyệt, mỗi beat có `beat_id`, `paragraph_id`, `narration_text`, `event_ids`, `source_scene_ids`, `storyline`, actor/action/emotion/intent và evidence. Không tự sáng tạo event mới khi chia; các beat về nhiều tuyến phải tách. Nối beat khôi phục **100%** bản lời bình TTS đã duyệt, kiểm hash văn bản và coverage bằng chứng. **Đầu ra:** `beats/beats.json`, `beats/beat_evidence_coverage.json`.

### Bổ sung v1.3 — Beat Visual Brief

Trong `beats/beats.json` bổ sung các trường **optional**: `preferred_shot_types`, `visual_intent`, `emotional_intensity`, `pacing_intent`, `cut_priority`, `continuity_requirement`, `subject_visibility_requirement`, `avoid_shot_types`, `visual_intent_status`. Xuất `beats/beat_visual_brief.json` theo `beat_id`, không sửa `narration_text`. Không có hình đủ chứng cứ thì trạng thái `DRAFT`/`NEEDS_REVIEW`, không giả verified. Ghép các beats phải **khôi phục 100%** bản `review_loi_binh_tts.txt` đã duyệt (so ký tự/hash).

## Giai đoạn 07 — Tạo giọng đọc local

Dùng VieNeu-TTS v3 Turbo nếu có, giọng Trúc Ly 1.00x là preset **tham khảo** cần duyệt khi chưa có xác nhận. TTS theo beat WAV, hash text+voice cho cache, retry/resume, hậu kiểm phát âm tên riêng dựa trên characters G04, silence, clipping, độ dài. **Không time-stretch** để đạt thời lượng giả định. **Đầu ra:** `voice/bNNNN.wav`, `voice_status.json`.

## Giai đoạn 08 — Tìm cảnh phim bám sát lời kể

**Bắt buộc đọc:** `references/SCENE_MATCHING.md`. Tái sử dụng `scene_catalog`, `visual_events`, `evidence_index` G04 để tìm nhiều clip ứng viên cùng storyline; chỉ mở rộng trích/xem phần chưa chắc. Gắn beat với đúng actor → action/event → emotion; kiểm chuyển động và clip thật cùng lời bình, **không lấy cảnh sai tuyến** để lấp thời lượng. Không tự nâng `CANDIDATE` thành `VERIFIED_VISUAL` vì có event ID; thiếu chứng cứ gắn `NEEDS_REVIEW`. Không cố định 3 shot/beat. **Đầu ra:** `shots/shot_map.csv` (src_in/out và evidence), `shots/shot_evidence.json`, contact sheets/clip kiểm chứng.

Nếu dùng O01 Qwen-VL/O02 CLIP/Embedding đã duyệt, kết quả model chỉ tạo/rank `CANDIDATE`; không tự động tạo `VERIFIED_VISUAL`. ChatGPT trực tiếp xem hình/clip, kiểm actor/action/storyline/emotion, `motion_verification`, `evidence_refs` và quyết định chọn shot; không đủ chứng cứ thì `NEEDS_REVIEW`. Gate `SHOT_SELECTION_READY` vẫn bắt buộc.

### Bổ sung v1.3 — Lựa chọn nhiều ứng viên

Đọc `references/VISUAL_EDITING.md` và `SCENE_MATCHING.md`. Xuất thêm `shots/shot_candidates.json`, `shots/shot_selection_decisions.json`; giữ cột cũ trong `shot_map.csv`, chỉ bổ sung `shot_id`, `shot_type`, `visual_intent`, `selected_rank`, `reuse_count`, `continuity_id`, `transform_hint`, `decision_evidence_ref`. **Hard reject** sai nhân vật, sự kiện, tuyến, nguồn hoặc thiếu thời lượng trước khi xét đẹp hình. ChatGPT trực tiếp kiểm hình/clip và chọn shot chính cùng phương án dự phòng, nêu lý do loại. Gate **`SHOT_SELECTION_READY`** là cổng chất lượng G08, không tự cho phép G09. Candidate, điểm embedding hoặc event ID không tự biến thành `VERIFIED_VISUAL`.

## Giai đoạn 09 — Lập EDL và dựng Remotion

Dùng thời lượng WAV thực cùng khoảng nghỉ hợp lý tính frame và clip in/out, đảm bảo timeline liên tục, không hụt lời, không hình đen ngoài ý đồ. Remotion giữ composition chỉnh sửa; FFmpeg/NVENC có thể render nhanh từ **cùng EDL**. **Đầu ra:** `timeline.json`, Remotion project, MP4 draft.

### Bổ sung v1.3 — Editorial Pacing & EDL

Dùng `references/VISUAL_EDITING.md` làm quy tắc dựng. `timeline/edit_decisions.json` là **EDL nguồn sự thật duy nhất** cho Remotion và FFmpeg fallback; `timeline/timeline.json` hiện có là view tương thích, `timeline/pacing_report.json` ghi nhịp và lặp. Mỗi edit có `source_in_s/source_out_s` thuộc phim gốc, `timeline_in_frame/timeline_out_frame_exclusive` thuộc bản dựng, `beat_ids`, `continuity_id`, `reuse_reason`, `transform`, `transition`. FPS theo phim/output được duyệt, frame nguyên, WAV thật quyết định độ dài. Nhịp `SLOW/NORMAL/FAST/ADAPTIVE` là ý đồ, **không ép 2,04 giây/cut**; giữ hành động liên tục, cảnh cận biểu cảm đủ lâu. Mọi transform `hflip=false` mặc định, chỉ thực thi khi G11 đúng phạm vi duyệt.

## Giai đoạn 10 — Kiểm thử pilot và tiếng hiện trường

Khi thiếu profile đã duyệt, dựng pilot một biến cố liền mạch để thử giọng/nhịp và mức khớp hình; người dùng chọn rồi mới dựng full. Giữ tiếng hiện trường nhẹ và bản voice-only đối chứng; không để thoại nguồn lấn TTS. Khi profile đã được duyệt áp dụng đúng, không hỏi lại. **Đầu ra:** pilot và cấu hình được nghiệm thu.

### Bổ sung v1.3 — Visual Pilot

`qc/g10_pilot_visual_review.md` kiểm biến cố liền mạch có thiết lập bối cảnh → chuyển ý → phản ứng/hành động. Đánh giá wide/medium/close-up, cắt giật, sai chủ thể, cảnh lặp, crop che mặt, liên tục chuyển động và khả năng hiểu câu chuyện **cùng WAV thực**. Một pilot có thể không đủ mọi thể loại; ghi phần chưa bao phủ, không tự nghiệm thu thay người dùng hoặc khởi chạy G11.

## Giai đoạn 11 — Hình ảnh và Full HD

Kiểm black bars, 16:9, ánh sáng, phụ đề cháy. Crop phụ đề không phải phục hồi hình. Chỉ upscale 720p→1080p với Lanczos/unsharp nhẹ nếu cần; NVENC H.264/CPU fallback, tránh ép khi nguồn đã đủ. **Đầu ra:** MP4 1920x1080 hoặc theo phim, kiểm số frame.

### Bổ sung v1.3 — Biến đổi an toàn, không nâng nét giả

Thực thi transform metadata từ EDL được phê duyệt và ghi `timeline/visual_transform_manifest.json` + `qc/g11_frame_comparison.json` cùng before/after evidence. Crop/reframe dựa trên active picture và chủ thể/vật chứng, kiểm vùng mặt/tay, subtitle/text_regions, aspect; cảnh quá tối không tự bị coi là black bar. Phụ đề cháy: lựa chọn giữ/crop có giới hạn/pad/blur có bằng chứng/nguồn sạch do user cung cấp; crop **không phải phục hồi chữ**. `hflip=false` mặc định; chữ, bảng hiệu và phương hướng bị lật sai thì chặn. Upscale hay unsharp/denoise chỉ khi hợp nguồn và được duyệt, 1080p xuất không chứng minh native/AI upscale. Kiểm nén, halo, màu và FFmpeg decode sau áp dụng. Không thay video gốc.

## Giai đoạn 12 — Intro và logo thương hiệu

Intro preset **2 giây** nếu duyệt, title card theo phim và kênh được chọn; TTS bắt đầu sau intro, không mất câu đầu. Chỉ logo PNG được chọn từ thư mục logo của phiên này làm watermark ở vị trí được duyệt; nếu chưa có, đề xuất góc trái, chỉnh opacity/tránh che nhân vật. Không mặc định logo TUA PHIM CÓ GU. **Đầu ra:** bản có intro/logo và composition sửa được.

### Bổ sung v1.3 — Brand Safe Area

`assets/brand_profile.json` chỉ tạo khi G12 được duyệt: `logo_path`, `anchor`, `size_percent`, `opacity`, `safe_margin_percent`, `show_from_s`, `show_to_s`, `intro_enabled`, `intro_duration_s`, `text_watermark` tùy chọn. Logo thuộc kênh đã chọn; overlay **sau transform nội dung** để không bị lật cùng phim, không che mặt/vật chứng/vùng phụ đề cần giữ. Không tự sao chép logo hoặc watermark UNABOMBER mẫu.

## Giai đoạn 13 — Nhạc nền theo cảm xúc

Nhạc không lời nguồn xác minh được, chỉ tải theo phê duyệt; chọn cue theo cảm xúc từ story_map đã được kiểm, crossfade/sidechain ducking để nhạc **không lấn át** giọng; kiểm LUFS, true peak và nghe A/B. **Đầu ra:** nhạc và provenance, MP4 có/không nhạc.

## Giai đoạn 14 — Nghiệm thu toàn bộ MP4

Đối chiếu Review→evidence→beats→WAV→clips→frames; FFprobe, FFmpeg decode, audio spot-check, cảnh chuyển tuyến, crop/logo/nhạc. **Hai kết luận độc lập**: `ĐẠT kỹ thuật` và `ĐẠT biên tập/cốt truyện`. Kiểm story claims với G04, clip vs G08, đúng hành động/nhân vật và causal links/timeline. Còn biến cố trọng yếu sai hoặc clip sai tuyến phải `CẦN SỬA`/`TẠM DỪNG`, không công bố đã hoàn chỉnh. Chưa xem–nghe liên tục thì ghi `CHƯA XÁC MINH`, **không tuyên bố 100%**. **Đầu ra:** MP4, `qc/g14_story_consistency.md`, `qc/QC_REPORT.md` và bảng sửa.

### Bổ sung v1.3 — Ba nhánh QC độc lập

G14 xuất thêm `qc/visual_editing_qc.json` và `qc/visual_editing_qc.md` theo `ISSUE-*`: timestamp, `beat_id/shot_id`, severity, expected/actual, evidence, cách sửa. Ba kết luận `TECHNICAL_STATUS`, `STORY_STATUS`, `VISUAL_EDITING_STATUS` với `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED`; **chỉ cho phép kết luận sẵn sàng xuất bản khi cả ba PASS** và mọi phê duyệt đầy đủ. Visual QC kiểm shot đúng ý đồ, hình đúng diễn biến, nhịp cắt, độ dài cảnh, reuse_reason, continuity, crop mất vật chứng, chữ bị lật ngược, logo che mặt và before/after. Phép đo scene detection phải báo algorithm/threshold, không gọi điểm cảnh là số lần cắt thực. Chưa xem–nghe liên tục ghi `NOT_VERIFIED`, không tự tuyên bố 100%.

## Giai đoạn 15 — Dọn dẹp và lưu trữ

Giữ phim gốc và logo bất biến, MP4 cuối, tài liệu G04/G05, REVIEW, transcript, shot map, nguồn nhạc, report/hash và **gói nguồn** ZIP có thể khôi phục. Xác minh SHA-256. **Không xóa** file nào nếu chưa có danh sách path cụ thể và **phê duyệt xóa riêng**; không xóa ngoài JOB_DIR. Giữ hai video + một bộ tài liệu cần thiết sau khi duyệt. **Đầu ra:** báo cáo dọn và dung lượng.

## Ca học hỏi, không mặc định

Traffic (2000) từng có 51 đoạn REVIEW, 281 beat, 334 shot, Trúc Ly 1.00x, intro 2 giây, MP4 ~23:02; UNABOMBER là ví dụ phương pháp kể chuyện 2 dòng thời gian. Không lấy các số, tên phim, giọng, logo hoặc thời lượng làm mặc định cho phim sau. Kiểm kỹ thuật từng frame không chứng minh chính xác 100% nội dung nếu chưa xem/nghe liên tục.

</details>
