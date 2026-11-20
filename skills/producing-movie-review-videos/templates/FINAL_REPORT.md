# FINAL_REPORT — Nghiệm thu toàn bộ review phim

## Thông tin bản dựng

- Phim gốc: `[tên, năm, path có thật, SHA-256]` — chỉ đọc.
- Máy: `[hostname/deviceId]`, `FILM_DIR`, `JOB_DIR=FILM_DIR\REVIEW_PHIM_WORKSPACE\<project-id>`.
- Logo: `[LOGO_DIR / LOGO_FILE]` hoặc không logo; vị trí/opacity đã duyệt.
- Review được duyệt: `[đường dẫn, hash, số từ, thời lượng ước tính]`.
- MP4 cuối: `[đường dẫn thật, FFprobe duration/resolution/FPS/codec/audio]`.
- Giọng đọc/tốc độ: `[preset/đã duyệt]`, âm hiện trường, intro và nhạc có nguồn dùng hợp lệ.
- Path ghi: `[mọi tệp mới thuộc JOB_DIR; ngoại lệ đã duyệt nếu có]`.
- Phê duyệt: `[G01..G15 đã duyệt theo stage; cài đặt; G15 xóa riêng]`.

## G04 — Nội dung phim đã hiểu và bằng chứng

- `scene_catalog.json`: `[path, số scene indexed, bao phủ đầu/cuối]`.
- Batch ảnh đã được ChatGPT **thực sự xem**: `[số, thời gian, frame ids]`.
- Motion clips/chuỗi khung hình đã xem: `[số, path]`.
- `visual_events.json`, `story_map.json`, `characters.json`, `evidence_index.json`: `[path]`.
- Tuyến thời gian `on_screen_order` và `chronological_events`: `[đã đối chiếu/CHƯA XÁC MINH]`.
- Không lời nhưng quan trọng: `[event_ids đã xác nhận]`.
- Core unresolved claims: `[ids/độ ảnh hưởng]`; gate `FILM_UNDERSTANDING_READY`: `[ĐẠT/BLOCKED]`.

## G05 — Kịch bản REVIEW

- Outline 6 bước có `event_ids`: `[path và trạng thái]`.
- `review_ke_chuyen.txt`, `review_loi_binh_tts.txt`, `review_evidence_map.json`: `[paths]`.
- Claim breakdown: `FILM_FACT`, `CHARACTER_INFERENCE`, `NARRATOR_COMMENTARY`, `EXTERNAL_FACT` `[counts]`.
- Claims `SUPPORTED/QUALIFIED/NEEDS_REVIEW/REJECTED`: `[counts]`.
- `EXTERNAL_FACT` nguồn riêng: `[path/link; chưa xác minh thì loại]`.
- Gate `REVIEW_STORY_READY`: `[ĐẠT / NEEDS_FIX]`; người dùng đã duyệt bản review `[có/chưa]`.

## G06–G08 — Beat, shot và kiểm chứng cảnh

| Hạng mục | ĐẠT/CẦN SỬA/CHƯA XÁC MINH | Bằng chứng |
|---|---|---|
| Nối đủ 100% nội dung REVIEW | | số beat/hash |
| Từng beat có event/scene liên hệ | | beat_evidence_coverage |
| Clip đúng nhân vật/hành động | | shot_map, clip evidence |
| Timeline frame khớp | | frame count + edit decision list |
| Giọng, nhạc, âm hiện trường không lấn | | WAV, loudness A/B, nghe thử |
| Intro/logo | | frame/timestamp PNG |
| 1080p/codec | | FFprobe/decode, crop có mất hình? |
| ZIP/SHA-256/tài liệu nguồn | | hash/tên gói |

## G14 — Đánh giá nội dung và chất lượng MP4 riêng biệt

| Mốc review phút:giây | Beat | Claim REVIEW | Event G04 | Cảnh phim G08 | Lỗi/bằng chứng thiếu | Trạng thái/sửa |
|---|---|---|---|---|---|---|
| [00:00] | [id] | [ý kể] | [EV-...] | [mốc source] | [CHƯA XÁC MINH] | [hành động] |

- Kết luận **ĐẠT kỹ thuật**: `[MP4 decode, khung hình, âm thanh, codec]`.
- Kết luận **ĐẠT nội dung/biên tập**: `[cảnh khớp REVIEW, nhân vật, hành động, nhân quả, tuyến thời gian]`.
- Đã xem-nghe liên tục toàn bộ video chưa: `[có/chưa]`; chưa thì không công bố 100%.
- Có vùng ASR lỗi, image unviewable, crop/subtitle cháy, quảng cáo? `[liệt kê timestamp]`.
- Những gì chưa thể chứng minh: `[CHƯA XÁC MINH với căn cứ]`.
- Các lệnh, log, exit code/hashes: `[chi tiết]`.

## Bàn giao và dọn

- Final MP4 và video nguồn: `[hai path, hash trước/sau]`.
- Bộ tài liệu giữ lại: `[story_map, visual_events, review evidence, transcript, shot_map, QC, source ZIP]`.
- Giấy phép/nguồn nhạc: `[file/URL]`.
- G15: `[danh sách tệp được duyệt xóa riêng; không xóa ngoài JOB_DIR]`.
- Trạng thái cuối: `ĐẠT kỹ thuật / CẦN SỬA / TẠM DỪNG` và **kết luận nội dung riêng**.

## REVIEW_PHIM v1.3 — Nghiệm thu biên tập hình độc lập

| Hạng mục | File bằng chứng | Kết quả |
|---|---|---|
| Source visual profile | `analysis/visual_source_profile.json` | `[verified/unknown]` |
| G04 cỡ cảnh/chuyển động/visual purpose | `analysis/visual_shot_profile.json` + frame/clip | `[coverage]` |
| G06 ý đồ hình từ lời kể | `beats/beat_visual_brief.json` | `[số beat]` |
| G08 hard reject/candidate/alternates | `shots/shot_candidates.json`, `shot_selection_decisions.json` | `[SHOT_SELECTION_READY/BLOCKED]` |
| G09 EDL/pacing/VFR/WAV | `timeline/edit_decisions.json`, `pacing_report.json` | `[FPS, frames, khớp WAV]` |
| G10 pilot kiểm nghe-nhìn | `qc/g10_pilot_visual_review.md` | `[ĐẠT/CẦN SỬA/CHƯA XÁC MINH]` |
| G11 crop/hflip/subtitle/face | `visual_transform_manifest.json`, `g11_frame_comparison.json` | `[before/after]` |
| G12 logo và safe area | `assets/brand_profile.json`, frame sau overlay | `[đúng kênh]` |
| G14 technical / story / visual editing | `qc/visual_editing_qc.json/.md` + `g14_story_consistency.md` | `[3 trạng thái độc lập]` |

Báo `TECHNICAL_STATUS`, `STORY_STATUS`, `VISUAL_EDITING_STATUS`: `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED`, đồng thời danh sách `ISSUE-*` có timestamp, `beat_id`, `shot_id`, severity, expected/actual/evidence/action. Không tự công bố 100% nếu chỉ spot-check. Mọi scene detection phải có algorithm/threshold và giải thích **không phải số cut của editor**. Giữ báo cáo G14 và bảng review → event → shot v1.2 cũ.
