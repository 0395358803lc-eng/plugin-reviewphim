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

# REVIEW_PHIM v1.3.19 — G11A YouTube Metadata (sau G11, trước G11B)

## Mục tiêu và phạm vi
Thêm bước **G11A.YOUTUBE_METADATA.FULL** trong G01–G15 giữ nguyên, chỉ sau Q11 render PASS/G10_PILOT đã duyệt, trước G11B và G12. Một nhiệm vụ, một Q11A; không chia Mnn hoặc xin duyệt từng tiêu đề. Hành vi là tạo nội dung để người dùng đăng video, **không tự đăng YouTube**, không mở rộng quyền publish hoặc quyền trên máy. Bản render G11 bất biến, lưu mới trong `JOB_DIR`.

## Nguồn và thuật toán biên tập
1. Đọc `review/review_ke_chuyen.txt`, review đã được G05_SCRIPT phê duyệt, G04 `story_map`, nhân vật, tên phim/năm và kênh từ profile người dùng đã xác nhận. Không suy đoán hãng phim, bản quyền, diễn viên hoặc giải thưởng nếu chưa có chứng cứ. Có thể đọc MP4 G11 bằng frame thật nếu được cấp quyền; không chỉ suy đoán từ tên file.
2. ChatGPT viết 3–5 tiêu đề đề xuất dạng khác nhau, nêu lý do; **không quá 100 ký tự** mỗi tiêu đề; không nhồi từ khóa, gây hiểu lầm hoặc dùng thông tin phim khác. Phong cách ảnh mẫu như `[REVIEW PHIM] …` là gợi ý, không nhân bản kênh/nhãn của người khác.
3. Mô tả có phần tóm tắt ngắn, tên phim (nếu xác minh), lời mời đăng ký theo profile kênh, hashtag liên quan, nguồn/ghi công khi có, các thông tin về quyền khi được người dùng xác nhận. **Không tự thêm disclaimer 'fair use' và không bảo đảm disclaimer tránh được copyright claim.**
4. Chọn một `title_selected` từ các tiêu đề có thật, bằng phê duyệt người dùng `G11A_METADATA`. Nếu user chỉnh, viết phiên bản mới; title đã duyệt tạo SHA-256 và bị khóa làm đầu vào G11B.

## Dữ liệu đầu ra trong JOB_DIR
- `publish/title_candidates.json`: `schema_version`, `source_review_sha256`, `source_movie_sha256`, `candidate_titles` 3–5, `reasons`, `channel_profile_ref`, `status`.
- `publish/title_selected.txt` chỉ được ghi là **selected** sau human gate G11A_METADATA; lưu `publish/title_approval.json` gồm `approval_ref`, `selected_index`, `title_sha256`, thời gian/phiên.
- `publish/youtube_description.txt`, `publish/youtube_metadata.json`: `title`, `description`, `hashtags`, `tags`, `film_identity`, `source_refs`, `approval_ref`, `hashes`; `qc/g11a_metadata_qc.md`.
- Không tạo URL video hoặc trạng thái đã đăng; metadata chỉ để sử dụng sau khi đăng.

## QC và cổng
Q11A kiểm đủ nguồn G04/G05/G11, tên phim/chủ thể, độ dài tiêu đề, nội dung mô tả, hashtag, hash. `G11A_METADATA_READY` chỉ sau Q11A đạt + người dùng chọn và duyệt tiêu đề. Thiếu duyệt -> `WAITING_FOR_HUMAN_APPROVAL`; không tự G11B. Title thay đổi sau G11B làm invalidate ảnh, văn bản ảnh, clip intro và G12–G15 liên quan; không ghi đè phiên bản đã duyệt.

</details>
