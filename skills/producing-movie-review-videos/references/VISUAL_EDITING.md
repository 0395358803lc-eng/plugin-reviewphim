# VISUAL_EDITING — REVIEW_PHIM v1.3.0: nhịp dựng, EDL, transform và QC

**Chỉ dùng sau phê duyệt giai đoạn G08/G09/G10/G11/G12/G14 tương ứng.** Đây là tài liệu điều phối của ChatGPT, không phải một AI editor chạy tự động. Không cài FFmpeg, không gọi Remotion và không sửa nguồn chỉ nhờ đọc tài liệu. Ưu tiên `SESSION_ORCHESTRATION.md`, `EVIDENCE_SCHEMA.md`, `SCENE_MATCHING.md` và `ACCEPTANCE_QC.md`.

## 1. Dữ liệu vào/ra và giới hạn

- **G08:** `shot_map.csv` (cột cũ giữ), `shot_candidates.json`, `shot_selection_decisions.json`, `shot_evidence.json` và gate `SHOT_SELECTION_READY`.
- **G07:** WAV đã nghiệm thu thực với độ dài từng beat, `voice_status.json`, sample rate/time offset; lời kể không bị thay vì muốn đạt độ dài video.
- **G06:** `beats.json` / `beat_visual_brief.json`, gồm `pacing_intent`, `visual_intent`, `continuity_requirement`, ý đồ chủ thể/cỡ cảnh. Scene/event/evidence của G04 xác minh hash nguồn.
- **G09 đầu ra:** `timeline/edit_decisions.json` EDL canonical, `timeline/timeline.json` tương thích, `timeline/pacing_report.json`, Remotion composition và draft MP4 đúng phạm vi phê duyệt.
- **G11 đầu ra:** `timeline/visual_transform_manifest.json`, `qc/g11_frame_comparison.json`, before/after có timecode và MP4; không thay source.
- **G12 đầu ra:** `assets/brand_profile.json`, bản xem trước thương hiệu. Logo của kênh khác hoặc UNABOMBER mẫu không tự sử dụng.
- **G14:** `qc/visual_editing_qc.json`, `.md` cùng `g14_story_consistency.md` và `QC_REPORT.md` cũ.

Thời gian nguồn là **giây của phim gốc**, timeline và voice là thời gian/khung hình của bản dựng. Clip từ nguồn khác chỉ khi người dùng cho phép và có provenance riêng. Đường dẫn output tương đối `JOB_DIR`; phim, logo gốc chỉ đọc. Không chuyển mặc định sang C:.

## 2. G09 — Nhịp hình (editorial pacing) quyết định theo nội dung

**Quy tắc tạo nhịp:** đầu tiên bám nội dung và WAV, sau đó chọn điểm cắt/góc hình giúp người xem hiểu cảnh; không chạy theo mục tiêu số cut/phút. Clip cận mặt có thể kéo dài khi một phản ứng cần thời gian. Tránh cắt giữa hành động nhân quả, tránh chuyển tuyến không có dấu hiệu. Ý đồ `SLOW`, `NORMAL`, `FAST`, `ADAPTIVE` chỉ là phân loại; KHÔNG ép 2,04 giây/cut, 24 fps hoặc 3 shot/beat. 2,04 và 18,71 chỉ là thông số quan sát video UNABOMBER mẫu.

Dựa trên `preferred_shot_types`: khi cần thiết lập bối cảnh dùng wide/establishing; giải thích/đối thoại ưu tiên medium và shot-countershot đúng nhân vật; diễn biến cảm xúc ưu tiên close-up có bằng chứng phản ứng; hành động/vật chứng dùng detail/action nhưng không đảo thứ tự. **Continuity requirement**:

