# REVIEW_STORYTELLING — G05 Công thức kể chuyện dựa trên bằng chứng

**Điều kiện tiên quyết:** Có `FILM_UNDERSTANDING_READY`, đã được duyệt **riêng G05**, có `story_map`, `visual_events`, `characters`, `evidence_index`, các nguồn thật có thể đọc. Chỉ nhận review mẫu từ người khác làm **tham khảo phong cách**, không coi đó là bằng chứng phim gốc.

## Sáu bước xây dựng toàn bộ REVIEW (giữ đúng công thức đã phê duyệt)

1. **Chọn mở đầu tạo tò mò:** chọn một sự kiện có bằng chứng, đủ gây chú ý nhưng không xuyên tạc và không tiết lộ tất cả. Đặt câu hỏi/hứa hẹn câu chuyện có thể được giải đáp về sau.
2. **Giới thiệu nhân vật và hoàn cảnh:** ai, ở đâu, lúc nào, mong muốn hoặc khó khăn chính. Không nhập nhằng hai người giống nhau hoặc các giai đoạn đời nhân vật.
3. **Kể sự kiện bằng hành động và nguyên nhân:** biến thoại và hành động trên màn hình thành lời dẫn ngôi thứ ba, giữ logic ai làm gì, vì sao, sau đó điều gì xảy ra.
4. **Đẩy xung đột, diễn giải cảm xúc có căn cứ:** nêu cản trở, phản ứng và hậu quả. Mô tả cảm xúc dựa vào hình/thoại; phân biệt *quan sát thấy* với *tôi đoán*. Không chẩn đoán bệnh hoặc gán động cơ như sự thật nếu phim không xác nhận.
5. **Tạo câu hỏi và chuyển tiếp sang biến cố kế tiếp:** trả lời một phần rồi dẫn sang tình tiết khiến người xem tiếp tục theo dõi. Nếu phim có hồi tưởng, đối chiếu `on_screen_order`, `chronological_events` trước khi dùng “trở lại hiện tại / ngược về quá khứ”. Không bịa cliffhanger.
6. **Tập trung cao trào và giải quyết câu chuyện:** tăng nhịp ở các bước ngoặt, hội tụ tuyến đúng nguồn, tóm kết trên phim. Tách phần epilogue đời thực ngoài phim và chứng minh bằng nguồn độc lập.

## Công thức cho từng đoạn REVIEW

`Bối cảnh → Hành động → Nguyên nhân/động cơ → Xung đột → Phản ứng → Hậu quả → Chuyển tiếp`.

Đây là **bộ yếu tố**, không phải bảy câu bắt buộc; mỗi đoạn sử dụng yếu tố cần thiết. Ngôn ngữ tự nhiên, có nhịp: đoạn giải thích có thể dài hơn, đoạn cao trào nhanh/ít câu; giữ chi tiết thay đổi lựa chọn của nhân vật, rút ngắn hội thoại chào hỏi và giải thích không tác động cốt truyện. Mọi chuyển cảnh phải rõ chủ thể, tuyến và thời điểm.

## Quy trình ChatGPT trực tiếp viết

