# REVIEW_PHIM v1.3.16 — G02 text-only QC

**G02:** ASR toàn phim → sửa Unicode/format/chữ rõ ràng → 1 Q02, không rà 17 cụm. **G03/G04:** chỉ theo quyền phê duyệt riêng; G04/G05/G08 kiểm nội dung và hình ảnh.

# REVIEW_PHIM v1.3.15 — Whole-film transcript, Story-first, Visual-first

Tạo video review phim tiếng Việt từ phim gốc: nhận dạng các thông tin cần thiết, phân tích diễn biến bằng hình ảnh thực, viết review có chứng cứ, chọn clip khớp lời bình và dựng/video QC theo phê duyệt.

**Bắt đầu bằng** `SKILL.md` → `references/WHOLE_FILM_TRANSCRIPT_V1314.md` → `references/STORY_FIRST_WORKFLOW_V1313.md` → `references/WORKFLOW_CONSISTENCY_V1312.md` → `references/SMART_BATCH_APPROVAL.md`.

## Thay đổi mới v1.3.15

- **Một phim → một G02.ASR.FULL**: không chia transcript thành B001–B010 hay nhiều microtask. Trích toàn bộ audio một lần, gọi ASR toàn phim một lần, ghi/đọc theo luồng để an toàn bộ nhớ, nghiệm thu một Q02 khi đủ coverage.
- Fatman: giữ các B001–B003 cũ chỉ làm bằng chứng; kế hoạch B004–B010 chưa được duyệt không còn phù hợp, phải trình lại **kế hoạch full-film và plan_hash mới** trước khi chạy. Không xử lý phim chỉ vì nâng plugin.

## Thay đổi trước đó so với v1.3.12

- G02 ASR: đoạn 1–2 từ/câu xã giao/hallucination không làm đổi cốt truyện sẽ thành **MINOR_NONBLOCKING**; giữ nguyên raw và quarantine, không sử dụng làm chứng cứ, không đòi WAV người dùng và không chặn việc xử lý lô tiếp theo. Lỗi ảnh hưởng hành động, nhân vật, cái chết, phủ định/nhân quả, thiếu phim hoặc hash vẫn chặn.
- G02 Q02 chỉ đạt khi **đủ toàn phim**; phân biệt PASS kỹ thuật với lời thoại chưa được nghe xác minh. Không ghi đè checkpoint cũ.
- G04: xây scene catalog và story map từ các khung hình, contact sheet và clip thực sự được xem.
- G05: kể review mạch lạc, không kể lặp hội thoại vô ích. Cần duyệt kịch bản.
- G08: mỗi beat trong lời bình phải liên hệ đúng sự kiện → cảnh → đoạn phim; đối chiếu người, hành động, thời gian và cảm xúc. Không dùng embedding/timestamp ASR để bịa `VERIFIED_VISUAL`.
- G09–G15: pilot trước full render; QC hình và lời, và chỉ xóa khi có quyền.

## Quyền hạn không đổi

Phê duyệt một WORK_PACKAGE_ID hữu hạn; deviceId, JOB_DIR, source hash, `plan_hash`, lock/checkpoint, các quyền đọc/ghi cài đặt phải được xác nhận. GPU-first, không tự fallback CPU, không ghi đè source hoặc dùng file phim/logo khác. Không tự chạy nền qua lượt chat. G05_SCRIPT, G07_VOICE, G10_PILOT, G15_DELETE giữ human gates.

## Công cụ kiểm tra

`tools/asr_story_first_policy.py`: bộ triage Python stdlib, đọc metadata JSON được chỉ định rõ khi có quyền, **không** nghe audio/dịch transcript, **không** sửa trạng thái. Dùng trong QC và xem kết quả trước khi áp dụng cho một package mới.

Tests mới: `tests/test_whole_film_transcript_v1314.py`, `tests/test_story_first_v1313.py`, `tests/test_asr_story_first_policy.py`. Thêm `tools/whole_film_transcript_policy.py` thuần Python stdlib để lập phạm vi một tác vụ và QC cấu trúc toàn phim.

## v1.3.15: G01/G03/G05 gộp theo giai đoạn

- `G01.SOURCE.FULL`: một tác vụ kiểm định nguồn và một Q01.
- `G03.TRANSLATE.FULL`: ChatGPT dịch toàn transcript trong một tác vụ Q03; phân trang ngữ cảnh nội bộ không sinh task.
- `G05.REVIEW.FULL`: toàn kịch bản review sáu bước và Q05; người dùng duyệt `G05_SCRIPT` sau khi có bản hoàn chỉnh.
- G02 tiếp tục `G02.ASR.FULL`; G04, G06–G15/P00 không thay quy trình.