- `MUST_PRESERVE_ACTION`: giữ một chuỗi hành động dễ theo dõi; không nhảy tới hậu quả trước nguyên nhân, không chia/cắt khiến diễn biến sai.
- `CAN_INTERCUT`: có thể xen hai tuyến đã kiểm khi ý kể phù hợp, không lẫn cảnh quá khứ/hiện tại.
- `ESTABLISH_THEN_REACT`: bối cảnh/nhân vật trước rồi tới phản ứng quan trọng, không đảo logic.

Cảnh giống nhau nối tiếp (same source window hoặc near-duplicate) được cảnh báo; không tự xóa khi đang hồi tưởng có `reuse_reason`. Nếu thời lượng WAV dài hơn clip tốt, dùng ứng viên dự phòng cùng sự kiện, giữ cận cảnh lâu hợp lý hoặc báo `NEEDS_REVIEW` — không kéo clip sai tới đủ tiếng.

## 3. G09 — EDL canonical, kiểm frame/time thật

**EDL duy nhất:** `timeline/edit_decisions.json` là nguồn duy nhất cho dựng Remotion và FFmpeg fallback; không dùng hai bản quyết định cắt riêng. `timeline/timeline.json` là view/backward compatibility. Mọi edit có `edit_id`, `shot_id`, `beat_ids`, `source_scene_id`, `source_in_s`, `source_out_s`, `timeline_in_frame`, `timeline_out_frame_exclusive`, `transition`, `continuity_id`, `reuse_reason`, `transform`, `source_fps` nếu biết, output rational `output_fps_num/output_fps_den`.

**Validate trước khi render:** `0 <= source_in_s < source_out_s <= source_duration_s`; timestamps hữu hạn, không NaN/Infinity; `timeline_in_frame >= 0`, `timeline_out_frame_exclusive > timeline_in_frame`; `duration_frames = out_exclusive - in`; source và timeline không tráo nhau; ID có provenance. Frame positions nguyên; FPS rational > 0, theo người dùng/dự án, không tự ép 24/25. Với 25 fps, ví dụ frame 1500→1615 là 115 frame = 4,6 giây, không bao gồm frame cuối.

Dùng WAV thật đã được nghiệm thu làm time anchor. Tính khoảng nghỉ đã duyệt và intro nếu có; đồng bộ VFR bằng timestamp nguồn/PTS và video output, không phép chia frame máy móc từ FPS nguồn trung bình. Bật `transition` CUT hoặc hiệu ứng có ý nghĩa theo quyền duyệt; không tạo frame đen ngoài ý đồ. Kiểm tổng audio/EDL đầu-cuối, không để thiếu hoặc đè tiếng kể. **Không chạy G09 nếu G08 chưa `SHOT_SELECTION_READY` hoặc G09 chưa được người dùng duyệt riêng.**

## 4. G11 — Safe visual transformations

Mỗi edit có transform metadata, mặc định `{ "hflip": false, "crop_mode": "NONE", "scale_mode": "FIT", "position_x": 0.5, "position_y": 0.5 }`. G09 ghi dự kiến, **G11 mới** áp dụng đúng phạm vi người dùng duyệt và phản hồi `requested_transform`, `applied_transform`, ảnh before/after và timestamp. Không ghi đè frame nguồn.

**Letterbox/black bars:** dùng FFprobe + ảnh nhiều thời điểm, phân biệt dark scene với dải đen thật; khung hình tối không phải lý do auto crop. Giữ aspect gốc khi resize; không biến dạng mặt để đủ 16:9.

**Crop/reframe:** kiểm face, tay, nhân vật, vật chứng, text_regions, hướng di chuyển trước/sau; crop làm mất đầu/đồ vật quan trọng hoặc phần cần chứng minh là `NEEDS_FIX`, trọng yếu là `BLOCKING`. Tính pixel/relative coordinate trên active picture, tránh phóng quá mức tạo mờ/halo. Lưu version, timecodes, border estimate, kết quả QC.

