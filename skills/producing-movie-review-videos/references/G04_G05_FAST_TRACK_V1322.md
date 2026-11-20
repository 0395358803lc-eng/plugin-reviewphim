# G04_G05_FAST_TRACK_V1322 — G04/G05 một nhiệm vụ, một QC tổng thể

**ƯU TIÊN CAO NHẤT TRONG G04/G05 từ REVIEW_PHIM v1.3.22.** Quy định này **ghi đè** mọi ví dụ chia `G04.Mnn[.Bxxx]`, `G05.Mnn[.Bxxx]`, QC lẻ từng batch, kế hoạch phụ tự phát và các quy trình cũ trong `MICROTASK_ORCHESTRATION.md`, `FILM_UNDERSTANDING.md`, `REVIEW_STORYTELLING.md`, `WORKFLOW.md`, `SMART_BATCH_APPROVAL.md`, `MICROTASK_ACCEPTANCE_REPAIR.md`, `WORKFLOW_CONSISTENCY_V1312.md` và các mẫu cũ **chỉ về granularity/độ sâu phân tích/điểm dừng nội bộ của G04, G05**. Các giới hạn thiết bị, nguồn phim, phê duyệt gói v1.3.21, quyền đọc/ghi, media QC thật v1.3.20, hash, lock, repair budget, và human gate `G05_SCRIPT` không thay đổi. Không tự ý chuyển trạng thái lịch sử hoặc mở rộng gói đã duyệt.

## Hợp đồng bắt buộc: không sinh việc mới theo từng cảnh/đoạn

| Stage | Task duy nhất của gói **mới** | Báo cáo duy nhất | Human gate |
| --- | --- | --- | --- |
| G04 | `G04.FILM.UNDERSTANDING.FULL` | Một Q04: `FILM_UNDERSTANDING_READY` hoặc trạng thái thiếu chứng cứ | Không tạo gate người dùng cho từng scene |
| G05 | `G05.REVIEW.FULL` | Một Q05: `REVIEW_STORY_READY` khi đủ chứng cứ | `G05_SCRIPT` duyệt **toàn bộ** bản REVIEW sau Q05 |

Trong package `work-package.v2`, `task_ids` là các task **FULL** trên; `bounded_batches` không được mang stem G04/G05. Vẫn dùng `tools/work_package_state.py` cho plan hash/approval/lock; bổ sung gọi `tools/g04_g05_atomic_policy.py::validate_stage_tasks(...)` cho gói mới trước khi trình duyệt/chạy. Python này chỉ kiểm metadata, **không** cấp quyền/chạy remote. Các phân trang, frame samples, nội dung được soạn qua nhiều lượt ChatGPT chỉ là **vòng lặp nội bộ** trong task đã duyệt: không lập `WORK_PACKAGE_ID` mới, không đổi `plan_hash`, không xin duyệt từng batch hoặc đẻ Q04.Bxxx/Q05.Bxxx. Với checkpoint G04/G05 lịch sử, giữ đường dẫn, hashes, approvals và task cũ theo phạm vi đã duyệt; **không migrate/ghi đè**. Khi người dùng chủ động tiếp tục gói cũ, kiểm scope trước, không âm thầm biến nó thành quyền cho FULL mới.

## G04: story-first fast-track, ưu tiên sự kiện quan trọng

1. **Một lượt chỉ mục toàn phim**: đọc `SOURCE_MOVIE`/hash/timebase hợp lệ và transcript; scene detect hoặc mẫu đều từ đầu đến cuối. Tạo `analysis/scene_catalog.json` và danh sách contact sheets/tham chiếu timecode *một lần*, tái sử dụng nếu hash/source không đổi. Chỉ mục ≠ ChatGPT đã xem.
2. **Một lượt xem có chọn lọc**: ChatGPT thật sự xem các frame/contact sheet có sẵn, ưu tiên nhân vật chính, sự kiện khởi phát, nút thắt, tình tiết không lời, cao trào, kết thúc. Với hành động không thể chứng minh bởi 1 frame hoặc lời thoại, xem **chuỗi frame/clip thật**; không tự coi model VL/FFprobe/ASR đã quan sát thay ChatGPT.
3. **Tăng độ sâu theo rủi ro, không theo số cảnh**: chỉ trích thêm khi bất đồng nhân vật, hành động, nhân quả, thời gian/tuyến truyện hoặc cảnh không lời **ảnh hưởng claim sẽ kể**. Cảnh phụ/shot phụ không chắc được ghi `UNKNOWN`/`NONBLOCKING` và tránh khẳng định trong G05. Không mở batch mới chỉ để rà tất cả góc máy, biểu cảm, subtitle hay shot đẹp.
4. **Một sản phẩm G04**: đồng bộ nhẹ `scene_catalog`, `visual_events`, `story_map`, `characters`, `evidence_index` với các mốc thật và `qc/g04_evidence_report.md`. Không cần phân tích sâu `visual_shot_profile.json` cho mọi cảnh ở G04; phần góc máy, thẩm mỹ, shot candidates, crop, matching theo beats chuyển trọng tâm sang **G08**. Nếu đã có dữ liệu shot profile được kiểm thực, tái dùng, không hủy.
5. **Một Q04 tổng thể**: `FILM_UNDERSTANDING_READY` khi chỉ mục phủ đầu–cuối theo lấy mẫu, sự kiện **cốt lõi** được ChatGPT kiểm bằng hình/clip đúng ngữ cảnh, bản đồ truyện nhất quán và không có core unresolved claim đang được khẳng định. Không khóa G04 vì camera_motion/shot_type cảnh phụ là UNKNOWN. Thiếu phương thức đọc ảnh thật hoặc bằng chứng then chốt → `NOT_VERIFIED/BLOCKED`; dùng `MEDIA_EVIDENCE_HANDOFF_V1320` cho ZIP clip cần thiết (đã có quyền), **không báo PASS giả**. Nếu có thể loại claim không chứng minh mà vẫn kể đúng, ghi warning và tiếp tục.