1. Từ `story_map` chọn thông điệp trung tâm, nhân vật và các storyline. Lập `review/review_outline.json` với hook, mở đầu, biến cố khởi phát, xung đột, các cú ngoặt, cao trào, kết thúc, `event_ids` đi cùng mỗi phần và nhãn thời gian trên phim.
2. Viết `review/review_ke_chuyen.txt` theo outline, **ngôi thứ ba**, dùng lời kể mới thay cho chép dài lời thoại. Có thể thêm bình luận dí dỏm phù hợp thể loại/kênh, không áp đặt giọng UNABOMBER hay tiếng lóng cực đoan.
3. Lập `review/review_evidence_map.json` cho mỗi đoạn có mốc ký tự `review_text_range`, danh sách `event_ids`, `claim_type`, `review_status` và nguồn. Không tạo story event mới ở G05, không gán source ids không tồn tại. Các câu `CHARACTER_INFERENCE` phải có cách diễn đạt phù hợp với chứng cứ; `EXTERNAL_FACT` có nguồn bên ngoài hoặc phải loại.
4. QC tính logic: nhân vật/chức danh/thời điểm/vật thể, nối nguyên nhân→hậu quả, so khớp tuyến phi tuyến, tình tiết im lặng, không bỏ/đảo biến cố then chốt, loại lời bình làm sai nghĩa; không tự biến diễn giải thành sự thật phim.
5. Biên tập `review/review_loi_binh_tts.txt` để đọc mượt (nhịp nghỉ, phát âm tên riêng) nhưng **không tự đổi thông tin** so với bản kể đã duyệt. Báo số từ và thời lượng ước tính dựa trên tốc độ đọc thực tế; **không mặc định thời lượng** 10/20/30 phút hoặc làm dài để đủ số phút.
6. Tạo `qc/g05_story_qc.md`: số claims trọng yếu supported/qualified/unresolved, chi tiết phải sửa, đề xuất độ dài, outline đã duyệt hay chưa. Trình nghiệm thu G05; không tự khởi động G06.

## Phân loại claim

- `FILM_FACT`: điều xảy ra thực sự trong phim, phải có event và bằng chứng phù hợp.
- `CHARACTER_INFERENCE`: giải thích suy nghĩ/động cơ, đánh dấu là suy luận khi chưa được nói rõ; không thay thế sự kiện.
- `NARRATOR_COMMENTARY`: bình luận của người kể, không được mâu thuẫn với phim hoặc cổ súy sai lệch thông tin.
- `EXTERNAL_FACT`: lịch sử, hậu trường, đời thực; cần URL/tài liệu được kiểm riêng, hoặc loại khỏi REVIEW.

## Gate REVIEW_STORY_READY

- `review_outline` truy xuất được các event trọng yếu; story events/scene ids tồn tại và được G04 xác thực phù hợp.
- `review_evidence_map` phủ **tất cả khẳng định sự kiện trọng yếu**; `REJECTED` không được giữ trong bản lời bình nghiệm thu; `NEEDS_REVIEW` phải xử lý hoặc giảm/loại câu.
- Mạch truyện và nhân quả đúng phim; không gán hành động, biểu cảm hay nguyên nhân không được kiểm chứng; giọng kể phù hợp yêu cầu người dùng.
- Review vẫn là **DRAFT** cho tới khi người dùng duyệt G05; qua gate chất lượng không tương đương tự động phê duyệt stage kế tiếp.

## Phân biệt các tình huống

- Phim tâm lý/chính kịch: ưu tiên nhịp kể tôn trọng và cảm xúc có chứng cứ; hạn chế tiếng lóng.
- Phim trinh thám/phi tuyến: giữ thứ tự xuất hiện trên màn hình khi nó phục vụ câu hỏi mở; không cố kể tuần tự làm hỏng bí ẩn.
- Phim hành động: các hành vi không lời phải lấy từ ảnh/clip, không suy ra từ âm thanh/nội dung phim khác.
- Phim tiểu sử/dựa trên sự kiện thật: không đánh đồng nội dung *trên màn hình* với lịch sử; phải dẫn nguồn riêng cho kết luận ngoài phim.

## Bổ sung v1.3: Ý đồ hình ảnh trong dàn ý (không đổi sáu bước)

Ở `review/review_outline.json`, mỗi đoạn có thể khai báo `visual_intent_hints`: `visual_moment_hint`, `required_emotion_on_screen`, `event_ids` nguồn. Đây chỉ là gợi ý loại hình cần minh họa, không tạo `FILM_FACT` mới và không thay đổi nguyên văn **Sáu bước** đã phê duyệt hoặc các đoạn REVIEW đã xác minh. Khi hình không đủ đẹp/đủ dài, G08 đề xuất ứng viên khác hoặc báo thiếu; tuyệt đối không sửa lời REVIEW để phù hợp một shot sai nội dung.
