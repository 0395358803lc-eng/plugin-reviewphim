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

# G05_NARRATIVE_ONLY_V1317 — REVIEW kể chuyện thuần túy, tuyệt đối không nhắc quy trình

> **ƯU TIÊN CAO NHẤT CHO MỌI PHIM Ở G05, hiệu lực từ REVIEW_PHIM v1.3.17.** Chính sách này bổ sung điều kiện bắt buộc cho `G05.REVIEW.FULL` và ghi đè mọi ví dụ trước đây có cách viết như "theo bản dịch", "trong transcript", "những khung hình đã kiểm tra", "kịch bản không khẳng định". Giữ nguyên **sáu bước** kể chuyện, một nhiệm vụ trọn giai đoạn, Q05 tổng thể và cổng con người `G05_SCRIPT`.

## 1. Tách tuyệt đối lời kể cho khán giả và hồ sơ nội bộ

**Kênh A — Lời REVIEW phát cho khán giả (chỉ được phép kể chuyện):**

- `review/review_ke_chuyen.txt` và `review/review_loi_binh_tts.txt`, cũng như mọi câu `narration_text`, `voiceover_text` được tạo từ hai tệp này.
- Chỉ nói nhân vật **là ai, muốn gì, làm gì, vì sao, gặp cản trở gì, phản ứng và hậu quả ra sao**; kể ngôi thứ ba, tự nhiên, có nhịp, mạch truyện và sáu bước theo `REVIEW_STORYTELLING.md`.
- **Không bao giờ** giải thích cách ChatGPT hiểu phim, tóm tắt bằng chứng đã xem, mô tả việc phân tích, hoặc báo tình trạng kiểm tra. Không nhắc tên công nghệ/công cụ, nguồn trung gian, các cổng QC, tiến độ, lỗi nhận dạng, hoặc giới hạn bằng chứng trong lời kể.
- **Cấm** những nhóm câu: "theo transcript/ASR/bản dịch/phần thoại", "trong các khung hình/chuỗi hình được kiểm tra", "qua ảnh cho thấy", "như đã được xác minh", "chưa đủ bằng chứng để khẳng định", "kịch bản này không khẳng định", "người xem/khán giả sẽ thấy", "ChatGPT đã phân tích", "Q05/nguồn/timecode/segment". Tránh cả cách nói tương đương không có đúng các từ trên.
- **Không biến thiếu chắc chắn thành sự thật.** Khi lời thoại/sự kiện chưa đủ căn cứ, chỉ kể những sự kiện đã được hỗ trợ; bỏ hẳn chi tiết phụ thuộc; hoặc diễn đạt suy luận về cảm xúc **tự nhiên** dựa trên hành vi, không nói "chưa được kiểm chứng" cho khán giả. Ví dụ câu không đủ chứng cứ về tử vong → chỉ nói "người đàn ông gục xuống / bị thương" nếu thực tế có hình chứng minh; không tự nói "đã chết".

**Kênh B — Metadata và báo cáo QC nội bộ (giữ nguyên đầy đủ):**

- `review/review_outline.json`, `review/review_evidence_map.json`, `review/review_visual_intent.v1.json`, `qc/g05_story_qc.md`, `qc/microtasks/G05.REVIEW.FULL/*`, ledger/checkpoint.
- Ghi đầy đủ `event_id`, `source_scene_id`, ảnh/clip đã xem, `claim_type`, `review_status`, `QUALIFIED`, flags nguồn, giới hạn xác minh, việc còn cần kiểm tra; không trộn các dòng ghi chú này vào hai bản lời kể hoặc TTS.
- Các trường metadata và báo cáo được phép có từ "transcript", "ASR", "evidence", "QC", timecode, v.v. **Linter chỉ kiểm văn bản dành cho khán giả**. Lời review thuần túy không đồng nghĩa bỏ QC hay bỏ truy vết nguồn.

## 2. Cách viết lại đúng mà không thay đổi nội dung phim

