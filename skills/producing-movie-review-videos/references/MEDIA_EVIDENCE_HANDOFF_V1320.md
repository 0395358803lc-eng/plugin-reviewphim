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

# REVIEW_PHIM v1.3.20 — Mandatory Clip/Audio ZIP Handoff & Actual Inspection

**Phạm vi:** mọi giai đoạn P00/G01–G15 (bao gồm G11A/G11B) khi có vướng mắc mà ChatGPT **bắt buộc** phải quan sát clip thật hoặc nghe audio thật để đưa ra nhận định cốt lõi, thay vì chỉ dựa vào log/JSON/ASR/FFprobe/model. Đây là **quy tắc ưu tiên v1.3.20**, ghi đè cách gửi audio riêng tại `APPROVAL_TRANSLATION_AUDIO.md` và mọi hướng dẫn cũ nếu có xung đột về ZIP/link/chứng cứ. Không ép xuất ZIP cho những lỗi nhỏ không ảnh hưởng kết luận hoặc những frame ChatGPT đã thật sự xem được qua công cụ hiện tại.

## 1. Trigger và giới hạn

- G02/G03: câu quan trọng gây thay đổi dịch nghĩa/nhân vật; G04/G05/G08: hành động, nhận diện, nguyên nhân, timeline, chuyển động chưa rõ; G07/G10/G13/G14: giọng đọc, phát âm, tiếng hiện trường, lỗi tiếng, clipping, sync; G09/G11/G12/G14: clip bị crop sai, rung/giật, phụ đề che, khung hình đen, sai hình, lỗi dựng. Áp dụng tương tự ở các G khác khi một claim quan trọng cần hình/âm thanh thật.
- Phân loại `MINOR_NONBLOCKING` nếu không ảnh hưởng chuyện phim/QC, không gây vòng lặp tải vô nghĩa. Nếu `DECISIVE_MEDIA_INSPECTION_REQUIRED` mà ChatGPT chưa trực tiếp thấy/nghe được: **không PASS** gate phụ thuộc, tạo một yêu cầu `MEDIA_EVIDENCE_REQUEST` cụ thể cho đúng khoảng thời gian và nội dung cần kiểm. Không yêu cầu upload phim nguyên bộ, không trích xuất tràn lan.
- Một yêu cầu có `request_id`, `deviceId`, `link_id`, `WORK_PACKAGE_ID`, `plan_hash`, `JOB_DIR`, stage/QC/issue, nguồn+hash, timecodes, media kind (audio/video/image), câu hỏi cần giải quyết, gói export/transfer permission, giới hạn số file/size và stop condition. Không phát sinh một phê duyệt **từng clip** nếu quyền extract/export/chia sẻ đã nằm rõ trong package hiện hữu; nếu chưa có quyền gửi clip ra chat, phải xin gói bổ sung hữu hạn **trước khi xuất file**.

## 2. Tạo clip NGẮN thực tế trên máy đang làm việc

