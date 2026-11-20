# FILM_UNDERSTANDING — G04 ChatGPT hiểu phim bằng hình ảnh + transcript

## Mục tiêu và giới hạn

G04 tạo bản đồ cốt truyện có thể truy vết qua video thực, không chỉ qua ASR. G04 không tự viết REVIEW (G05) hoặc chọn clip dựng cuối (G08). ChatGPT là người xem và kết luận từ dữ liệu thật; các công cụ FFmpeg, FFprobe, PySceneDetect, OpenCV, vision embedding/Qwen-VL nếu đã có chỉ tạo/tìm chứng cứ. Không mặc định cài/tải model, không sử dụng API trả phí.

- Đầu vào bắt buộc: `SOURCE_MOVIE` (chỉ đọc), `analysis/media_probe.json`, transcript và flags G02–G03, source duration/timebase, bản ghi đã duyệt G04.
- Đầu ra: `analysis/scene_catalog.json`, `visual_events.json`, `story_map.json`, `characters.json`, `evidence_index.json`, `qc/g04_evidence_report.md`, frame/contact sheet/clip kiểm chứng trong JOB_DIR.
- Mức độ đã đọc toàn phim là **coverage chỉ mục + lấy mẫu**, không phải cam kết xem đủ từng giây; báo rõ độ phân giải mẫu, cảnh chưa được xem, ranh giới/điểm rủi ro.

## Quy trình thực hiện được

1. Xác thực hash/FFprobe nguồn, timestamp gốc, thời lượng, tracks, VFR, subtitles; bỏ hoặc khoanh vùng ASR vượt duration, lặp bất thường, quảng cáo, ngôn ngữ khác và khoảng im lặng. Trích video/audio chỉ khi G04 được duyệt.
2. Dùng PySceneDetect phát hiện các scene cuts; fallback lấy mẫu đều theo thời gian nếu scene detection không hoạt động. Không xem VAD/ASR làm chỉ mục đầy đủ vì cảnh không lời có thể chứa biến cố chính.
3. Xuất frame thực với tên và mốc hình rõ, ảnh đại diện cho toàn cảnh (đầu/giữa/cuối hoặc theo thay đổi hành động), contact sheets theo batch vừa đủ để **ChatGPT thực sự nhìn/đọc được**. Kiểm ranh giới, cảnh liền kề và motion clips. Không tạo file ra ngoài `JOB_DIR/analysis/` và `JOB_DIR/temp/`.
4. Đọc từng contact sheet qua kênh hình ảnh thực sự xem được trong phiên Remote Desktop Commander. Ghi lại batch đã nhìn, ID frame và khoảng thời gian. Nếu công cụ chỉ trả tên/path mà không trả ảnh đủ rõ, không giả đã xem: tìm cách chuyển frame vào kênh xem được có thẩm quyền hoặc đánh dấu `NEEDS_REVIEW`.
5. Từ hình + transcript tạo `scene_catalog` với nhãn scene `INDEXED`, `VISUALLY_REVIEWED`, `NEEDS_REVIEW`. `INDEXED` nghĩa là đã trích chỉ mục, **chưa** xác minh nhân vật, hành động hoặc cảm xúc.
6. Tại biến cố quan trọng, đoạn cắt chuyển tuyến, manh mối nhỏ, tương tác im lặng, biểu cảm hoặc mâu thuẫn hình/thoại: đọc chuỗi **3–n khung hình** hoặc clip ngắn để biết hướng hành động, chủ thể, đối tượng và hậu quả. Một frame tĩnh không thể tự chứng minh “mở cửa”, “đưa đồ”, “giết”, “lén giấu”, “khóc” hay ý đồ.
7. Liên kết lời thoại và khung hình theo timestamp có xét sai số ASR. Mỗi event phải tách `visible_observations` (quan sát), `dialogue_summary` (nghe được), `emotion_interpretation`/động cơ (diễn giải), `causes` và `consequences`. Không coi lời thoại về một nhân vật là bằng chứng người đó đang ở trên màn hình.
8. Tạo `story_map` gồm thứ tự xuất hiện trên màn ảnh `on_screen_order`, thứ tự câu chuyện theo thời gian `chronological_events`, các storyline và điểm hội tụ, dấu mốc mở đầu/biến cố/cao trào/kết, causal links cùng trạng thái chứng cứ. Không tái sắp xếp các tuyến thành diễn biến lịch sử nếu phim không chứng minh.
9. Lập `evidence_index` trỏ vào ảnh/clip/transcript tồn tại thực trong JOB_DIR, với sự kiện/chủ thể, timestamp, độ phân giải hình, nguồn và phiên bản. Mọi nhận định trọng yếu phải truy xuất được nguồn kiểm chứng; nếu đường dẫn đã mất hoặc vật thể/nhân vật không rõ, đánh `NEEDS_REVIEW`.
10. Viết `g04_evidence_report.md`: số scene và batch thực sự xem, coverage thời gian, sự kiện chính, biến cố không lời, phần khó nhận diện, mọi mâu thuẫn và tình tiết cốt lõi chưa xác minh. Dừng sau G04; chỉ trình kế hoạch G05 khi đạt gate.