| Câu bị cấm trong lời REVIEW | Câu theo logic kể chuyện — chỉ dùng khi tình tiết đủ bằng chứng |
|---|---|
| "Theo phần thoại đã được dịch, Billy gây sức ép lên Christine." | "Billy tìm cách ép Christine nhận rằng cô không xứng đáng với giải thưởng." |
| "Trong những hình ảnh liên tiếp, Chris đối mặt người cầm súng." | "Chris bước ra khoảng sân phủ tuyết và đối mặt người đàn ông có súng." |
| "Kịch bản không khẳng định sát thủ đã chết." | Bỏ hoàn toàn lời bình quy trình; chỉ kể hậu quả thực sự đã thấy, ví dụ "Hắn bị thương nhưng vẫn cố cầm súng." |
| "Các khung hình chưa đủ bằng chứng để biết ai bắn trước." | Bỏ chi tiết ai bắn trước; kể đúng diễn biến nhìn thấy: "Cuộc đấu súng tiếp diễn ngoài sân tuyết." |
| "Trong bản dịch, Chris nói mình không thể thay cha mẹ." | "Chris giải thích rằng những món quà không thể thay thế vai trò của cha mẹ." |

Từng câu sửa phải được so với `story_map`, `visual_events`, transcript dịch nội bộ và chứng cứ thực tế. Các câu minh họa **không tự mang quyền khẳng định sự kiện** trong một phim khác.

## 3. Quy trình G05 trong đúng một gói

1. ChatGPT đọc G04 `FILM_UNDERSTANDING_READY` có điều kiện, đọc transcript dịch và chứng cứ **ở nội bộ**. Chọn tuyến truyện, lên `review_outline` đủ **sáu bước**.
2. Viết một bản `review_ke_chuyen.txt` hoàn chỉnh, *chỉ lời kể*, không tiêu đề QC/nhãn kỹ thuật/giải thích nguồn. Không viết "theo ..." về nguồn dữ liệu. Giữ vai trò người kể chuyện phim, không vai trò người phân tích chứng cứ.
3. Tạo `review_evidence_map.json` (vị trí các đoạn, event/scene refs và trạng thái hỗ trợ), `visual_intent` và báo cáo QC **riêng**. Khi chứng cứ yếu, sửa / bỏ claim khỏi *lời kể* nhưng giữ warning và giải thích trong metadata.
4. Tạo `review_loi_binh_tts.txt` từ lời kể, giữ nghĩa và không thêm cụm quy trình. Nếu workflow yêu cầu hai bản giống nhau, so byte/Unicode. Không chèn dấu `QUALIFIED`, `[CẦN NGHE ...]` hay thẻ QC vào lời TTS.
5. **Bắt buộc chạy linter** chuẩn Python `tools/g05_narrative_only_policy.py` trên cả hai văn bản bằng `q05_narrative_gate(review_text, tts_text)`, **chỉ khi scope thực thi G05 đã được người dùng phê duyệt**. Nếu `BLOCKED`, sửa lại nội dung và chạy lại, không dùng replace hàng loạt để xóa mất chứng cứ hoặc thay đổi sự thật; không ghi Q05 PASS khi còn vi phạm.
6. Kiểm tra ngữ nghĩa thủ công lần cuối để bắt **cách nói tương đương** chưa nằm trong từ điển regex: đọc như khán giả, bất kỳ câu nào kể việc kiểm tra/dịch/viết thì **FAIL**. Xác minh lại logic nhân vật, hành động, nguyên nhân–hậu quả và evidence map. Sau đó một Q05 tổng thể, giữ `G05_SCRIPT=WAITING_FOR_HUMAN_APPROVAL`; không tự cấp quyền G06/G07/G08.

## 4. Điều kiện nghiệm thu và hành vi dừng

**Hard gate:** `Q05_NARRATIVE_ONLY=PASS` phải đi cùng các cổng cũ (6 bước đủ, không có claim bịa, mọi `FILM_FACT` trọng yếu có event/evidence, TTS nhất quán, 1 Q05, G05_SCRIPT còn chờ con người). Linter trả vị trí dòng/từ vi phạm; `BLOCKED` thì `REVIEW_STORY_READY` **không được nâng PASS**.

**Kiểm tra không phải bảo đảm máy móc tuyệt đối về ngữ nghĩa:** ngoài regex, ChatGPT phải tự duyệt và đọc lại từng đoạn. Mẫu mới mang ý nghĩa tương đương quy trình phải chặn dù không khớp regex. Không tự sửa các bản review/checkbox đã PASS của dự án cũ khi phát hành plugin mới; muốn thay đổi bản Fatman v1 cũ phải viết phiên bản mới trong một gói được duyệt, giữ nguyên hash/checkpoint cũ.

**G04/G06/G07/G08/G09–G15 và mọi điều kiện source/hash/approval cũ giữ nguyên.** Quy tắc mới chỉ điều chỉnh ngôn ngữ xuất cho người xem ở G05 và điều kiện nghiệm thu Q05.

</details>
