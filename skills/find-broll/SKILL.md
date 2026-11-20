---
name: find-broll
description: Use when REVIEW_PHIM needs B-roll or inserts to support the narration, find timestamped source footage, verify provenance, vet shots, maintain B-roll approvals or place cutaways in G06, G07, G08 or G09.
---

# REVIEW_PHIM — Find B-Roll

Phỏng theo [find-broll](https://github.com/gitethanwoo/video-editing/tree/main/skills/find-broll) của Ethan Woo (MIT, phương pháp có ghi công B-Roll Finder của Louise De Sadeleer). Đây là **lập kế hoạch và kiểm duyệt nguồn**, không là giấy phép tải/phát lại phim hoặc làm biến đổi sự thật. Khi chỉ làm review phim, **ưu tiên footage phim gốc đã được người dùng chọn**; B-roll ngoài là phương án có điều kiện.

## Quy trình theo nghĩa lời kể, không theo từ khóa đơn

1. Đọc bản REVIEW/beat đã được duyệt đầy đủ; mỗi beat gắn `beat_id`, `narration_text`, `event_ids`, `actor`, `action`, `emotion`, `anchor_word` và `narration_anchor_s` nếu có timestamp thật.
2. Ưu tiên scene/shot có bằng chứng trong `scene_catalog`, `visual_events`, `shot_candidates`; đặt nguồn `source_kind=ORIGINAL_FILM`. Không dùng cảnh sai tuyến để lấp khoảng trống.
3. Khi thật sự thiếu hình: lập đề xuất `SOURCE_FILM_ALTERNATIVE`, `USER_PROVIDED`, `LICENSED_ARCHIVE`, `OFFICIAL_SOURCE`, `ORIGINAL_GRAPHIC`, hoặc `NONE`. Không tự tải từ web, không tự sử dụng ảnh có watermark hoặc nguồn không rõ quyền. Nếu cần tải, xin duyệt nguồn, URL, phạm vi, quyền sử dụng và vị trí lưu trong JOB_DIR trước.
4. Gắn mốc đặt sau **từ/cụm từ cần minh họa** (nếu word timestamps thực tế hỗ trợ); không mặc định lệch 0,2–0,5 giây thành luật cứng. Phải phân biệt `source_in/out_s` và `timeline_in/out_frame`.
5. Cho ChatGPT kiểm chứng contact sheet và clip/cấu trúc chuyển động thực; ChatGPT quyết định cuối theo actor/action/storyline, không để CLIP/vision tự chốt. Chỉ `APPROVED` mới vào EDL của G09.

## Manifest đầu ra

`shots/broll_plan.json`, `shots/broll_source_manifest.json`, `shots/broll_placement_decisions.json`, `qc/broll_qc.md` trong JOB_DIR; giữ tương thích `shot_map.csv` và `timeline/edit_decisions.json`. Mỗi item: `broll_id`, `beat_id`, `anchor_text`, `anchor_time_s`, `source_kind`, `canonical_url_or_source_path`, `source_sha256`, `source_start_s/end_s`, `timeline_start_frame/end_frame_exclusive`, `rights_note`, `source_provenance`, `visual_purpose`, `evidence_ref`, `status` (`PLANNED/SOURCED/APPROVED/PLACED/DROPPED`), `approval_id`.

QC trước sau dựng: kiểm mốc không đi trước lời kể, chủ thể tồn tại sau crop, đúng asset, không nháy frame, âm thanh ngoài bị tắt nếu chưa duyệt trộn, overlay/caption dễ đọc, đủ quyền/tác giả và không nhân đôi beat sai. Thiếu giấy phép hoặc bằng chứng quan trọng: `BLOCKED/NOT_VERIFIED`; sai clip: `NEEDS_FIX`; chỉ công việc được phê duyệt, kiểm chứng đạt mới `PASS`. Không bao giờ coi media tìm thấy trên mạng là được phép sử dụng lại.
