## Chọn chế độ trước khi đọc

**PRODUCTION_FIRST_V1325 đã được duyệt:** dùng
[PRODUCTION_FIRST_AUTONOMOUS_V1325](PRODUCTION_FIRST_AUTONOMOUS_V1325.md) và
[PRODUCTION_RELIABILITY_V1326](PRODUCTION_RELIABILITY_V1326.md).
Không dùng QC/PASS, duyệt từng scene/beat/WAV/shot/batch, web crosscheck hay ba trục
G14 dưới đây để chặn tiến độ. Chỉ kiểm file thực dùng được, hash, lỗi chương trình
và quyền thao tác. Không ghi đè bản cũ; xóa cần phê duyệt xóa riêng.
Các chi tiết kỹ thuật sản xuất vẫn có thể tham khảo, nhưng điều phối và nghiệm thu
tuân theo chính sách Production First. Không tự suy diễn ủy quyền sáng tạo.

## Nhánh Legacy — quy tắc dưới đây chỉ điều phối gói chế độ cũ

<details>
<summary>Hướng dẫn lịch sử; không áp cho Production First</summary>

# APPROVAL_TRANSLATION_AUDIO — Gói được duyệt, ChatGPT dịch và nghe có bằng chứng

**Quy tắc phê duyệt mới:** xem `SMART_BATCH_APPROVAL.md`. Chỉ xin phê duyệt trước **WORK_PACKAGE_ID** và các quyết định cần người dùng thật sự chọn; không bắt duyệt mỗi `TASK_ID`, mỗi lô transcript hay mỗi đoạn audio trích xuất nếu đã nằm rõ trong package scope. Thiếu quyền trích audio hoặc cấp quyền gửi file ra chat → đề xuất gói bổ sung. Đây không phải quyền tự tải/sửa toàn máy.

## A. Trình trước gói

Nêu `deviceId`, `FILM_DIR`, `SOURCE_MOVIE`, `JOB_DIR`, `WORK_PACKAGE_ID`, `plan_hash`, các Mnn/Bxxx thuộc scope, `start/end segment_id` hoặc time range, read roots, write roots, output, giới hạn lô, acceptance_criteria và rủi ro. Chỉ khi user duyệt mới được thực hiện. Nút thực `GenUI.issueNewTurn('PHÊ DUYỆT GÓI ...')`; nếu không có UI dùng cú pháp rõ, không bịa nút bấm.

## B. ChatGPT đọc và tự dịch

G02 Faster-Whisper local chỉ ASR transcript gốc, không dùng mode translate. G03 ChatGPT phải **trực tiếp đọc toàn bộ** `analysis/transcript_original.jsonl` qua Remote Desktop Commander theo các lô ≤40 segment hoặc 1.000 từ; bản dịch do ChatGPT trực tiếp tạo, không local LLM/API/script/thư viện dịch. Script chỉ được phân trang, ghi/ghép, kiểm hash/coverage. Giữ segment_id, start/end, tên riêng, người nói, lưu `analysis/transcript_vi.jsonl`, `.txt`, `analysis/translation_flags.json`. Câu không nghe rõ: `[CẦN NGHE KIỂM CHỨNG]` và timecode, không phỏng đoán. **Nhiều lô chạy liên tiếp sau một phê duyệt gói**, nghiệm thu nội bộ từng lô, không xin duyệt cho B002 sau B001.

## C. ChatGPT nghe âm thanh từ người dùng upload

Nếu cần nghe tại G02/G03/G04/G08/G14, lập `AUDIO_QC_REQUEST` ghi segment/timecode, lý do, nguồn; trích audio clip khoảng 30 giây–5 phút vào `JOB_DIR/analysis/audio_for_chat/` **nếu gói đã duyệt thao tác trích xuất**. Lập `audio_manifest.json` (file/source/timecodes/bytes/SHA-256). Nếu công cụ hỗ trợ chuyển file về sandbox ChatGPT, chỉ cung cấp link `sandbox:/mnt/data/...` khi file tồn tại và hash khớp. Nếu không hỗ trợ, ghi `CHƯA CÓ LINK TẢI TRỰC TIẾP` cùng đường dẫn trên máy để người dùng tự upload, không dùng link file://, localhost, IP private hay link giả. Không tự mở server/firewall/port/upload cloud.

Chỉ khi **người dùng upload file audio vào chat và ChatGPT thực sự nghe/giải mã được**, so khớp transcript và ghi `HEARD_VERIFIED/HEARD_UNCLEAR/MISMATCH/NOT_VERIFIED`. Không có upload → `WAITING_FOR_AUDIO_UPLOAD`, dừng gate liên quan; được tiếp các task không phụ thuộc đã có phép nhưng không báo PASS phần cần nghe. Không yêu cầu tải/audio mới cho mọi câu vô ích.

## D. Những việc không được gộp quyền

Duyệt `WORK_PACKAGE_ID` không tự chấp thuận thay phim/logo, tải/cài model mới, thay GPU backend, xóa G15, đổi kịch bản G05/giọng G07/pilot G10 đã duyệt, hay xem/nghe thay ChatGPT. Gói có thể thực hiện các công việc kỹ thuật độc lập trong scope; phê duyệt nội dung của người dùng là human gate riêng. Mọi bản dịch thiếu đoạn không được khai QC PASS.

</details>
