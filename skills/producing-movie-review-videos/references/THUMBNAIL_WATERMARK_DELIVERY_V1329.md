# REVIEW_PHIM v1.3.29 — Thumbnail riêng + logo góc trái

**Chính sách ưu tiên mới, áp dụng cho mọi gói mới sau v1.3.29.** Với gói đã được phê duyệt trước đó, không tự động thay đổi scope, nguồn phim, hash hay checkpoint; nếu người dùng muốn áp dụng cho sản phẩm đang dựng, tạo revision đúng phần phụ thuộc và giữ MP4 cũ.

## Nghiệp vụ bắt buộc

- G11B tạo đúng thumbnail YouTube 16:9 (khuyến nghị 1280×720 JPG/PNG), đúng phim/tiêu đề, xuất **ảnh độc lập** để người dùng tải về từ ChatGPT hoặc đường dẫn tải đã kiểm chứng. Người dùng **tự tải ảnh lên mục Thumbnail của YouTube Studio khi đăng video**. Không chèn thumbnail vào video, không dùng làm poster, intro, đoạn tĩnh 2 giây, transition, frame đầu, hoặc overlay. Không tự đăng YouTube.
- Thumbnail là sidecar độc lập. G11B cần giao được file ảnh thật và bằng chứng tồn tại/hash; **không buộc người dùng chép thủ công vào JOB_DIR để mở khóa G12**. Khi ảnh chỉ có trong ChatGPT, phải bàn giao ảnh để tải và ghi manifest liên kết (generation_ref, title hash, file SHA nếu có); không nói file đã tồn tại trên máy remote. Nếu kế hoạch yêu cầu thumbnail là output có thật trong JOB_DIR, executor phải đưa vào thư mục được duyệt bằng kênh đã được cấp quyền hoặc tách file đó khỏi `stage_outputs` bắt buộc và dùng manifest stage riêng; không giả `FILE_ACCEPTED`. 
- G12 **không dùng thumbnail** và **không tạo assets/intro_card_2s.mp4**. Dùng video G11 nguyên thời điểm bắt đầu; chèn logo/watermark lấy từ thư mục logo đã được chọn P00 ở **góc trên bên trái (top-left)** từ frame đầu đến frame cuối. Chèn bằng overlay alpha, không phát logo 2 giây ở đầu, không đẩy voiceover lùi 2 giây, không tăng thời lượng video chỉ vì logo.
- Logo: kích thước gợi ý ~8–12% chiều rộng khung, giữ nguyên tỷ lệ, biên an toàn khoảng 2% chiều rộng/cao, alpha theo profile được duyệt (mặc định giữ alpha gốc); không che vùng chữ quan trọng. Nếu hình gốc không có alpha, dùng ảnh gốc không tự xóa nền. Logo luôn là watermark **trong video**, không phải ảnh bìa.
- G13 dùng MP4 đã overlay G12 làm đầu vào để trộn nhạc. G14 chỉ kiểm đủ file, codec/audio giải mã như Production First, cộng kiểm tra cấu hình kỹ thuật bảo đảm G12 không ghép intro/không lệch thời lượng. G15 bàn giao **hai tệp độc lập**: video final MP4 có logo góc trái suốt video, và thumbnail JPG/PNG để người dùng tải về; kèm metadata YouTube và file/project, hash. Không gộp thumbnail vào MP4.

## Contract cho kế hoạch mới

`production_config`/`stage_config` phải thể hiện:

```json
{
  "thumbnail_delivery": "DOWNLOAD_SEPARATELY_UPLOAD_IN_YOUTUBE_STUDIO",
  "thumbnail_embed_in_video": false,
  "intro_card_enabled": false,
  "logo_overlay": {"enabled": true, "position": "top_left", "start": "first_frame", "end": "last_frame", "mode": "persistent_watermark"},
  "g12_input_thumbnail": false
}
```

- `stage_outputs.G11B`: có thể là ảnh đã ghi thật vào JOB_DIR **nếu có quyền transfer**, hoặc manifest bàn giao có thật mà không tuyên bố file ảnh ở JOB_DIR. `stage_outputs.G12`: video đã overlay logo + manifest cấu hình overlay/codec/hash. `stage_outputs.G15`: MP4, metadata, thumbnail file hoặc **manifest liên kết ảnh ChatGPT có thể tải**, không yêu cầu nhúng ảnh vào MP4.
- Với `G11B_THUMBNAIL`, nếu chưa ủy quyền sáng tạo, chờ chọn/duyệt ảnh theo gói; nhưng **không có cổng `USER_IMAGE_PLACEMENT` bắt buộc mới**. Không thêm vòng phê duyệt trung gian. Không sửa ngầm gói legacy.
- Phụ thuộc: G12 chỉ phụ thuộc G11 và logo/profile, **không phụ thuộc G11B thumbnail**. G11A/G11B vẫn có thể chạy để giao ấn phẩm YouTube. Đổi thumbnail không cần render lại G12/G13/video MP4; chỉ cập nhật thumbnail, metadata liên quan và manifest G15. Đổi logo cần dựng lại G12→G13→G14→G15, giữ nội dung G11.

## Quy định chống thoái lui

Bị cấm dùng tên công việc/đầu ra `intro_card_2s.mp4`, `video_with_intro.mp4`, `intro_frames=2*fps`, `VOICE_START_BEFORE_INTRO_END` cho gói mới. Không thêm 2 giây im lặng/ảnh/brand đầu video; không buộc `verify_drop` của v1.3.24 khi thumbnail được giao ở ChatGPT độc lập. Nội dung đoạn mở đầu của kịch bản G05 vẫn được phép có cảnh hấp dẫn/giọng thuyết minh, chỉ bỏ đoạn poster/logo tĩnh.

Việc giữ ảnh cạnh video trong thư mục bàn giao để người dùng tiện lấy là được, nhưng không coi đó là lệnh YouTube đã được đăng.
