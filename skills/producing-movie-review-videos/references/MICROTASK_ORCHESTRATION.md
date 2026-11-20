# MICROTASK_ORCHESTRATION — v1.3.23: thống nhất điều phối G01–G15

**ƯU TIÊN V1.3.23:** Luôn dùng `FULL_WORKFLOW_INTEGRITY_V1323.md` và `tools/workflow_integrity_v1323.py::decide_dispatch` trước **mỗi** task. Qxx/approval chỉ là điều kiện; stage/task đã PASS và hash thật đúng thì reuse thay vì tạo lô mới; G07 mẫu giọng không thay G07_VOICE, Q09 trước pilot G10, Q10+G10_PILOT trước full render G11, Q12 trước mix G13, Q13 trước G14.

**Quy tắc hiện hành:** đọc `ONE_APPROVAL_START_POLICY_V1321.md`, `G04_G05_FAST_TRACK_V1322.md`, `ATOMIC_STAGES_V1315.md`, `SMART_BATCH_APPROVAL.md`, `WORKFLOW_CONSISTENCY_V1312.md` và `MICROTASK_ACCEPTANCE_REPAIR.md` theo thứ tự ưu tiên chuyên biệt. Người dùng duyệt `WORK_PACKAGE_ID` hữu hạn, rồi ChatGPT triển khai ngay các task đủ điều kiện trong cùng lượt; không có vòng phê duyệt kế hoạch/triển khai thứ hai. `Gxx.Mnn[.Bxxx]` là mã **nội bộ** đối với các stage còn dùng batch, không phải nút phê duyệt. Không tự chạy nền qua lượt chat.

## Tác vụ nguyên giai đoạn bắt buộc cho gói mới

| Stage | Task ID duy nhất | QC | Quy tắc |
| --- | --- | --- | --- |
| G01 | `G01.SOURCE.FULL` | Q01 | Một lượt kiểm nguồn phim |
| G02 | `G02.ASR.FULL` | Q02 | Một ASR toàn phim, QC văn bản đơn giản |
| G03 | `G03.TRANSLATE.FULL` | Q03 | ChatGPT dịch toàn transcript, phân trang chỉ nội bộ |
| **G04** | **`G04.FILM.UNDERSTANDING.FULL`** | **Một Q04** | Scene index toàn phim và visual thật tại các tình tiết cốt lõi, không mở phê duyệt/QC riêng cho từng scene |
| **G05** | **`G05.REVIEW.FULL`** | **Một Q05** | Viết REVIEW sáu bước trọn vẹn, kiểm web + narrative-only, người dùng duyệt duy nhất bản kịch bản hoàn chỉnh qua `G05_SCRIPT` |

**Với G04/G05, các mã lịch sử `M01/M02.Bxxx/M03.Bxxx/M04/M05/M06.Rxxx` KHÔNG được đưa vào task_ids hoặc bounded_batches của package mới.** Giới hạn 8 scene/24 ảnh hay 4 đoạn của tài liệu trước chỉ là gợi ý *phân trang có thể điều chỉnh*, không phải giới hạn về số cảnh phải xem hoặc cổng dừng. Được ghi checkpoint tiến độ nội bộ trong task FULL nhưng chỉ nghiệm thu tổng thể. G04 không đòi mọi shot đều có phân tích góc máy/visual_shot_profile; G08 là nơi phân tích shot phục vụ dựng. G05 không tự chia nội dung thành các nhiệm vụ viết từng đoạn.

## Những stage khác vẫn cần QC thực nhưng không chia phê duyệt

