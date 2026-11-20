---
name: analyze-video-editing
description: Use when REVIEW_PHIM needs to reverse-engineer reference edits or inspect source video shots, cuts, movement, typography, music, sound and pacing with timecoded evidence in G04, G08, G10 or G14.
---

## Production First v1.3.26

Khi gói đã duyệt chọn `PRODUCTION_FIRST_V1325`, đọc
[chính sách chuẩn](../producing-movie-review-videos/references/PRODUCTION_FIRST_AUTONOMOUS_V1325.md)
và [khôi phục v1.3.26](../producing-movie-review-videos/references/PRODUCTION_RELIABILITY_V1326.md).
Dùng `project_flow_v1325.py`; không lấy QC=PASS, cổng duyệt hay vòng sửa lỗi
thẩm mỹ trong nhánh Legacy dưới đây làm điều kiện chuyển bước.
Chỉ dừng khi thiếu đầu ra dùng được, quyền hoặc đầu vào thiết yếu.

## Legacy — chỉ điều phối gói cũ

<details><summary>Quy tắc lịch sử</summary>



# REVIEW_PHIM — Analyze Video Editing

Nguồn phương pháp: Ethan Woo, [analyze-video-editing](https://github.com/gitethanwoo/video-editing/tree/main/skills/analyze-video-editing), MIT. Đây là bản tích hợp **phương pháp và output contract**, không phải khẳng định đã đóng gói `video_analyzer.py`, `audio_listener.py` hay các dependencies của chúng.

## Thứ tự ưu tiên

Áp dụng tuyệt đối skill `producing-movie-review-videos` và `references/EDITORIAL_SKILLS_INTEGRATION.md`: Gxx.Mnn/Bxxx, xin phê duyệt trước mỗi task, GPU-FIRST với hạng mục phù hợp, chỉ dùng JOB_DIR, không tải/cài/tạo file ngoài phê duyệt. G04/G08/G10/G14 đều phải tự nghiệm thu bằng chứng trước khi trình công việc kế. Có xung đột thì hợp đồng REVIEW_PHIM thắng. Phân tích video mẫu bên ngoài chỉ khi user cung cấp hoặc cho phép truy cập; không tự tải từ web.

## Phân tích nguồn thành ba lớp

1. `MEASURED`: FFprobe, SHA-256, frame/timebase, shot-change candidates, độ dài cut, mức âm, khoảng yên lặng, subtitle cue; ghi tham số thuật toán và sai số.
2. `OBSERVED`: ChatGPT trực tiếp xem frame/strip/clip đã chuyển được; ghi shot_type (wide/medium/close/insert), actor, action, text, camera_motion khi có **chuỗi frame hoặc clip**; không gán 'đã xem' cho metadata.
3. `INTERPRETED`: vai trò biên tập: hook, reveal, proof, reaction, transition, pace, căng thẳng, giải tỏa. Mọi kết luận liên kết với hai lớp trên; thiếu bằng chứng là `NOT_VERIFIED`.

## Microtask theo Gxx

- G04: xây scene/shot catalog qua A01, A03, A08; tạo timestamped contact sheet, event strips, timeline hình và audio. Không nhầm scene detector với số cut thực.
- G08: phân tích kỹ thuật của video review mẫu được phép xem, so sánh với phim gốc và beat; lưu dấu cắt, shot length, camera, text/subtitle, âm thanh. Tách nội dung phim gốc và bản dựng tham chiếu.
- G10: phân tích pilot trên đoạn liên tiếp, đối chiếu narration WAV với visual, J/L cut/nhạc; không tự sao chép style, chữ hoặc thời điểm cut của mẫu.
- G14: đối chiếu báo cáo kỹ thuật + trực tiếp xem hình/clip + nghe audio người dùng upload; chưa nghe được không ghi PASS âm thanh.

## Đầu ra sau task được duyệt

`analysis/editorial_reference_probe.json`, `analysis/editorial_reference_shots.jsonl`, `analysis/editorial_reference_timeline.md`, `analysis/editorial_reference_contact_sheet.jpg`, `analysis/editorial_reference_pacing.json`, `qc/editorial_analysis_qc.md` (đường dẫn trong JOB_DIR; không ghi đè G04/G08 hiện có). Bảng timeline tối thiểu: `shot_id`, `source_sha256`, `source_in_s`, `source_out_s`, `cut_type`, `shot_type`, `camera_motion`, `dialogue_ref`, `sound_transition`, `text_overlay`, `editorial_function`, `evidence_paths`, `confidence`, `verification_status`. Lưu output mẫu chỉ khi thực sự được tạo, không bịa file.

Trích riêng cửa sổ audio khi cần; vì ChatGPT không nghe audio trên Remote Desktop Commander, yêu cầu upload qua chat sau phê duyệt theo `APPROVAL_TRANSLATION_AUDIO.md`. Tách đo độ ồn/spectrogram và nhận định đã nghe. Mọi task báo `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED` + bằng chứng, vấn đề sửa phải duyệt riêng.

</details>