**Burned subtitle:** phụ đề cháy trong video gốc có thể giữ nguyên; hoặc crop giới hạn; pad/blur nếu không gây xung đột; hoặc dùng nguồn sạch được người dùng cung cấp. Không tuyên bố xóa/khôi phục subtitle bằng crop; không auto làm biến mất cả môi/mắt/tay để che dòng chữ. `subtitle_regions` phải theo thời gian khi chỉ xuất hiện ở một số cảnh.

**Horizontal mirror:** mặc định `hflip=false`/OFF. Lật ngược chữ/bản đồ/biển hiệu, hướng chạy, tay cầm súng, vị trí chấn thương hoặc địa điểm có thể làm sai thông tin. Nếu user duyệt flip cụ thể, kiểm chuỗi hình, nhân vật và text; chữ bị ngược nguy hiểm → dừng hoặc chọn shot khác, không cố dùng chỉ vì video UNABOMBER mẫu lật. **Branding after content transform:** chồng logo/watermark **sau** flip/crop nội dung, không để thương hiệu bị đảo.

**Chất lượng:** không hứa native 1080p hay AI upscale chỉ vì xuất 1920×1080. Chỉ upscale khi nguồn thấp hơn và có phê duyệt; Lanczos/unsharp/denoise nhẹ theo cảnh, so sánh before/after, chặn oversharpen/halo, thay đổi màu/luma bất thường, bitrate quá thấp. Kiểm decode MP4, FPS, số frame cuối, so nguồn tại timecode.

## 5. G10 — Pilot visual review

Pilot đủ có bối cảnh + chuyển ý + một hành động hoặc cảm xúc, đi cùng WAV thực và không xóa nguồn. `qc/g10_pilot_visual_review.md` có bảng: timestamp, beat, `visual_intent`, shot minh họa, face/action continuity, pacing, cận/trung/toàn, audio sync, crop/subtitle, `ĐẠT/CẦN SỬA/CHƯA XÁC MINH`. Kiểm xem-nghe thực; không báo PASS chỉ vì render exit 0. Nếu style/profile được duyệt trước đó cho đúng dự án, tái dùng theo hash; không bắt user duyệt lại vô lý.

## 6. G12 — Branding safe area

`assets/brand_profile.json` là profile theo user/kênh đang chọn với `logo_path`, `anchor`, `size_percent`, `opacity`, `safe_margin_percent`, `show_from_s`, `show_to_s`, `intro_enabled`, `intro_duration_s`, `text_watermark` optional. Không lấy watermark video mẫu, không tự thêm 2 logo. Overlay logo sau hflip/reframe, tránh che mặt, subtitle cần giữ, bằng chứng và vùng hành động. So ảnh có/không overlay trong pilot; đổi vị trí/độ đậm theo phê duyệt.

## 7. G14 — Three-axis QC, phát hiện khác xác nhận

**Ba trạng thái độc lập:** `TECHNICAL_STATUS`, `STORY_STATUS`, `VISUAL_EDITING_STATUS` nhận `PASS`, `NEEDS_FIX`, `NOT_VERIFIED`, `BLOCKED`. Không gộp `PASS` kỹ thuật thành `PASS` nội dung. Chỉ tuyên bố đủ điều kiện xuất bản khi **cả ba PASS**, đầy đủ gate và phê duyệt. Chưa xem-nghe liên tục thì `NOT_VERIFIED`, không được tự tuyên bố 100%.

- **Technical**: ffprobe/decode, duration, fps, VFR audio sync, black frames, quality compression/blur, codec, crop, logo/branding.
- **Story**: lời REVIEW đúng sự kiện/nhân vật/action, thứ tự nguyên nhân–kết quả và tuyến, voice beat khớp evidence, clip được ChatGPT xem.
- **Visual editing**: shot đúng `visual_intent`, cỡ cảnh, pacing, chuyển wide→medium→close-up có lý do, continuity, hành động không bị đảo, near-duplicate/reuse_reason, sắc độ giữa shot, crop che mặt/vật chứng, hflip làm chữ ngược, watermark che nội dung.

