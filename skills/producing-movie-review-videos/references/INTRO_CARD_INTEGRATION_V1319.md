# REVIEW_PHIM v1.3.19 — G12 Intro Card 2s + logo

> **ƯU TIÊN v1.3.24:** [MANUAL_THUMBNAIL_HANDOFF_V1324.md](MANUAL_THUMBNAIL_HANDOFF_V1324.md) quy định ảnh từ ChatGPT được **người dùng chép thủ công** vào `JOB_DIR/assets/youtube_thumbnail.png` hoặc JPG, sau đó ChatGPT kiểm file/hashes và lưu `publish/thumbnail_approval.json:image_relpath`. G12 lấy file đúng `image_relpath` đã được duyệt, không mặc định phải có `assets/intro_card.png` hay kênh remote upload. G11B Q11B/human gate vẫn bắt buộc trước G12.

## Thứ tự chuẩn
`G11 Q11 PASS` → `G11A (Q11A + G11A_METADATA)` → `G11B (Q11B + G11B_THUMBNAIL)` → `G12` → `G13` → `G14` → `G15`. Giữ mã G12–G15 hiện hành; legacy job không yêu cầu bổ sung gate mới nếu gói cũ không bao gồm G11A/G11B. Gói mới bao gồm các bước này phải khóa dependency. Không tự nâng quyền của các gói đang chạy hoặc sửa checkpoint cũ.

## Nguồn và cách ghép
- Input bắt buộc: `G11` MP4 render hợp lệ (hash), ảnh thật `image_relpath` + `image_sha256` trong `publish/thumbnail_approval.json` (mặc định `assets/youtube_thumbnail.png`, JPG nếu đúng format), `publish/title_selected.txt` và approval khớp cùng `G11B_THUMBNAIL`, brand profile/logo của job đang làm.
- Tạo `assets/intro_card_2s.mp4` trực tiếp từ ảnh người dùng đặt qua FFmpeg/Remotion đã được phê duyệt; kiểm lại hash trước khi dựng, không ghi đè ảnh nguồn; đúng **2,000 giây theo timebase/frame output** (`frame_count = 2 * fps` nếu fps nguyên; với fps phân số phải dùng cách quy đổi timestamp/frame chính xác và ghi chênh lệch thực). Không lấy duration ước chừng từ container để tuyên bố chính xác; xác minh bằng FFprobe/PTS và frame đầu/cuối.
- Nối đoạn intro vào đầu bản G11 và giữ video/voiceover G11 bắt đầu **sau** intro, không làm mất tiếng đầu, không lặp frame/gây khung đen, không phát chồng giọng/tiếng phim. Nếu cần concat đổi codec, tính lại PTS/audio sync và ghi hash output; không phá G11 source. G12 áp logo/watermark theo brand profile được duyệt, tránh che chữ mặt nhân vật, không mặc định kênh/logo mẫu.
- Nếu G12 hiện đã có intro cũ, **không ghép hai lần**; tính `intro_integration_id` từ hash phim/ảnh/title/profile để tái sử dụng kết quả PASS hoặc tạo revision mới có lineage. Nếu profile kênh không muốn intro, cần quyết định rõ và ghi `INTRO_SKIPPED_BY_USER`.

## Đầu ra
- `assets/intro_card_2s.mp4`, `timeline/intro_integration.json` (source hashes, title hash, 2s target, fps num/den, frames, actual duration, video/audio start, FFmpeg/Remotion command, logo config, idempotency ID), `output/video_with_intro.mp4`, `qc/g12_intro_brand_qc.md`.
- Q12 gồm QC hình thật (ảnh đúng, dấu chữ, 2s đầu), so before/after, giọng mở đầu không mất, logo đúng kênh, audio zero/nhạc intro có duyệt, tổng duration = G11 + intro trong dung sai frame. Không PASS chỉ từ log. G13 mix tiếp trên bản G12. G14 xác nhận 3 nhánh quality như cũ và kiểm intro trong MP4 sau G13. G15 giao đủ MP4, thumbnail JPG/PNG riêng, title/description/hashtags, hashes, source project và không xóa nếu không duyệt G15_DELETE.

## Giới hạn
Plugin chỉ sản xuất và bàn giao thumbnail/metadata/intro; không tự upload hay đổi YouTube Studio. Muốn thumbnail trang chủ trùng ảnh đã tạo phải **upload custom thumbnail** theo YouTube Help; YouTube có thể thay đổi hiển thị theo bối cảnh.