1. Chỉ thao tác trên thiết bị `deviceId` đã xác thực qua Remote Desktop Commander. Đối chiếu timecodes/clip IDs với `SOURCE_MOVIE` read-only và `JOB_DIR` đã duyệt; không quét thư mục khác.
2. Dùng FFmpeg đã có/được phép để trích các **clip 5–30 giây** điển hình, ưu tiên MP4 H.264/AAC yuv420p; đoạn nghe lời thoại thường **10–60 giây** thành WAV PCM 16k mono hoặc M4A. Chỉ tăng thời lượng khi cần thực sự kiểm một hành động/âm thanh liên tục, tối đa video 60s, audio 240s mỗi file; phải nằm trong ngân sách xuất dữ liệu được duyệt. Nếu chuyển động cần bằng chứng, gửi **clip/video thật** cùng frame/contact sheet hỗ trợ (frame không thay cho chuyển động). Nếu lỗi âm cần nghe, phải có audio gốc đủ rõ, không chỉ spectrogram/transcript.
3. Mọi file được trích vào `JOB_DIR/analysis/snippets/` hoặc nhánh con thuộc `JOB_DIR` dưới tên riêng; không đụng file nguồn, không ghi đè checkpoint/version. Tạo tệp yêu cầu JSON liệt kê item relative to JOB_DIR, `kind`, `start_s`, `end_s`; gói video/audio/ảnh liên quan có thể ở **một ZIP**, không cần hỏi từng file.
4. Dùng `tools/media_evidence_handoff.py build --job-dir <JOB_DIR> --request-id <ID> --stage <Gxx> --question "..." --items-json <JOB_DIR/.../items.json>` sau khi xác thực đã được phép chạy tool + xuất media. File ZIP xuất `JOB_DIR/analysis/media_for_chat/<request_id>/REVIEW_PHIM_<stage>_<request_id>_MEDIA.zip`, kèm `manifest.json`, SHA-256 và bytes thật. Mặc định 1–6 item, tổng nguồn ≤30 MiB/ZIP; nếu lớn hơn phải trích ngắn/chuyển codec/giảm bitrate/split thành **gói hữu hạn mới**. Không ép gửi file lớn hoặc mất phần hành động quyết định. Script đóng gói sẵn file; **không** tự trích phim, chuyển file, cấp quyền hoặc thực sự xem/nghe.
5. Kiểm ZIP `verify` trước cung cấp file. Manifest chứa `request_id`, stage, question, timecodes, source relpaths, từng SHA-256, và `inspected_by_chatgpt=false`. ZIP PASS chỉ có nghĩa là file đã đóng gói đúng; **chưa được xem/nghe**.

## 3. BẮT BUỘC báo người dùng và gắn link khi thật sự có

- ChatGPT chủ động nói rõ **vì sao cần xem/nghe**, giai đoạn/timecodes, số file, ZIP thực tế, kích thước, SHA-256, và hướng dẫn **người dùng tải ZIP, gửi ZIP trở lại hội thoại ChatGPT này**. Nếu cần, người dùng giải nén ZIP trên máy và tải trực tiếp từng `.mp4`/`.wav`/`.m4a`/ảnh vào chat để ChatGPT thật sự tiếp cận media; chỉ attach ZIP có thể **không** giúp ChatGPT nghe/phát trực tiếp tùy khả năng phiên làm việc.
- Trước tiên kiểm tra công cụ truyền file **thật sự được cấp quyền và hiện có** từ thiết bị remote tới vùng file có thể tải của ChatGPT. **Chỉ** cung cấp `[Tải ZIP](sandbox:/mnt/data/<exact_file>.zip)` khi ZIP đã được đưa vào **đúng container phiên hiện tại**, đường dẫn tồn tại, bytes/size và SHA256 khớp; hoặc URL tải về khác **chỉ** nếu nguồn/đường dẫn thật đã được công cụ xác minh và người dùng có thể truy cập. **Không tự tạo link giả** từ đường dẫn Windows, không dùng `file://`, `localhost`, địa chỉ LAN/private hoặc link cloud tự đoán. Không tự mở HTTP server/port, đẩy lên drive, thay firewall, bật chia sẻ công khai.
- Remote Desktop Commander **không mặc định bảo đảm truyền được ZIP video/audio về ChatGPT** chỉ từ `read_file`, `get_file_info`, `start_process`. Nếu đường truyền không hỗ trợ, trạng thái `ZIP_READY_NEEDS_TRANSFER`, thông báo chính xác `CHƯA CÓ LINK TẢI TRỰC TIẾP`; chỉ cung cấp **đường dẫn ZIP trên thiết bị thật** để người dùng tự mở/thao tác, upload vào chat, không giả vờ người dùng đã tải được. Khi có tính năng transfer rõ ràng được xác minh, tạo link tải có chứng cứ; nếu không, báo giới hạn và đưa thao tác thủ công ngắn gọn.
- Mẫu thông báo: **"[REVIEW_PHIM G08] Tôi cần xem clip 01:34–01:45 và nghe đoạn 01:39–01:45 để xác định nhân vật/hành động. Đã tạo `REVIEW_PHIM_G08_G08-EV-001_MEDIA.zip` (2 file, [X MiB], SHA-256: ...). [Tải ZIP — chỉ khi link đã xác minh]. Vui lòng tải, đính kèm ZIP vào chat; nếu ZIP không xem/nghe được, giải nén và gửi MP4 + WAV riêng. Tôi sẽ kiểm tra trước khi kết luận Q08."**

