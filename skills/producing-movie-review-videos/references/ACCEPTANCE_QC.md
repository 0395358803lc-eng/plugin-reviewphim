# ACCEPTANCE_QC — Cửa nghiệm thu kỹ thuật, nội dung và hình ảnh

**Không chấp nhận tuyên bố 100%** chỉ từ FFmpeg, ASR, contact sheet chưa thực sự xem hoặc clip chỉ khớp thời lượng. Kết luận `ĐẠT kỹ thuật`, `ĐẠT nội dung/biên tập`, `CHƯA XÁC MINH`, `CẦN SỬA`, `TẠM DỪNG` tách biệt. Mọi gate chỉ xét **sau khi người dùng duyệt riêng đúng Gxx**.

| Gate | Hạng mục | Bằng chứng nghiệm thu |
|---|---|---|
| Q01 / G01 | Phim nguồn | FFprobe, đúng path, duration/timebase/VFR/audio-offset, video giải mã được |
| Q02 / G02 | ASR | Segment, ngôn ngữ, flags ASR lặp, gộp, vượt duration, kiểm nghe những đoạn nghi ngờ |
| Q03 / G03 | Dịch | Tên riêng/timestamp và ngữ cảnh, không tự bịa lời thoại |
| **Q04 / G04** | **FILM_UNDERSTANDING_READY** | scene_catalog index từ đầu tới cuối; contact sheet đã ChatGPT xem, các event then chốt có ảnh/chuỗi clip và transcript phù hợp; story_map + event_ids + report vùng chưa xác minh; không có core unresolved claim bắt buộc |
| **Q05 / G05** | **REVIEW_STORY_READY** | review_outline + văn bản mới + review_evidence_map, sáu bước G05, mọi claim sự kiện trọng yếu có event_ids/sources; không bịa/đánh đồng diễn giải và sự thật |
| Q06 / G06 | Beats | Nối beat khôi phục 100% lời bình TTS đã duyệt; event/source_scene hợp lệ; coverage report |
| Q07 / G07 | WAV/TTS | Giọng đã duyệt, tốc độ, số WAV, phát âm và silence/clipping |
| Q08 / G08 | Clip khớp | Đúng tuyến, actor/action/emotion, chứng cứ visual và clip đã xem; không tự nâng candidate |
| Q09 / G09 | Timeline | Tổng frame đúng, hình liên tục, không hụt audio |
| Q10 / G10 | Pilot | Thử nghe xem, phản hồi/approval profile |
| Q11 / G11 | Full HD | Ratio/codec/frame và giới hạn upscale/crop |
| Q12 / G12 | Intro/logo | Đúng preset được duyệt, không che chủ thể |
| Q13 / G13 | Nhạc/âm thanh | Ducking, nghe A/B, LUFS và true peak, nguồn nhạc rõ |
| **Q14 / G14** | **Cốt truyện và video** | `g14_story_consistency.md`: REVIEW vs G04, clip vs G08, continuity timeline và nhân quả; video decode, xem-nghe liên tục và ghi timestamp chưa khớp |
| Q15 / G15 | Bàn giao/dọn | MP4, ZIP, SHA-256, nguồn gốc và quyền xóa riêng |

## Quy tắc thực thi QC

**Đối chiếu** toàn tuyến giữa lời kể, cảnh phim, bằng chứng G04 và clip G08 trước kết luận đạt nội dung. Không chỉ kiểm codec.

- Khi G04: `INDEXED` chỉ là index; không là `VISUALLY_REVIEWED`, sự kiện không lời đòi chuỗi frame/clip, sai actor cần xác minh thêm, yếu tố phi tuyến phân biệt `on_screen_order` và `chronological_events`. G04 thiếu ảnh có thể xem được → `BLOCKED`, không được viết G05 về mặt sự kiện trọng yếu.
- Khi G05: mọi `FILM_FACT` trọng yếu phải có `event_ids` hợp lệ; `EXTERNAL_FACT` phải có nguồn riêng, chưa xác minh thì loại; `CHARACTER_INFERENCE` không được kể như chứng cứ. `REJECTED` trong review không thể nghiệm thu. Nếu có `NEEDS_REVIEW`, báo rõ cách xử lý; không mặc định thời lượng hoặc gán lời gốc vào văn thuyết minh.
- Khi G06: so khớp chính xác `review_loi_binh_tts.txt` và nối `narration_text`, không sáng tác khi chia beat.
- Khi G08: `VERIFIED_VISUAL` cần chứng cứ nhân vật + hành động và clip/chuỗi xác minh, không đạt chỉ nhờ event_id.
- Khi G14: `ĐẠT kỹ thuật` đòi decode MP4, ffprobe, kiểm frame, audio, song song với `ĐẠT nội dung` đòi diễn biến đúng nhân vật/hành động/quan hệ nhân quả. Nếu chưa xem-nghe liên tục = `CHƯA XÁC MINH`; sai cốt truyện trọng yếu hoặc nhạc lấn át = `CẦN SỬA`/`TẠM DỪNG`, **dừng xuất bản**.

