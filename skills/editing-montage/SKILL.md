---
name: editing-montage
description: Use when REVIEW_PHIM needs montage, J-cuts, L-cuts, match cuts, continuity, visual rhythm, edit decisions, EDL and montage QC in G05, G06, G08, G09, G10 or G14.
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



# REVIEW_PHIM — Editing Montage

Phỏng theo [editing-montage](https://github.com/calesthio/generative-media-skills/tree/main/skills/production/post-production/editing-montage) (MIT); thực hiện trong workflow G01–G15, không độc lập vượt phê duyệt. Không cần model/SDK riêng: đây là kỹ năng **quyết định biên tập**, không phải engine dựng phim.

## Quy tắc biên tập

- Ưu tiên đúng diễn biến/nhân vật/hành động/vật chứng và cảm xúc, sau đó mới đến nhịp, chuyển cảnh và hiệu ứng. Không chọn clip đẹp nhưng sai câu chuyện.
- Mỗi shot phải phục vụ `orient/reveal/prove/reaction/intensify/bridge/breathe/close`. Nếu không chứng minh được vai trò: cân nhắc bỏ, thay hoặc `NEEDS_REVIEW`.
- `J-cut`: âm thanh của cảnh/ý sau xuất hiện trước điểm cắt hình; `L-cut`: âm thanh của cảnh/ý trước còn tiếp tục qua điểm cắt hình. Không dùng thay đổi audio nếu chưa được duyệt và kiểm nghe A/B.
- `match_cut`: nối hành động/bố cục/hướng chuyển động có ý nghĩa; tránh nối sai nhân quả. `cutaway`: che bước nhảy thời gian khi nguồn có căn cứ; `montage`: phải thể hiện diễn tiến, tương phản hoặc tích lũy, không ghép cảnh ngẫu nhiên.
- Duy trì eyeline, screen direction, độ liên tục hành động/vật thể, chiều thời gian, âm nền. Không lật hình làm đảo văn bản. Nhịp nhanh không tự động tốt; đánh giá độ phức tạp thông tin và thời gian đọc subtitle.
- Đề xuất pacing `SLOW/NORMAL/FAST/ADAPTIVE` theo cảm xúc và cấu trúc, không áp dụng duration hay BPM mặc định; so sánh hình-câm, audio-only (nếu có file ChatGPT nghe được), caption-only và full-view khi bằng chứng đủ.

## Tích hợp theo gate

G05: gợi ý nhịp kể mà không thay công thức REVIEW 6 bước. G06: bổ sung visual intent vào beat; không đổi chữ. G08: chấm shot theo nội dung và tính liên tục trước khi rank thẩm mỹ. G09: ghi `timeline/edit_decisions.json` (nguồn sự thật) + EDL với frame nguyên, source/output timestamp độc lập; A06 Remotion dựng theo EDL, A01 FFmpeg fallback khi được duyệt. G10: pilot kiểm continuity và audio. G14: QC story + technical + visual editing độc lập, không tự coi bản dựng đã được người dùng duyệt.

## Quyết định & kiểm chứng

Mỗi edit: `edit_id`, `beat_ids`, `shot_ids`, `source_in_s`, `source_out_s`, `timeline_in_frame`, `timeline_out_frame_exclusive`, `cut_type`, `j_l_audio_overlap_frames`, `editorial_purpose`, `continuity_check`, `narration_anchor`, `evidence_ref`, `approval_id`, `qc_status`.

Nếu nhịp tốt nhưng sai actor/action/storyline thì `NEEDS_FIX`, không phải PASS. Thiếu bản nghe thì `NOT_VERIFIED` phần âm thanh; issue sửa cần nút phê duyệt riêng. Giữ toàn bộ nguyên tắc GPU-FIRST, workspace cục bộ, microtask QC `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED` từ skill chủ.

</details>
