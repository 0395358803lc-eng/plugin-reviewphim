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

# MANUAL_THUMBNAIL_HANDOFF_V1324 — ChatGPT tạo ảnh, người dùng tự chép vào máy từ xa

> **v1.3.25 — PRODUCTION_FIRST_V1325:** Với gói mới đã duyệt mode này, ưu tiên [PRODUCTION_FIRST_AUTONOMOUS_V1325.md](PRODUCTION_FIRST_AUTONOMOUS_V1325.md). Các Qxx/QC thẩm mỹ, nghe/xem, web và phê duyệt sáng tạo giữa giai đoạn trong tài liệu dưới đây là **LEGACY-ONLY**; mode mới dùng DONE đầu ra kỹ thuật và chờ user nghiệm thu cuối. Giữ nguyên quyền thiết bị/source/install/delete và thao tác chép thumbnail thật.


**ƯU TIÊN CAO NHẤT cho G11B và đầu vào ảnh của G12, từ REVIEW_PHIM v1.3.24.** Ghi đè yêu cầu truyền ảnh tự động và `BLOCKED_TRANSFER` mặc định trong `THUMBNAIL_INTRO_POLICY_V1319.md`, `INTRO_CARD_INTEGRATION_V1319.md`, `SKILL.md` và mọi tài liệu cũ **chỉ về phương thức chuyển ảnh ChatGPT → JOB_DIR**. Giữ nguyên quyền thiết bị, nguồn phim chỉ đọc, Q11A/G11A_METADATA, hình thật, Q11B/G11B_THUMBNAIL, Q12, file/hash, lock, visual QC, G14, quyền xử lý video và không chuyển quyền phê duyệt thành tự động.

## Mục tiêu — chỉ một thao tác chuyển thủ công

1. Sau Q11 và `G11A_METADATA`, ChatGPT **thật sự tạo thumbnail 16:9** bằng công cụ tạo ảnh, có chữ đúng tiêu đề đã được duyệt và đã xem/kiểm tra kết quả hiển thị. Chỉ nói có ảnh khi tool thực sự trả ảnh. Đưa cho người dùng ảnh để tải bằng cơ chế download thực tế của ChatGPT; chỉ đưa `sandbox:/...` khi đường dẫn tồn tại và đã được kiểm chứng trong phiên. Không tạo URL tải giả từ file Windows/remote.
2. Chỉ định **một đích chính xác** trên đúng máy `deviceId` đã chọn, thay `JOB_DIR` bằng đường dẫn đầy đủ đã được phê duyệt. Mặc định **`<JOB_DIR>\assets\youtube_thumbnail.png`**. Nếu ChatGPT xuất JPG, báo trước `...\assets\youtube_thumbnail.jpg` (hoặc `.jpeg`) theo **định dạng thực**, không chỉ đổi tên đuôi. Folder `assets` phải tồn tại trong `JOB_DIR` đã duyệt; chỉ tạo nếu gói cho phép, không tạo ngoài root, không tự ghi sang workspace khác.
3. Hướng dẫn người dùng tải ảnh xuống máy và **tự copy/move** vào đúng vị trí trên thiết bị làm phim; không dùng Remote Desktop Commander để upload ảnh từ ChatGPT, không yêu cầu mở server/drive/cloud và không xin quyền chuyển file tự động. **G11B chờ** `WAITING_FOR_HUMAN_APPROVAL` trong state core; ghi substatus `WAITING_FOR_USER_IMAGE_PLACEMENT` để chỉ rõ đang chờ người dùng đặt file. Không hạ gate thành PASS, không gửi thêm kế hoạch triển khai chỉ vì chờ thao tác này.
4. Sau đặt ảnh, gửi một tin nhắn rõ ràng **`ĐÃ CHÉP ẢNH VÀ DUYỆT G11B`**. Đây là **một lần xác nhận bao gồm đặt file + chấp thuận ảnh G11B_THUMBNAIL**, nếu thực sự do người dùng gửi và chỉ cho đúng ảnh/tiêu đề. Nếu người dùng chỉ nói “đã chép”, chưa có phê duyệt ảnh thật thì giữ `WAITING_FOR_HUMAN_APPROVAL`; nếu trước đó đã chọn/duyệt ảnh và có bằng chứng hợp lệ, dùng lại phê duyệt ấy không cần duyệt lặp. Không tự tạo user approval hoặc dùng tín hiệu tạo ảnh làm quyết định người dùng.
5. ChatGPT tiếp tục **cùng WORK_PACKAGE_ID**, kết nối lại đúng `deviceId/link_id`, kiểm đường dẫn dưới `JOB_DIR`, file tồn tại là regular file, không symlink/junction/reparse ra ngoài, PNG/JPG signature phù hợp, 16:9, width≥640, decode bằng FFmpeg/Pillow đã được phép, và SHA-256 bytes trên máy. Có thể dùng `tools/manual_thumbnail_handoff_v1324.py::handoff_destination` để xác định đích và `verify_drop` để kiểm metadata/path/hash/human record. Tool chỉ kiểm offline, không kết nối máy hay giải mã ảnh hoàn chỉnh. Không PASS từ “người dùng đã chép” khi chưa có file thực.
6. Đối chiếu tiêu đề và ảnh đã tạo trong chat với asset trên máy: nếu có SHA-256 nguồn ở ChatGPT, **bắt buộc so sánh exact bytes**. Nếu không có SHA-256 nguồn, ghi `image_identity=USER_ATTESTED_NOT_BYTE_MATCHED`, nêu rõ sự trùng khớp bit chưa chứng minh và dựa vào lựa chọn của người dùng cộng với kiểm tra ảnh thực ở máy nếu có khả năng. Nếu ảnh/mô tả khác, JPG giả PNG, thiếu hoặc sai hash → `NOT_VERIFIED/NEEDS_FIX/BLOCKED` tương ứng; không gán `VISUALLY_VERIFIED` cho asset từ metadata đơn thuần.
7. **Chỉ sau** file được kiểm và ảnh thực được xác nhận đúng content bằng Q11B cùng user gate `G11B_THUMBNAIL`, lưu `publish/thumbnail_approval.json`: `approval_ref`, `title_sha256`, `image_sha256`, `image_relpath` (`assets/youtube_thumbnail.png` hoặc `.jpg`), size, format, dimensions, identity_assurance, visual_evidence_ref, file_hash_checked_at, deviceId, JOB_DIR. Tạo `qc/g11b_thumbnail_qc.md` kèm chứng cứ thật. Giữ nguyên ảnh được người dùng chép; không tự ghi đè/đổi nội dung.
8. G12 dùng **chính file có `image_relpath` + SHA-256 được khóa** từ approval G11B để làm intro tĩnh 2 giây và thumbnail riêng. Có thể đọc file PNG/JPG trực tiếp bằng FFmpeg; không bắt buộc tạo `assets/intro_card.png` thứ hai. Nếu công cụ đã duyệt cần file trung gian, tạo file dẫn xuất **trong JOB_DIR** với lineage/hash và không ghi đè file cũ, nhưng không tạo thêm cổng phê duyệt transfer. Q12 vẫn kiểm hình intro, thời lượng 2 giây, logo và bắt đầu TTS sau intro.

