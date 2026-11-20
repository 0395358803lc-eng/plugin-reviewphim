# REVIEW_PHIM v1.3.19 — G11B Thumbnail + Poster bằng ChatGPT

> **CẬP NHẬT BẮT BUỘC v1.3.24:** [MANUAL_THUMBNAIL_HANDOFF_V1324.md](MANUAL_THUMBNAIL_HANDOFF_V1324.md) thay thế yêu cầu chuyển ảnh tự động tại bước 5. Người dùng sẽ tải ảnh từ ChatGPT và **tự chép** vào đúng `JOB_DIR/assets/youtube_thumbnail.png` (hoặc `.jpg` thật). Chờ xác nhận đặt file + duyệt G11B trong một tin nhắn, rồi ChatGPT kiểm lại file thật/hash/visual QC. Không báo lỗi `BLOCKED_TRANSFER` chỉ vì Remote Desktop không có chức năng upload.

## Mục tiêu
Sau `G11A_METADATA_READY`, ChatGPT tạo **ảnh thật** 16:9 có tiêu đề đã chọn, tham khảo tinh thần thumbnail phim người dùng gửi (sắc nét, tập trung nhân vật, kiểu chữ nổi bật) nhưng không sao chép layout/logo/kênh của người khác. Ảnh được dùng **cả thumbnail riêng** và **intro poster 2 giây** tại G12. Một G11B, một Q11B, một cổng `G11B_THUMBNAIL` cho người dùng chọn/duyệt.

## Quy trình bắt buộc
1. Đọc `publish/title_selected.txt` và xác thực `title_sha256` cùng `G11A_METADATA` còn hiệu lực; truy phim G04/G05 và chọn hình/cảnh có evidence hình thật. Chỉ dùng tài sản người dùng có quyền sử dụng hoặc hình AI được phép tạo; không ngụ ý poster là cảnh phim chính thức nếu là ảnh minh họa AI.
2. ChatGPT sử dụng **công cụ tạo ảnh của ChatGPT thật** khi có; không tuyên bố đã tạo khi chỉ viết prompt. Nếu cần, tạo nền 16:9 sau đó dùng trình ghép chữ cục bộ đã được phê duyệt (ví dụ Pillow) để đặt **chính xác** tiếng Việt và ký tự từ tiêu đề được chọn. Không cài thư viện mới hay tự sửa font/OS nếu chưa cho phép. Có thể dùng tiêu đề rút gọn trên ảnh khi người dùng duyệt riêng; mặc định chữ trên ảnh phải đúng tiêu đề đã chọn.
3. Tạo ảnh phù hợp 16:9, tối thiểu 640 px bề ngang; khuyến nghị 1280×720 hoặc lớn hơn. Tối ưu đọc được trên di động, safe area, tránh mặt nhân vật/vật chứng, kiểm chữ dấu Việt, không cắt text. Đừng khẳng định YouTube sẽ lấy 2 giây đầu làm thumbnail.
4. **Kiểm tra bằng mắt thật** kết quả render và chữ (không pass chỉ từ metadata/JSON). Nếu lỗi font, chữ sai dấu, nội dung khác title, vỡ ảnh, hình sai phim → `NEEDS_FIX`, sửa rồi nhìn lại. Lưu evidence ảnh đã xem và trạng thái `VISUALLY_VERIFIED`.
5. **Mặc định chuyển thủ công:** ChatGPT đưa ảnh thật để người dùng tải, chỉ định một đường dẫn trong `JOB_DIR/assets/` và chờ người dùng tự chép ảnh vào đích. Khi người dùng xác nhận “ĐÃ CHÉP ẢNH VÀ DUYỆT G11B”, kiểm file trên máy thật, SHA-256, định dạng, đúng title và QC trực quan theo MANUAL_THUMBNAIL_HANDOFF_V1324.md. Không tự truyền file từ ChatGPT, không bịa path, không tự PASS trước khi file hiện hữu. Chờ thì ghi `WAITING_FOR_USER_IMAGE_PLACEMENT` là substatus, không mở lượt phê duyệt triển khai thứ hai.

## Đầu ra
- `assets/youtube_thumbnail.png` (hoặc JPG đúng format do người dùng tự chép) là nguồn sự thật duy nhất; `assets/intro_card.png` chỉ là dẫn xuất tùy chọn trong JOB_DIR nếu trình render cần, không bắt buộc nhân bản; `assets/thumbnail_generation.json` (prompt, source ref, model/tool thực tế, style, title hash, source SHA, output hash, generated-at).
- `assets/thumbnail_visual_evidence/` (frame/ảnh hiển thị thực tế, evidence references, người kiểm); `qc/g11b_thumbnail_qc.md`.
- `publish/thumbnail_approval.json`: `G11B_THUMBNAIL`, user approval, approved image hash, title hash.

## QC và human gate
`Q11B=PASS` chỉ nếu (a) title đã duyệt, (b) hình thật đã tạo và đọc được, (c) evidence visual thật, (d) ảnh thực tồn tại trong JOB_DIR và hash trùng, (e) người dùng duyệt `G11B_THUMBNAIL`; nếu thiếu chờ phê duyệt, nếu người dùng chưa đặt file thì giữ `WAITING_FOR_HUMAN_APPROVAL`/substatus `WAITING_FOR_USER_IMAGE_PLACEMENT` (không mặc định lỗi transfer); nếu đã đặt nhưng QC chưa đạt thì `NOT_VERIFIED`/`NEEDS_FIX`. Hình hoặc title thay đổi phải tạo bản mới và xin duyệt lại; invalidate G12 intro/G14/Q15 khi phụ thuộc. Nếu user chọn `NO_THUMBNAIL`, yêu cầu quyết định rõ cho G12 và không tuyên bố đã dùng thumbnail.

## YouTube
Theo YouTube Help `https://support.google.com/youtube/answer/72431`: video thường nên dùng thumbnail tỷ lệ 16:9; file JPG/PNG và account cần được xác minh để dùng custom thumbnail. Upload file ảnh làm **custom thumbnail** trong YouTube Studio là bước riêng; chèn ảnh 2 giây vào MP4 không bảo đảm thumbnail hiển thị đúng trên trang chủ. Việc đăng/tải ảnh lên YouTube nằm ngoài phạm vi plugin nếu chưa có quyền publish được người dùng cấp.
