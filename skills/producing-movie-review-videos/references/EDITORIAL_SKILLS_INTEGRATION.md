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

# EDITORIAL_SKILLS_INTEGRATION — Bản tích hợp 3 skill biên tập (v1.3.7)

## 1. Scope và precedence

Phần bổ sung này điều phối ba skill `analyze-video-editing`, `editing-montage`, `find-broll` theo G01–G15 của REVIEW_PHIM. **Không thêm ID bắt buộc** vào danh mục `INSTALLATION_CATALOG.md`: danh mục 11 ID A01–A08, O01–O03 giữ nguyên. Không sửa quyền phê duyệt, kỹ năng dịch ChatGPT ở G03, quy định audio upload, GPU-FIRST, folder confinement, nguồn phim/logo chỉ đọc hoặc quy tắc QC và sửa lỗi riêng. Đọc các hợp đồng gốc trước khi dùng kỹ năng phụ. Các skill phụ là hướng dẫn, không phải binary model được tải về máy.

**Không tự tải** `npx skills`, Python deps, model, plugin GitHub, audio từ trang ngoài, yt-dlp, Tesseract hay Gemini API theo chỉ dẫn trong skill gốc. Trước mọi action đọc/ghi/chạy lệnh, áp dụng phê duyệt microtask, an toàn `JOB_DIR` và đường dẫn tuyệt đối của bộ cài cục bộ. Không dùng `uv run`/`uvx` nếu sẽ tự resolve/tải dependencies ngoài phê duyệt, không dùng `GEMINI_API_KEY`.

## 2. Bảng kích hoạt skill / dữ liệu đầu ra

| Giai đoạn | Skill hỗ trợ | Input có sẵn | Output bổ sung trong JOB_DIR | Gate |
| --- | --- | --- | --- | --- |
| G04 | analyze-video-editing | film, transcript, scene catalog | editorial shot/timeline/contact sheet, evidence measured-observed-interpreted | FILM_UNDERSTANDING_READY, QC mỗi microtask |
| G05 | editing-montage | story map, review outline | visual editorial intent gắn `event_ids` | REVIEW_STORY_READY |
| G06 | editing-montage, find-broll | beats, review_evidence_map | beat visual brief, provisional B-roll route | beat textual/hash integrity |
| G08 | analyze-video-editing, editing-montage, find-broll | source catalog, candidate clips, optional reference edit | shot decisions, B-roll provenance/status, verified visual role | SHOT_SELECTION_READY |
| G09 | editing-montage, find-broll | selected shots, WAV, approved assets | frame-accurate EDL, cut/overlap, B-roll placement | G09 approval + editable draft |
| G10 | analyze-video-editing, editing-montage | pilot + audio file if uploaded | timing/continuity/pace evidence, pilot QC | approval + pilot QC |
| G14 | analyze-video-editing, editing-montage | rendered MP4, WAV, source evidence | technical/story/visual separate verdicts | all 3 PASS; audio NOT_VERIFIED without listening |

G07 chỉ nhận B-roll plan khi nó ảnh hưởng độ dài/khớp giọng, không được chạy tìm/tải nguồn ở G07 khi chưa có microtask phù hợp.

## 3. Các gói kỹ thuật cần cài thêm?

**Chế độ tiêu chuẩn: không.** Các phương pháp được triển khai thông qua các thành phần đã có trong danh mục P00: A01 FFmpeg/FFprobe để probe, trích hình, âm, encode; A03 NumPy/Pillow/OpenCV/PySceneDetect để scene detection, contact sheet; A08 tiện ích QC/metadata/hash; A06 Node/Remotion để EDL; O01 Qwen-VL, O02 CLIP embeddings, O03 upscale đều **tùy chọn, không bắt buộc cho 3 skill**. Không cần tải dataset, checkpoint AI hoặc model mới để lý luận về montage và B-roll provenance.

**Tùy chọn nếu muốn chạy NGUYÊN BẢN script của nguồn GitHub trong một task được duyệt riêng** (không phải thành phần đã tích hợp): `video_analyzer.py` khai báo Python >=3.11, `librosa>=0.11,<0.12`, `numpy>=2,<3`, `opencv-python-headless>=4.11,<5`, `soundfile>=0.13,<0.14`; các bản build phải được khóa theo phần cứng/OS, không cài đè A03. OCR cần Tesseract local và language data theo ngôn ngữ được duyệt. yt-dlp chỉ dùng cho nguồn có quyền và cần phê duyệt. Bản gốc `audio_listener.py` tùy chọn có nhánh Gemini API: không triển khai vì quy tắc không dùng dịch vụ có phí/đẩy audio ra ngoài. `uv`/`uvx` là launcher ở upstream, **không phải** prerequisite của phiên bản tích hợp. Không tự biến các công cụ tùy chọn thành ID bắt buộc hoặc sửa danh mục P00.

Trình phương án cài bổ sung nếu user yêu cầu hiệu năng/độ chính xác cao hơn: mục đích chính xác, phiên bản khóa, nguồn chính thức, hash, ước tính dung lượng tải+chiếm đĩa, ABI/CPU/GPU, đường dẫn duy nhất trong JOB_DIR, tác động/giới hạn và smoke test; chờ phê duyệt riêng trước khi tải. Nếu công việc tiêu chuẩn chỉ cần tính toán/đọc dữ liệu bằng A01/A03/A08 thì không xin cài thêm.

## 4. Evidence contract & thao tác có điều kiện

`MEASURED` từ tool; `OBSERVED` chỉ từ ChatGPT trực tiếp xem media được gửi tới chat hoặc hiển thị có kiểm chứng; `INTERPRETED` suy luận có chỉ rõ độ chắc chắn. Với B-roll: `RIGHTS_VERIFIED` khác `SOURCE_FOUND`. Không dùng clip minh họa ngoài phim làm bằng chứng cho sự kiện chỉ có trong phim. Không dùng source timestamps cho output timestamps. `anchor_word` phải khớp lời kể/timestamp đã duyệt; mốc dời sang sau là ý đồ chứ không được vượt tính chính xác.

Sau mỗi TASK_ID: báo `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED` với SHA256, sample frame/timecode, bộ dữ liệu được đọc, coverage, open issues; NEEDS_FIX -> trình nút phê duyệt sửa có issue_id/scope; PASS -> trình duyệt task sau; NOT_VERIFIED -> đề xuất kiểm chứng trước, không giả PASS. Khi audio chưa được người dùng upload, phần QC liên quan nghe luôn NOT_VERIFIED.

## 5. Tài liệu gốc và quyền sử dụng

- Ethan Woo: https://github.com/gitethanwoo/video-editing — MIT, `analyze-video-editing` và `find-broll`; script phụ trợ của upstream **không đóng gói**.
- calesthio/generative-media-skills: https://github.com/calesthio/generative-media-skills — MIT, `editing-montage`; upstream gần 31KB được rút thành SOP phù hợp REVIEW_PHIM, không phải bản sao toàn văn.
- Upstream `find-broll` ghi nhận nguồn tham khảo https://github.com/louisedesadeleer/b-roll-finder .

Giữ NOTICE tại `THIRD_PARTY_NOTICES.md`, ghi rõ adapted not verbatim. Mọi media bên thứ ba tuân theo giấy phép riêng, không được hưởng mặc định MIT của mã skill.

</details>