## Trạng thái và tránh vòng lặp

- `WAITING_FOR_USER_IMAGE_PLACEMENT` **chỉ là substatus mô tả**, không thay enum core; dùng core `WAITING_FOR_HUMAN_APPROVAL` và chờ một hành động người dùng. File chưa có → đưa lại **đúng** đường dẫn, không chạy lại ChatGPT tạo ảnh/khởi đầu G11B nếu ảnh vừa tạo vẫn còn.
- Sai tên/đuôi/path → chỉ sửa hướng dẫn đặt ảnh hoặc chọn đúng file. Sai chất lượng hoặc title → sửa ảnh mới rồi lấy phê duyệt revision mới, invalidate G11B/Q12–Q15 phụ thuộc như quy tắc hiện hành. Không cấp quyền đổi nguồn, file hay model ngoài package.
- Khi người dùng gửi tin xác nhận, kiểm remote ngay trong lượt hiện tại nếu có quyền và công cụ; không tạo nút “duyệt triển khai” mới. Không hứa chạy nền khi đã hết phiên, không tuyên bố G12 đã render từ việc thấy file.
- Nếu người dùng chủ động chọn `NO_THUMBNAIL`/`NO_INTRO`, xử lý theo quyết định cụ thể và quy trình legacy/scope, không tự giả image/approval.

## Hợp đồng kiểm thử

`tools/manual_thumbnail_handoff_v1324.py` kiểm file allowlist dưới JOB_DIR, tránh symlink phổ biến, signature PNG/JPEG, kích thước/aspect, SHA, user action và hình ChatGPT đã thực sự thấy. **Trả `FILE_ACCEPTED` không đồng nghĩa Q11B PASS**: còn bắt buộc kiểm giải mã/hiển thị và ghi QC thật. Các ca thiếu file, chưa có user approval, sai title, sai source hash, file giả/khác tỷ lệ, symlink phải bị chặn. Không tự động chuyển ảnh sang máy, không chỉnh sửa file trên máy chỉ bằng policy helper. Plugin v1.3.24 không tự nghiệm thu thiết bị thực; phải đo trên project thật.

</details>