## Gate FILM_UNDERSTANDING_READY

**ĐẠT** khi: nguồn hợp lệ; scene_catalog bao phủ đầu–cuối ở mức lấy mẫu; các sự kiện quyết định mạch truyện có hình/thoại/clip thật phù hợp; phân biệt được quan sát và suy luận; storyline và thứ tự thời gian đều có; các `unresolved_claims` quan trọng không được dùng làm khẳng định trong outline dự kiến. Mọi bằng chứng tham chiếu tồn tại, xem được.

**BLOCKED** khi: video/ảnh không đọc được, claim trụ cột chưa xác minh, scene cut/lời thoại xung đột chưa giải quyết, contact sheet không thực sự được ChatGPT xem hoặc nguồn bị nhận diện sai. Chỉ có thể làm rõ, lấy thêm ảnh/clip hoặc đề xuất loại/giảm chắc chắn claim khỏi outline; không tự vượt gate.

**KHÔNG ĐƯỢC KẾT LUẬN:** việc đã giải mã khung hình bằng FFmpeg hay kết quả CLIP/Qwen-VL tự nó đủ chứng minh ChatGPT đã hiểu nhân vật/hành động; số ảnh được sinh ra không bằng số ảnh đã xem; một scene có ID không đồng nghĩa event đã verified.

## Quy tắc chống quá tải và khôi phục

- Chia phim dài thành batch có timestamp range, `frame_count`, `inspected_frame_ids`, `inspected_motion_ids`, `reviewed_by_chatgpt`, `unresolved_items`; báo đúng phần đã hoàn thành.
- Sau mỗi batch có thể ghi checkpoint `analysis/g04_checkpoint.json` khi G04 đã duyệt, kèm hash phim, scene ids và tool provenance. Trên phiên tiếp theo so sánh hash trước khi tái dùng; không ghi đè phát hiện cũ khi chưa đối chiếu.
- Phim đa thời gian: giữ `film_time_s` tách biệt `story_time_hint`; cùng nhân vật ở hiện tại/quá khứ có thể khác ngoại hình, phải xác minh bằng ngữ cảnh.
- Không có model vision local: xử lý bằng FFmpeg và ChatGPT trực tiếp; thiếu kênh quan sát khung hình thì báo chặn, không giả tạo.

## Phân tích Visual Shot Profile — v1.3.0

Sau khi đã duyệt G04, từ scene index lựa chọn ảnh đầu/giữa/cuối và khi chuyển động thay đổi, rồi ChatGPT **thực sự nhìn ảnh** trước khi gán nhãn `shot_type`, `visual_purpose`, `primary_subject_ids`, `objects_of_interest`, `facial_expression_observed` (quan sát) và `emotion_interpretation` (suy luận). `shot_type`: `EXTREME_CLOSE_UP/CLOSE_UP/MEDIUM/WIDE/DETAIL/MIXED/UNKNOWN`; `camera_motion`: `STATIC/PAN/TILT/TRACK/HANDHELD/ZOOM/MIXED/UNKNOWN`. Quan sát một frame không xác minh hướng/chuyển động của camera; ghi `motion_verification=UNKNOWN` nếu chưa có nhiều frame/clip.

**Bộ thuộc tính chất lượng:** `text_regions`, `subtitle_region`, `letterbox_estimate`, `quality_flags` (`BLUR`, `DARK`, `OCCLUDED_FACE`, `BURNED_SUBTITLE`, `NONE`, `UNKNOWN`); những dấu hiệu mơ hồ giữ `UNKNOWN` thay vì suy diễn. `shot_boundaries` chỉ ghi khi có chuỗi/scene boundary đủ chứng cứ, ngược lại `UNRESOLVED`. Một cảnh có thể chứa nhiều shot, không đánh đồng scene_id với cut thật.

Mỗi profile kết nối về `scene_id` + `event_ids`, có `inspection_status`, `inspected_by_chatgpt`, `inspected_motion_ids`, `evidence_refs` với file tồn tại/timecode. File `analysis/visual_shot_profile.json` có thể chia thành nhiều batch/checkpoint, ghi coverage đã thực sự kiểm tra; không viết `VISUALLY_REVIEWED` chỉ vì FFmpeg trích frame.

Các cảnh không lời vẫn là sự kiện nếu chuỗi hình minh chứng hành động; phân biệt phát hiện nét buồn trên mặt với giả định về động cơ. Nhân vật tương tự nhau hoặc phim có tuyến thời gian song song phải kiểm `characters` và `story_map` trước khi dùng profile. **FILM_UNDERSTANDING_READY** vẫn đánh giá claim cốt truyện: một cảnh phụ `shot_type=UNKNOWN` không tự làm chặn G05.
