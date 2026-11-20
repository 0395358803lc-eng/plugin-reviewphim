# REVIEW_PHIM v1.3.19 — G11B Thumbnail + Poster bằng ChatGPT

## Mục tiêu
Sau `G11A_METADATA_READY`, ChatGPT tạo **ảnh thật** 16:9 có tiêu đề đã chọn, tham khảo tinh thần thumbnail phim người dùng gửi (sắc nét, tập trung nhân vật, kiểu chữ nổi bật) nhưng không sao chép layout/logo/kênh của người khác. Ảnh được dùng **cả thumbnail riêng** và **intro poster 2 giây** tại G12. Một G11B, một Q11B, một cổng `G11B_THUMBNAIL` cho người dùng chọn/duyệt.

## Quy trình bắt buộc
1. Đọc `publish/title_selected.txt` và xác thực `title_sha256` cùng `G11A_METADATA` còn hiệu lực; truy phim G04/G05 và chọn hình/cảnh có evidence hình thật. Chỉ dùng tài sản người dùng có quyền sử dụng hoặc hình AI được phép tạo; không ngụ ý poster là cảnh phim chính thức nếu là ảnh minh họa AI.
2. ChatGPT sử dụng **công cụ tạo ảnh của ChatGPT thật** khi có; không tuyên bố đã tạo khi chỉ viết prompt. Nếu cần, tạo nền 16:9 sau đó dùng trình ghép chữ cục bộ đã được phê duyệt (ví dụ Pillow) để đặt **chính xác** tiếng Việt và ký tự từ tiêu đề được chọn. Không cài thư viện mới hay tự sửa font/OS nếu chưa cho phép. Có thể dùng tiêu đề rút gọn trên ảnh khi người dùng duyệt riêng; mặc định chữ trên ảnh phải đúng tiêu đề đã chọn.
3. Tạo ảnh phù hợp 16:9, tối thiểu 640 px bề ngang; khuyến nghị 1280×720 hoặc lớn hơn. Tối ưu đọc được trên di động, safe area, tránh mặt nhân vật/vật chứng, kiểm chữ dấu Việt, không cắt text. Đừng khẳng định YouTube sẽ lấy 2 giây đầu làm thumbnail.
4. **Kiểm tra bằng mắt thật** kết quả render và chữ (không pass chỉ từ metadata/JSON). Nếu lỗi font, chữ sai dấu, nội dung khác title, vỡ ảnh, hình sai phim → `NEEDS_FIX`, sửa rồi nhìn lại. Lưu evidence ảnh đã xem và trạng thái `VISUALLY_VERIFIED`.
5. Bắt buộc **chuyển bytes ảnh thật vào `JOB_DIR` qua đường truyền file thực tế có sẵn**, kiểm tồn tại file + hash. Remote Desktop Commander có thể không có đường upload ảnh từ chat đến máy; khi chưa có kênh truyền file được kiểm chứng, ghi `BLOCKED_TRANSFER` và trình phương án người dùng tải ảnh vào JOB_DIR; không giả đã lưu chỉ bằng đường dẫn ChatGPT. Chỉ dùng root đã được duyệt.

## Đầu ra
- `assets/youtube_thumbnail.png` (hoặc JPG) + `assets/intro_card.png` (có thể cùng bytes; hash ghi rõ); `assets/thumbnail_generation.json` (prompt, source ref, model/tool thực tế, style, title hash, source SHA, output hash, generated-at).
- `assets/thumbnail_visual_evidence/` (frame/ảnh hiển thị thực tế, evidence references, người kiểm); `qc/g11b_thumbnail_qc.md`.
- `publish/thumbnail_approval.json`: `G11B_THUMBNAIL`, user approval, approved image hash, title hash.

## QC và human gate
`Q11B=PASS` chỉ nếu (a) title đã duyệt, (b) hình thật đã tạo và đọc được, (c) evidence visual thật, (d) ảnh thực tồn tại trong JOB_DIR và hash trùng, (e) người dùng duyệt `G11B_THUMBNAIL`; nếu thiếu chờ phê duyệt, nếu transfer chưa xong BLOCKED/NOT_VERIFIED. Hình hoặc title thay đổi phải tạo bản mới và xin duyệt lại; invalidate G12 intro/G14/Q15 khi phụ thuộc. Nếu user chọn `NO_THUMBNAIL`, yêu cầu quyết định rõ cho G12 và không tuyên bố đã dùng thumbnail.

## YouTube
Theo YouTube Help `https://support.google.com/youtube/answer/72431`: video thường nên dùng thumbnail tỷ lệ 16:9; file JPG/PNG và account cần được xác minh để dùng custom thumbnail. Upload file ảnh làm **custom thumbnail** trong YouTube Studio là bước riêng; chèn ảnh 2 giây vào MP4 không bảo đảm thumbnail hiển thị đúng trên trang chủ. Việc đăng/tải ảnh lên YouTube nằm ngoài phạm vi plugin nếu chưa có quyền publish được người dùng cấp.