Ghi issue trong `qc/visual_editing_qc.json` và bảng `.md`: `issue_id`, `severity=INFO/WARNING/NEEDS_FIX/BLOCKING`, `timeline_in_frame`, `timeline_out_frame_exclusive`, `beat_id`, `shot_id`, `check`, `expected`, `actual`, `evidence_refs`, `status`, `action`. `BLOCKING` cho wrong actor/action, continuity đảo nhân quả, crop mất manh mối hoặc chữ đảo làm sai thông tin. Cảnh lặp có `reuse_reason` rõ không auto fail. Chỉ gán `VERIFIED_VISUAL` khi đã xem ảnh/clip đủ, không dùng cosine thay.

**Scene detection không đồng nghĩa editorial cut**: nếu dùng FFmpeg/PySceneDetect báo algorithm, threshold, sampling, số points phát hiện, denominator (video duration) và giải thích có thể bao gồm cắt máy gốc/false positives. Với UNABOMBER mẫu, 415 vs 694 points không chứng minh chính xác từng lần người dựng cắt. Ngoại suy nhịp tham khảo phải ghi tính không chắc chắn.

## 8. Failure, recovery và điều kiện dừng

- Missing file/hash drift → `NEEDS_REVIEW` hoặc `BLOCKED`, không tự tái tạo dữ liệu cũ/trả VERIFIED.
- Mất kết nối G08/G09 → đọc approvals+source SHA-256+checkpoint, chỉ resume phần được duyệt; không báo đã xem clip khi thực tế chỉ có tên file.
- Candidate không khớp actor/action/storyline → hard reject và giữ beat uncovered; không nhồi footage sai vào timeline.
- Motion chưa xác minh → `CANDIDATE`, yêu cầu clip/chuỗi frame; không gán xác suất cao thành kết luận.
- Crop/subtitle gây mất bằng chứng hoặc hflip làm sai chữ → `BLOCKING`, đề xuất giữ bản không transform/chọn scene khác hoặc xin user phê duyệt cách xử lý; không tự vượt gate.
- Bất cứ Gxx kết thúc đều báo file thực, kiểm chứng, công việc tồn đọng và **dừng**, trình kế hoạch giai đoạn kế để user phê duyệt riêng. P5 pilot trên UNABOMBER là tác vụ riêng sau khi user cho phép; cập nhật plugin không cấp quyền tự chạy phim.

## 9. Bảng nghiệm thu theo chủ thể (case examples)

| Sự cố | Tín hiệu | Kết luận tối thiểu |
|---|---|---|
| Beat Ted nhưng shot Henry | sai actor trọng yếu | `REJECTED`, không rank thẩm mỹ |
| Cảnh trao vật chỉ có 1 frame | motion_verification UNKNOWN | CANDIDATE, cần clip |
| Phim tối bị crop | detect không xác minh black bars | NEEDS_FIX, kiểm lại mẫu |
| Số cut/phút tăng nhưng sai tuyến | visual pace đẹp mà story sai | STORY/EDITING BLOCKED |
| Two shots near-duplicate | cùng nguồn, mục đích khác | cảnh báo, dùng `reuse_reason` nếu có ý đồ |
| hflip đảo chữ cảnh nguồn | chữ/bản đồ sai chiều | BLOCKING nếu ảnh hưởng ý nghĩa |
| Thời gian output vượt WAV | timeline đen hoặc chưa đủ video | NEEDS_FIX, tái lập EDL |
| G14 chỉ spot-check | chưa xem/nghe liên tục | NOT_VERIFIED |
| Video nguồn 1080p nhưng xuất 1080p | chỉ container size | không được gọi upscale AI/native |
| Logo nằm trên mặt nhân vật | overlay che chứng cứ | NEEDS_FIX; logo sau transform |