**Không áp cứng “8 scene/24 ảnh một lô” như cổng dừng**. Có thể chia nhỏ thực tế để không quá tải bộ nhớ/kênh truyền, nhưng mọi phần đều thuộc task FULL và không đòi duyệt/QC độc lập. Không bỏ sự kiện quan trọng chỉ để tiết kiệm số frame.

## G05: tạo và nghiệm thu toàn bộ REVIEW trong một lượt logic

1. Chỉ bắt đầu khi Q04=`FILM_UNDERSTANDING_READY` với story/evidence có thật và quyền gói còn hợp lệ. Đọc một lần các tài liệu đã có; không quay lại trích frame G04 chỉ vì chi tiết phụ mà G05 không cần kể.
2. ChatGPT xây dựng outline sáu bước và **viết toàn bộ** `review_ke_chuyen.txt` ngôi ba từ sự kiện cốt lõi; tạo `review_loi_binh_tts.txt` nhất quán cùng `review_evidence_map.json` và các hint hình ảnh cần cho G08. **Không** tạo task/duyệt riêng cho hook, mở đầu, phần 1–4 đoạn hay cao trào/kết. Nếu nội dung dài, phân trang là thao tác nội bộ, không thành stage mới.
3. Lời REVIEW/TTS **chỉ kể chuyện phim** theo `G05_NARRATIVE_ONLY_V1317`; nội dung QC, ASR, nguồn và cách ChatGPT làm việc phải nằm trong hồ sơ nội bộ. Chỉ so/kiểm lại những claim trọng yếu, không kiểm hàng loạt từ thoại phụ.
4. Sau bản thảo đầy đủ, ChatGPT tìm web thật và đối chiếu **ít nhất hai nguồn độc lập đúng phim** theo `G05_WEB_STORY_CROSSCHECK_V1318`. Đánh giá **một lượt có chủ đích**, chỉ thay những đoạn có vấn đề được chứng cứ phim/G04 hỗ trợ. Không sửa lại toàn bộ REVIEW vì một câu/chi tiết phụ và không tái tìm nguồn mỗi lần chỉnh văn phong. Web thiếu/không xác minh thì ghi `NOT_VERIFIED` và đúng một blocker, không chạy vòng tìm kiếm vô hạn/không bịa nguồn.
5. Đồng bộ bản REVIEW/TTS/evidence map và chạy `Q05_NARRATIVE_ONLY` trên hai bản; sau các sửa cần thiết chỉ **một Q05 tổng thể** bao gồm story/causal logic, coverage trọng yếu, web crosscheck và narrative-only. Linter có thể chạy lại **nội bộ** sau sửa; đó không phải Q05 mới hoặc một gói mới. Nếu còn một claim cốt lõi chưa chắc, chỉ kiểm lại đúng đoạn clip/nhân quả ấy trong quyền được duyệt; không được tự mở rộng G04.
6. Sau Q05 đủ điều kiện, trình người dùng duyệt **toàn bộ kịch bản duy nhất** qua `G05_SCRIPT`, ghi `WAITING_FOR_HUMAN_APPROVAL`; chỉ khi được duyệt mới được sang G06. Không gộp G05_SCRIPT thành sự đồng ý chung trước khi bản kịch bản tồn tại.

## Chống vòng lặp và trách nhiệm bằng chứng

- Chỉ mở công việc mới nếu có **nguyên nhân trọng yếu cụ thể + evidence gap + phạm vi/hashes/phép phù hợp**. Không sinh việc kiểu “xem thêm toàn bộ” từ warning cảnh phụ, không tự tạo Q04/Q05 thứ hai; nếu không thể khắc phục trong repair_budget, báo một blocker tổng hợp và dừng phần phụ thuộc.
- Sau mỗi phần nội bộ thực hiện được, **tiếp tục ngay trong cùng WORK_PACKAGE_ID** mà không xin duyệt từng trang, batch, đoạn review, clip. Khi giới hạn phiên chat bắt buộc dừng, ghi checkpoint `PARTIAL`; người dùng chủ động “Tiếp tục gói” đúng scope chứ không “duyệt lại”. Không giả rằng ChatGPT chạy nền.
- `tools/g04_g05_atomic_policy.py` cung cấp kiểm cấu trúc package và metadata QC, không chứng minh media đã xem hoặc thông tin web thực; ChatGPT vẫn phải quan sát thực tế trước khi ghi VERIFIED.
- Giữ tất cả sửa giới hạn, không xóa dữ liệu nguồn hoặc sửa checkpoint lịch sử, và không nới quyền cài/tải/đăng YouTube/chuyển media.