## Kiểm tra kỹ thuật tham khảo

- `ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,nb_frames -of json "<FINAL_MP4>"`; `ffmpeg -v error -i "<FINAL_MP4>" -f null NUL` (được phép sau khi G14 duyệt).
- So beat count với WAV và clip coverage, kiểm điểm nối, đầu/cuối intro 2 giây nếu preset đó được duyệt. Tiếng lời kể tham khảo -17 đến -19 LUFS và nhạc -30 đến -38 LUFS, nhưng phải nghe vì số đo không thay chứng cứ.
- Kiểm phụ đề cháy/crop: crop là loại khỏi khung nhìn, không phục hồi; nguồn 720p upscale không là native 1080p.
- Video gốc, logo gốc bất biến, file được lưu trong `JOB_DIR`, không xóa; G15 yêu cầu SHA-256/ZIP và **phê duyệt xóa riêng**.

## Tình huống hồi quy cần giữ

1. Đa ngôn ngữ và thoại sai timestamp → cờ lỗi, không đoán cảnh.
2. Beat nói nhân vật A mà video là nhân vật B → `REJECTED`.
3. Phim im lặng có hành động quan trọng → G04 ghi nhận event.
4. Giọng Trúc Ly 1.00x dài hơn dự đoán → theo WAV thật.
5. Giảm intro 5s→2s ở 25FPS → 50 frame, không mất câu đầu.
6. Nhạc lấn lời → sidechain, nghe lại và kiểm kết quả.
7. Đề nghị dọn → kiểm file thật/hash, xin duyệt danh sách xóa riêng.

## Q Visual v1.3 — Nghiệm thu cảnh, nhịp và EDL

- **Q01:** `visual_source_profile.json` có nguồn/hash, frame samples, letterbox/subtitle theo timestamp, cảnh tối không tự crop.
- **Q04:** `visual_shot_profile.json` với scene/actor, `shot_type`, camera motion chỉ VERIFIED sau chuỗi/clip, emotion observation tách suy luận, motion UNKNOWN nếu thiếu chứng cứ.
- **Q05/Q06:** sáu bước REVIEW giữ nguyên, `visual_intent_hints` không phát sinh fact, các beat ghép chính xác 100% TTS; visual brief chỉ là định hướng hình.
- **Q08:** `SHOT_SELECTION_READY` kiểm hard reject → rank, nhiều ứng viên với provenance, visual verified, không giả clip; không cho G09 nếu chưa được user phê duyệt riêng.
- **Q09:** EDL frame exclusive đúng WAV, FPS rational, Remotion/FFmpeg từ cùng nguồn, continuity không đảo nhân quả, `reuse_reason`, tránh shot gần trùng. Không hardcode 2,04 giây/shot.
- **Q10:** pilot trực tiếp xem-nghe, wide→medium→close-up nếu hợp, nhân vật/hành động và crop hợp lý; lưu `g10_pilot_visual_review.md`.
- **Q11/Q12:** `hflip=false` mặc định, crop/reframe không mất face/vật chứng, subtitle không bị gọi là khôi phục, image evidence before/after, logo đặt sau transform và không che nhân vật.
- **Q14:** `qc/visual_editing_qc.json` và `.md`, issue ID/time/shot/evidence; `TECHNICAL_STATUS`, `STORY_STATUS`, `VISUAL_EDITING_STATUS` riêng, enum `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED`. Sai actor/action, mất manh mối do crop, continuity làm hiểu sai hay chữ ngược làm sai thông tin là `BLOCKING` và dừng xuất bản. Chỉ **PASS cả ba** + đủ phê duyệt mới được gọi hoàn tất. Chưa xem-nghe liên tục ghi `NOT_VERIFIED`, không tuyên bố 100%.
- **Scene detection**: mọi số thay đổi hình phải công bố algorithm/threshold/sampling và không nhầm với cut thực của editor. Chỉ là tín hiệu tìm vùng để xem, không thay quan sát visual trực tiếp của ChatGPT.

### Ca minh họa phát hiện lỗi

`ISSUE-*` có `severity`, `timeline_in_frame`, `timeline_out_frame_exclusive`, `beat_id`, `shot_id`, `check`, `expected`, `actual`, `evidence_refs`, `status`, `action`. Một frame tìm khớp phim gốc chưa chắc cùng event/đúng người; giữ `CANDIDATE` tới khi nhìn clip/chuỗi. Khi thiếu file hoặc hash mismatch → `NEEDS_REVIEW/BLOCKED`, không tự fake pass. Phim nguồn 1080p không phải bằng chứng đã upscale; logo của kênh A không tự mang sang dự án kênh B. Không có OpenCV/Qwen-VL thì dùng FFmpeg và ChatGPT trực tiếp nếu có kênh ảnh thực.
