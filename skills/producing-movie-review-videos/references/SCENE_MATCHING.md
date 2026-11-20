# SCENE_MATCHING — G08 đúng phim, đúng nhân vật, hành động và cảm xúc

**Mấu chốt:** khớp ngữ nghĩa không đồng nghĩa khớp timestamp/ASR. G08 phải **tái dùng** `scene_catalog.json`, `visual_events.json`, `evidence_index.json`, `story_map.json` từ G04, không nghiên cứu lại toàn bộ phim nếu dữ liệu đã xác minh và hash nguồn trùng. Đọc `EVIDENCE_SCHEMA.md` và `FILM_UNDERSTANDING.md` trước thao tác.

## Với mỗi beat

- Beat: `beat_id`, `paragraph_id`, `narration_text`, `event_ids`, `storyline`, `actor`, `action`, `emotion`, `intent`.
- Ứng viên shot: `src_in_s`, `src_out_s`, `source_scene_id`, `event_id`, `actor_evidence`, `action_evidence`, `visual_evidence`, `transcript_evidence`, `frame_sheet`, `match_status`.
- `match_status` chỉ nhận `VERIFIED_VISUAL`, `CANDIDATE`, `NEEDS_REVIEW`, `REJECTED`. `scene_status=INDEXED` không chứng minh nhân vật/hành động. Event ID tồn tại không đủ nâng candidate thành VERIFIED.

## Quy trình chọn cảnh

1. Đọc beat và các event đã xác minh: ai, làm gì, bối cảnh, thời kỳ, đoạn lời kể muốn khán giả nhìn thấy điều gì. Đối chiếu `story_map` trước khi chọn clip, đặc biệt phim có quá khứ/hiện tại.
2. Truy vấn scene catalog lấy **nhiều candidate cùng tuyến** và timestamp nguồn; kiểm bản đồ evidence, nhìn ảnh/clip thật. ASR có thể lặp/sai mốc; transcript chỉ là chỉ dẫn tìm vị trí.
3. Nếu G04 chưa xác minh chuyển động, mở rộng 3–n frame hoặc clip ngắn để biết actor, action, object, reaction, causal order. Cảnh lời về hậu quả nên ưu tiên hậu quả/biểu cảm được xác minh, không lấy hành động ngẫu nhiên.
4. Sai nhân vật hoặc sai hành động cốt lõi → `REJECTED` ngay; không lấy cảnh sai tuyến để lấp thời lượng. Đúng nhân vật → đúng hành động/sự kiện → đúng nhịp cảm xúc → đúng tuyến/timeline rồi mới xét thẩm mỹ.
5. Kiểm src_in/out, tránh quảng cáo/trailer/phụ đề cháy không hợp, cảnh bị lặp vô lý, shot không đủ thời gian, tài liệu chứng cứ thiếu đường dẫn. Nếu không đủ bằng chứng → `NEEDS_REVIEW`, không tự sửa lời REVIEW để hợp clip sai.
6. Dùng WAV thật đã duyệt, không ép 1–3 shot/beat. Kiểm xem clip **cùng lời thuyết minh**, nếu người xem không liên tưởng đúng nội dung thì đổi shot.
7. Ghi `shots/shot_map.csv`, `shots/shot_evidence.json` có nguồn frames/clips cụ thể và `match_status`, đánh dấu các beat orphan/thiếu clip; không dùng confidence tự chấm thay evidence.
8. Kết thúc G08 báo `VERIFIED_VISUAL / CANDIDATE / NEEDS_REVIEW / REJECTED`, đường dẫn shot_map, clip kiểm chứng và các lỗi còn lại. Không tự khởi chạy G09.

## Tình huống ưu tiên kiểm kỹ

- Hook, cao trào, kết, thoại nêu rõ hành động hoặc chủ thể.
- Chuyển nhiều nhân vật/tuyến giữa cùng đoạn, hồi tưởng, split-screen, cảnh nhiều người giống nhau.
- Transcript gộp dài, mất âm, VAD yên lặng nhưng màn ảnh có hành động; những tình tiết không lời.
- Cảnh chỉ có một ảnh đại diện nhưng REVIEW khẳng định hành động đang diễn ra.
- `CANDIDATE` và `NEEDS_REVIEW`/khung hình mờ hoặc có phụ đề tràn khung.

