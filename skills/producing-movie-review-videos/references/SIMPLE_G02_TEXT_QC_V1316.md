# SIMPLE_G02_TEXT_QC_V1316 — G02 = tạo transcript toàn phim + một QC văn bản

> **QUY TẮC ƯU TIÊN CAO NHẤT CHO NGHIỆM THU G02 kể từ REVIEW_PHIM v1.3.16.** Thay thế mọi ràng buộc trước đây bắt G02 phải nghe lại từng câu thoại, mở 17 cụm, phân loại `MATERIAL_REVIEW` hoặc rà nghi vấn cốt truyện mới có thể PASS. Áp dụng cho dự án mới và cho **gói chuyển trạng thái mới được người dùng duyệt** ở dự án cũ. Không tự sửa checkpoint có sẵn, không tự mở quyền G03/G04.

## 1. Mục tiêu và điểm kết thúc

- G02 chỉ có **một tác vụ `G02.ASR.FULL`**: lấy toàn bộ âm thanh phim → một lần ASR toàn phim → **một bản transcript tiếng Anh hoàn chỉnh** → rà và **sửa lỗi văn bản** → nghiệm thu Q02 một lần.
- **`Q02_TEXT_PASS`** khi: đúng nguồn/hash, audio đã được xử lý toàn bộ; ASR thực sự chạy xong và xuất file, bản transcript sạch tồn tại, Unicode/UTF-8, dấu câu, xuống dòng, mã hóa, timecode, id và định dạng đều đọc được; không còn lỗi chữ hỏng chưa sửa. Kết quả là `Q02_GATE_STATUS=PASS` dù còn cờ `LOW_LOGPROB`, `REPEATED_TEXT_REVIEW`, `LONG_SEGMENT_CHECK` hoặc nghi nghe nhầm lời thoại. G02 không xác nhận từng câu thoại đúng 100%; đây là nghiệm thu **đầu ra văn bản**, không phải xác minh nội dung phim.
- **Không kiểm 17 cụm**, không kiểm từng cảnh báo/câu chào, **không chặn vì** 1–2 từ ASR, nghi lỗi nghe trong tiếng nhạc, câu lặp hoặc thiếu bằng chứng ngữ cảnh. Không xin người dùng upload WAV để PASS G02. Dừng chỉ khi không có transcript thật, nguồn/hash sai, ASR mới xử lý một phần hoặc lỗi văn bản/định dạng không sửa được mà không đoán lời.

## 2. Sửa chữ có nguyên tắc, không viết lại lời thoại

- Transcript ở dạng UTF-8 plain text / JSONL, không có “font chữ” riêng trong byte văn bản; lỗi chữ thường là encoding/Unicode hoặc format. Chuẩn hóa Unicode NFC, bỏ BOM, sửa khoảng trắng, ngắt dòng, dấu câu, escape hợp lệ, chỉ sửa chính tả **khi chắc chắn là lỗi đánh máy**, không đổi tên riêng, phủ định, con số, câu thoại không chắc, vai diễn hoặc nội dung hành động chỉ vì đoán từ ngữ cảnh.
- Nếu phát hiện lỗi trình bày: **sửa trực tiếp trong bản transcript sạch/version mới**, ghi log `text_qc_changes` và SHA-256. Đầu ra chính bàn giao là `analysis/transcript_cleaned.v1.jsonl` và `analysis/transcript_cleaned.v1.txt` (hoặc version kế tiếp nếu đã tồn tại). File ASR raw `analysis/g02_asr_full_raw.jsonl` và báo cáo cũ giữ **read-only**, không ghi đè. Đầu ra phiên bản mới được coi là transcript dùng cho G03.
- Câu ASR còn nghi ngờ nhưng không sai định dạng được giữ nguyên bản xuất ra với `unverified_by_listening=true` hoặc được gắn cờ ở metadata; **không khẳng định là lời thoại thật**. Với timestamp vượt độ dài âm thanh, loại ứng viên thời gian sai khỏi bản sạch, giữ nguyên trong raw và log; không tự kéo dài WAV hay bịa timecode. Không tự xóa câu lặp dựa trên tần suất vì có thể là thoại thật.
- Nếu chữ bị hỏng không thể phục hồi chắc chắn (ví dụ ký tự `�`), giữ `Q02_GATE_STATUS=NOT_VERIFIED` cho đến khi sửa bằng nguồn rõ ràng; **không** thay cả câu bằng câu do ChatGPT sáng tác. Không bật ASR lại khi chưa được duyệt riêng.

## 3. Đơn giản hóa QC và chuyển bước

QC G02 chỉ cần 4 nhóm: `SOURCE_AND_FULL_ASR_COMPLETE`, `TRANSCRIPT_EXISTS_NONEMPTY`, `TEXT_ENCODING_LAYOUT_FIXED`, `CLEAN_TRANSCRIPT_HASH_AND_LINEAGE`.

- Đạt → ghi một `Q02` mới với `Q02_GATE_STATUS=PASS`, `QC_NOTE=PASS_WITH_ASR_WARNINGS` khi còn cảnh báo. **Không có** Q02 theo câu, 17 cụm hoặc cảnh phụ, không QC ngữ nghĩa tại G02. Sau đó **đề xuất phê duyệt riêng** `G03.TRANSLATE.FULL` để ChatGPT dịch toàn bộ bản sạch.
- Các câu hỏi ai làm gì, ai chết, ai thắng, động cơ, nguyên nhân-hậu quả và **độ khớp hình ảnh** thuộc công đoạn G04/G05/G08/G14; phải kiểm tra khi tạo nội dung REVIEW nhưng **không dùng để khóa Q02**. G04 vẫn cần quan sát khung hình/clip thật; G08 vẫn cần `VERIFIED_VISUAL` và `SHOT_SELECTION_READY`; G05_SCRIPT/G07_VOICE/G10_PILOT vẫn giữ nguyên.
- Không mở rộng phê duyệt: sửa quy tắc plugin **không tự động PASS** các checkpoint `NOT_VERIFIED` hiện có. Với Fatman (2020), **G02.PKG05.CONTEXT17 là kế hoạch chưa thi hành và không còn cần thiết theo chính sách mới**. Khi được duyệt một gói QC văn bản mới, tái sử dụng toàn bộ WAV và ASR G02 hiện có, tạo transcript sạch v1 và QC mới append-only, **không chạy ASR, không đọc lại 17 cụm, không sửa phim gốc, không tự chạy G03/G04**.

## 4. Cách áp dụng

1. Kiểm checksum nguồn, WAV, ASR raw, manifest, phiên bản plugin và gói duyệt.
2. Từ ASR toàn phim đã xuất, định dạng lại văn bản và JSONL, giữ `segment_id`/`start`/`end`/`speaker_id`; sửa chính tả/format chắc chắn, các lỗi âm thanh chưa nghe thì chỉ đánh cờ.
3. Kiểm UTF-8, chữ đọc được, hash, số dòng/ID, báo lỗi chữ không sửa được; chỉ một `Q02_TEXT_PASS` tổng thể.
4. Trình transcript hoàn thành và đề xuất phê duyệt riêng để ChatGPT dịch (`G03.TRANSLATE.FULL`). Không tự phê duyệt thay người dùng.

**Ranh giới:** Quy tắc này chỉ thay G02/Q02. G01, G03, G04, G05 và G06–G15 tiếp tục theo các hợp đồng hiện hành, không cài/tải/CPU fallback/xóa file khi không được duyệt.