| Stage | Nội dung trong gói đã duyệt | Gate |
| --- | --- | --- |
| G06 | Khóa script; chia beat, nối event_id, đối chiếu coverage toàn narration | Q06 |
| G07 | Chọn giọng, tạo sample, người dùng duyệt `G07_VOICE`, TTS WAV, QC âm thanh | Q07 |
| G08 | Beat→scene candidates; ChatGPT xem hình/clip thật, loại sai actor/action, chọn shot và lập shot_map | Q08 `SHOT_SELECTION_READY` |
| G09 | EDL, chuẩn hóa timeline, smoke/preview/pilot có giới hạn; không full render | Q09 |
| G10 | Dựng pilot từ EDL và WAV thật; ChatGPT xem/nghe và người dùng duyệt `G10_PILOT` | Q10 |
| G11 | Full render sau pilot duyệt, quality transforms theo quyền, QC output | Q11 |
| G11A | Metadata YouTube và chọn title qua `G11A_METADATA` | Q11A |
| G11B | Tạo thumbnail ChatGPT, kiểm ảnh thật, duyệt `G11B_THUMBNAIL` | Q11B |
| G12 | Dùng thumbnail làm intro 2 giây + logo thương hiệu theo profile đã duyệt | Q12 |
| G13 | Nhạc có quyền sử dụng, ducking, mix, QC mức âm | Q13 |
| G14 | QC MP4 thật technical/story/visual độc lập, nghe/xem evidence quan trọng | Q14 |
| G15 | Bàn giao MP4/thumbnail/metadata/ZIP/manifest/SHA; xóa chỉ theo `G15_DELETE` | Q15 |

Các stage G06–G15 có thể cần chia `Bxxx` **để xử lý kỹ thuật**, chỉ thực thi trong finite task scope đã duyệt và không hỏi người dùng từng batch. Giới hạn như 12 beat/lô ở G06/G08, 12 WAV/lô G07, 12 beat EDL/lô G09 chỉ là ngân sách nội bộ; không được bỏ sót dữ liệu hoặc gán PASS khi chưa QC.

## Tình huống tiếp tục/sửa chữa

- Với `WORK_PACKAGE_ID` đã duyệt, các batch/segment/trang tiếp theo hợp lệ được chạy trong lượt đang hoạt động; nếu context hết, ghi `PARTIAL`/checkpoint và trình **Tiếp tục gói** chứ không xin duyệt kế hoạch/triển khai lại.
- Mỗi task có `source_hash`, input/output hash, Qxx, ledger append-only. Đã PASS và hash khớp thì skip. Không tạo thêm `WORK_PACKAGE_ID` hay microtask chỉ để tái kiểm một cảnh phụ/từ thoại phụ.
- `NEEDS_FIX` trong `repair_budget` đã duyệt tối đa 2 lần/issue và tối đa 4/gói; sửa cục bộ, kiểm lại. Thiếu quyền/chứng cứ cốt lõi thì `NOT_VERIFIED`/`BLOCKED`; không bí mật nới scope để vượt lỗi.
- Trường hợp đang chờ xử lý tiến trình đã cho phép: `WAITING_FOR_JOB`; chờ clip/âm thanh người dùng gửi lại: `WAITING_FOR_AUDIO_UPLOAD`; không được đánh dấu PASS hay mở task mới khi gate vẫn bị chặn.
- G04/G08/G14 cần bằng chứng thực: metadata/FFprobe/AI candidates không thay cho ChatGPT xem/Nghe media. Nếu thiếu kênh truyền ảnh/clip, dùng `MEDIA_EVIDENCE_HANDOFF_V1320.md` trong phạm vi duyệt, báo ZIP có thật và chờ người dùng upload; không bịa link.
- Human gates `G05_SCRIPT`, `G07_VOICE`, `G10_PILOT`, `G11A_METADATA`, `G11B_THUMBNAIL`, `G15_DELETE` là quyết định độc lập của người dùng, không được vượt bằng phê duyệt package ban đầu. Đặc biệt `G05_SCRIPT` chỉ xuất hiện khi toàn bộ kịch bản đã có và Q05 đủ điều kiện.
- Với gói cũ có các task `G04.Mnn`/`G05.Mnn`, giữ nguyên approval/hash/checkpoint, chỉ áp chính sách atomic vào **gói mới**. Muốn mở rộng phạm vi hay chuyển sang FULL phải có gói tương ứng được người dùng duyệt.

Ví dụ lịch sử `G03.M02.B001` → `G03.M02.B002` dùng để giải thích cách checkpoint trước v1.3.15, **không còn là task riêng cho G03 mới**. Không tự dịch sang một package mới khi chưa có quyền.