## 4. Khi người dùng gửi ZIP/MP4/WAV vào ChatGPT

- Đầu tiên xác nhận attachment thực tế đã xuất hiện (không đoán từ tên file), đọc bytes/manifest, kiểm SHA-256 nếu có, request_id/timecodes và giới hạn đọc; `tools/media_evidence_handoff.py verify --zip ... --sha256 ...` chỉ xác minh tính toàn vẹn. Trạng thái receipt = `RECEIVED_NOT_INSPECTED`.
- Sau đó ChatGPT thực sự **trực tiếp** xem frame/clip có timestamp bằng khả năng đa phương thức hiện tại, và **thực sự** nghe/phân tích âm thanh qua đầu vào/công cụ audio có hỗ trợ. Nếu chỉ xem frame tĩnh thì chỉ xác nhận hình tĩnh, không tự suy chuyển động; nếu chỉ đọc ASR/text/FFT mà không nghe được âm thanh, không ghi `HEARD_VERIFIED`/"đã nghe". Nếu giải nén ZIP trong ChatGPT nhưng không phát được định dạng, đề nghị gửi **file media riêng** tương thích, không tự nâng gate lên PASS.
- Lập `qc/media_evidence_requests/<request_id>.json` và `.md` trong `JOB_DIR` khi đã được phép ghi: attachment metadata/hash, timecodes đã thật sự xem/nghe, lỗi phát hiện, sửa chữa đề xuất hoặc kết luận `VERIFIED_VISUAL`/`HEARD_VERIFIED`/`NEEDS_FIX`/`NOT_VERIFIED`, `observed_by_chatgpt` và giới hạn. **Không** coi receipt, FFprobe, model candidate, transcript, thumbnail, manifest hay ZIP đã tạo là chứng cứ thị giác/thính giác hoàn chỉnh.
- Audio không có upload ở giai đoạn G02/G03/G07/G13/G14: giữ parent package `WAITING_FOR_AUDIO_UPLOAD` (state cũ); video/hình không được upload: `NOT_VERIFIED` hoặc `BLOCKED` theo phụ thuộc và ghi nhãn `MEDIA_UPLOAD_PENDING` trong QC phụ; không tự tạo enum `WAITING_FOR_MEDIA_UPLOAD` khi `tools/work_package_state.py` chưa có. Nếu đã nhận nhưng không thể nghe/xem: `NOT_VERIFIED`. Được tiếp tục task **không phụ thuộc** trong phạm vi gói đã duyệt, không báo PASS nhầm.
- Sau khi dữ liệu đã thực sự được xem/nghe và giải quyết issue, cập nhật QC cấp stage và tiếp tục **cùng package đã được phê duyệt**, không tự mở rộng source/model/output/budget; sửa video/audio theo repair budget, QC lại. Nếu vượt quyền sửa hoặc cần đổi nguồn thì xin gói scope mới. Các snapshot/ZIP/version đều append-only, không xóa nguồn.

## 5. Acceptance và kiểm thử

- **Hard fail**: có request quan trọng nhưng không ZIP hoặc ZIP không thật; link download chưa được xác minh; ZIP không hash; file trích ngoài JOB_DIR/quyền; upload chưa có mà ghi `HEARD_VERIFIED`/`VERIFIED_VISUAL`; clip không đủ timecodes/âm thanh/motion để trả lời; gate PASS chỉ nhờ ASR/log.
- **Cho phép báo chờ đúng thực tế** nếu remote không thể truyền file. Phải có thông báo rõ ràng + đường dẫn máy, không dựng link giả. Trải nghiệm "download link" tự động chỉ hoàn chỉnh khi connector hỗ trợ đưa file ra vùng có thể tải hoặc user có cách tải trực tiếp đã kiểm chứng.
- **Không thay đổi** quy trình 15 G-stage, G11A/B, human gates G05_SCRIPT, G07_VOICE, G10_PILOT, G11A_METADATA, G11B_THUMBNAIL, G15_DELETE; package scopes/hash, nguồn read-only, `work_package.lock`, G14 3 nhánh QC độc lập; áp dụng quy tắc này xuyên giai đoạn dưới dạng **ngoại lệ có bằng chứng**.

</details>