**Nếu không đủ bằng chứng** tuyệt đối không tuyên bố khớp 100%. Dựng nháp được phép cho QC, nhưng **dừng xuất bản** khi còn lỗi cốt truyện trọng yếu, clip sai tuyến, sai nhân vật hoặc hành động.

Ví dụ schema (không phải dữ liệu thật):

| beat_id | storyline | actor | action | src_in_s | src_out_s | match_status | evidence |
|---|---|---|---|---:|---:|---|---|
| 17 | Điều tra | A | Vào phòng thẩm vấn | 1250.0 | 1255.2 | CANDIDATE | frame và transcript chưa kiểm motion |

## v1.3 — Multi-candidate retrieval, hard reject và quyết định biên tập

1. Từ `beat_visual_brief.json` đọc `visual_intent`, `preferred_shot_types`, `continuity_requirement`, `actor/action/storyline`. Kiểm hash/phim/time domain của `scene_catalog` trước truy vấn.
2. Xuất **nhiều candidate** trong `shots/shot_candidates.json` có `shot_id`, `beat_id`, `scene_id`, `src_in_s`, `src_out_s`, `evidence_refs`, các cờ chất lượng và `match_status`. Nếu chỉ tìm được một, ghi rõ vì sao; không tạo ứng viên giả.
3. **Hard reject** trước ranking: sai nhân vật cốt lõi, sai hành động, sai tuyến quá khứ/hiện tại, source out-of-duration, source path ngoài job/sai nguồn, clip không đủ chứng cứ hoặc hình chứa chữ/vật thể trái sự kiện. Đặt `REJECTED` + `hard_reject_reasons`, không cứu bằng cosine điểm cao.
4. Chỉ chấm thứ tự ứng viên còn hợp lệ theo event/actor/action → biểu cảm/hậu quả → dễ hiểu trong hình → **continuity** → cỡ cảnh/góc máy → chất lượng → tránh lặp. Điểm CLIP/cosine chỉ giúp tìm candidate, **không** tự nâng lên VERIFIED.
5. Nhân vật đang trao vật, di chuyển hoặc xảy ra biến cố phải được xem chuỗi ảnh/clip và có `motion_verification`, không gán `VERIFIED_VISUAL` bằng một frame. Nếu bằng chứng thiếu, giữ `CANDIDATE` hoặc `NEEDS_REVIEW`.
6. ChatGPT ghi quyết định vào `shots/shot_selection_decisions.json` (`decision_by_chatgpt`, `selection_reason`, `selected_shot_id`, `alternate_shot_ids`, `rejected_shot_ids`, evidence). Shot lựa chọn chính và dự phòng phải cùng tuyến và không trái lời kể.
7. `shot_map.csv` giữ nguyên mọi cột v1.2, bổ sung `shot_id`, `shot_type`, `visual_intent`, `selected_rank`, `reuse_count`, `continuity_id`, `transform_hint`, `decision_evidence_ref`. Ghi reuse có lý do, không dùng cảnh sai để lấp WAV.

**Gate SHOT_SELECTION_READY:** mọi beat trọng yếu có clip đã xem, `VERIFIED_VISUAL`, `0 <= src_in_s < src_out_s <= source_duration`; không còn actor/action/storyline sai hoặc orphaned critical beats. Nếu chưa READY, G08 báo các beat thiếu và cần rà soát; **không cho G09 bắt đầu**, dù model similarity cao. Gate nội dung không phải quyền duyệt G09.

**Trường hợp V35:** máy ghép frame chỉ là `CANDIDATE`; đối chiếu chuỗi chuyển động + nhân vật/thoại mới có thể kết luận cùng cảnh. Không lấy một điểm trùng ảnh làm bằng chứng chắc chắn.
