# ATOMIC_STAGES_V1315 — G01, G03, G05: mỗi giai đoạn một đầu việc hoàn chỉnh

> **BỔ SUNG ƯU TIÊN G05 v1.3.18:** [G05_WEB_STORY_CROSSCHECK_V1318](G05_WEB_STORY_CROSSCHECK_V1318.md) yêu cầu ChatGPT **sau khi viết xong review phải tìm web bằng công cụ ChatGPT**, đối chiếu synopsis/plot ít nhất hai nguồn độc lập với G04 và review, kết luận có cần sửa trong cùng `G05.REVIEW.FULL`, trước **một Q05**. Không lấy web thay phim, không tự chèn tình tiết chưa đủ chứng cứ, không đưa dữ liệu kiểm chứng vào lời kể; giữ `G05_NARRATIVE_ONLY_V1317`, sáu bước, `NO_STAGE_SPLIT`, và cổng người dùng `G05_SCRIPT` riêng. Không có web thật / còn xung đột quan trọng thì không tự `REVIEW_STORY_READY`.

> **CẬP NHẬT ƯU TIÊN v1.3.16:** Với G02/Q02, chính sách [SIMPLE_G02_TEXT_QC_V1316](SIMPLE_G02_TEXT_QC_V1316.md) ghi đè yêu cầu kiểm tra nghi vấn nội dung, 17 cụm và gate theo ASR. G02 hoàn tất khi transcript toàn phim đã xuất và lỗi chữ/format được sửa an toàn; nghĩa phim và hình ảnh kiểm sau ở G04/G05/G08. Giữ nguyên các điều kiện bảo vệ dữ liệu và phê duyệt.


> **HỢP ĐỒNG ƯU TIÊN CAO NHẤT CHO G01/G03/G05 — REVIEW_PHIM v1.3.15.** Đối với ba giai đoạn này, tài liệu này có ưu tiên cao hơn các ví dụ chia G01.Mnn, G03.Mnn.Bxxx, G05.Mnn, `batch` hoặc nhiều nút/QC ở `WORKFLOW_CONSISTENCY_V1312.md`, `SMART_BATCH_APPROVAL.md`, `MICROTASK_ORCHESTRATION.md`, `APPROVAL_TRANSLATION_AUDIO.md`, `WORKFLOW.md`, `REVIEW_STORYTELLING.md`, `ACCEPTANCE_QC.md`, `WHOLE_FILM_TRANSCRIPT_V1314.md` và các mẫu cũ. **Chỉ đổi đơn vị công việc; không đổi yêu cầu chất lượng, quyền truy cập, nguồn, hash, phê duyệt hoặc thứ tự công đoạn.** `NO_STAGE_SPLIT` là quy tắc mặc định cho tất cả dự án.

## 1. Quy tắc một giai đoạn = một nhiệm vụ = một lần QC

| Giai đoạn | Mã nhiệm vụ duy nhất | Đầu ra hoàn chỉnh | Cổng QC |
|---|---|---|---|
| **G01** | `G01.SOURCE.FULL` | Kiểm tra nguồn phim từ đầu đến cuối; FFprobe/audio-video timebase, SHA-256, visual source profile, media manifest, chứng cứ nguồn | **Q01** một lần |
| **G03** | `G03.TRANSLATE.FULL` | Bản dịch transcript tiếng Việt **toàn phim**, giữ `segment_id`, timecode, tên riêng, flags và provenance, cùng báo cáo coverage | **Q03** một lần |
| **G05** | `G05.REVIEW.FULL` | **Toàn bộ kịch bản REVIEW sáu bước**; review outline, story/evidence map và `visual_intent` theo beat; một bản review để người dùng xét duyệt | **Q05** một lần và cổng **G05_SCRIPT** riêng |

Không phát sinh những task bắt buộc `G01.M01/G01.M02`, `G03.M01/G03.M02.B001`... hoặc `G05.M01/G05.M02.B001` trong **dự án mới**. Không có nút phê duyệt ở giữa một giai đoạn và không gắn PASS cho phần nhỏ của phim khi chưa hoàn thành sản phẩm toàn giai đoạn. Các bước kỹ thuật (FFprobe/hash, đọc dữ liệu, tạo outline/viết nội dung) vẫn chạy **bên trong** nhiệm vụ cha; nội bộ có log/tiến độ nhưng không phải microtask độc lập.

`NO_STAGE_SPLIT` không có nghĩa gom ba giai đoạn thành một quyền tự động chạy xuyên G01–G05. Mỗi giai đoạn trong một `WORK_PACKAGE_ID` phải có task_id, input/output, giới hạn, công cụ và `plan_hash` đã được người dùng chấp thuận. Có thể duyệt gộp **nhiều giai đoạn** chỉ khi tất cả scope và dependency có thật, được ghi rõ và human gates không bị vượt. Chưa duyệt G03/G05 không được tự chạy vì G01/G02 đã hoàn tất.

## 2. G01: một lượt kiểm định nguồn phim, không chia task

- `G01.SOURCE.FULL` đọc `SOURCE_MOVIE` **read-only** trong `FILM_DIR` đã được phê duyệt, ghi chứng cứ ra `JOB_DIR` duy nhất; bao trùm container, tracks, FFprobe, SHA-256, duration, start/end PTS, VFR/FPS nếu có, audio-video synchronization, source visual profile, media manifest và nguồn/logo nếu có quyền liên quan.
- Có thể gọi nhiều lệnh kỹ thuật FFprobe/hash bên trong một nhiệm vụ, nhưng **chỉ một report QC Q01** cho toàn phim, có `source_sha256`, media duration/timebase, input/output hashes và coverage nguồn. Không lấy số lệnh công cụ làm số microtask.
- Nếu chứng cứ thiếu, nguồn sai hash hoặc audio-video timing có vấn đề → `NOT_VERIFIED/BLOCKED`; giữ checkpoint **PARTIAL** theo đúng thực tế, không coi Q01 đạt từ một bước nhỏ. Một khi G01 đã PASS với cùng source SHA-256 và bằng chứng còn hợp lệ (như Fatman), **tái sử dụng** G01 đã kiểm chứng, **không chạy lại P00 hoặc G01** chỉ vì nâng plugin.

## 3. G03: ChatGPT trực tiếp dịch toàn bộ transcript trong một giai đoạn

- Điều kiện: có `G02.ASR.FULL` **toàn phim**, Q02 đủ điều kiện và nguồn `analysis/transcript_original.jsonl` đầy đủ. Một tác vụ `G03.TRANSLATE.FULL` → một `analysis/transcript_vi.jsonl`, `analysis/transcript_vi.txt`, `analysis/translation_flags.json`, coverage report và **Q03** duy nhất.
- **ChatGPT trực tiếp** đọc **toàn bộ** đoạn transcript gốc và tự dịch ngữ nghĩa theo từng `segment_id`/timecode, bảo toàn nội dung quan trọng, không tự bịa lời thoại. **không dùng model dịch** local/API, **không dùng script dịch** văn bản. Script chỉ hỗ trợ đọc/phân trang, ghi kết quả, ghép, kiểm checksum/coverage và ID/timecode; không tự dịch.
- Khi transcript vượt giới hạn ngữ cảnh, **đọc theo cửa sổ tối đa 40 segment hoặc 1.000 từ trong cùng tác vụ** là kỹ thuật `INTERNAL_CONTEXT_PAGING`: không phải task riêng, không phải Q03-Bxxx, không được yêu cầu phê duyệt mới cho mỗi trang. Những trang là dữ liệu tạm có lineage trong `JOB_DIR`, chỉ công bố bản dịch hoàn chỉnh sau khi đối chiếu tất cả ID và timecode.
- Không thể thực sự đọc hết transcript trong lượt chat → ghi `PARTIAL` và checkpoint số `segment_id` đã dịch thật; lượt sau người dùng chủ động **Tiếp tục cùng gói**, không tự chạy nền, không bỏ qua trang hoặc giả đã dịch hết. Q03 chỉ PASS khi coverage 100% các đoạn transcript hợp lệ và flags đã được phân loại; không đòi dịch forensic mọi câu thoại phụ đã bị quarantine, không biến `MINOR_NONBLOCKING` thành câu thoại chắc chắn.

## 4. G05: viết toàn bộ review trong một nhiệm vụ

- Điều kiện bắt buộc: G04 đạt `FILM_UNDERSTANDING_READY`, đã có `story_map`, scene catalog, visual events, nhân vật và bằng chứng kiểm tra thật. Một tác vụ `G05.REVIEW.FULL` viết **kịch bản REVIEW sáu bước trọn vẹn** từ đầu tới cuối, không lập từng nhiệm vụ cho đoạn mở đầu/cao trào/kết phim.
- Đầu ra là một review hoàn chỉnh, đồng bộ `review_outline`, `event_id`/source scene cho claim cốt truyện, mapping `visual_intent` cho beat, các cảnh quan trọng cần tìm ở G08; lời Việt tự nhiên, kể đúng nhân vật/tuyến truyện/nguyên nhân-kết quả, **không bịa** sự kiện từ ASR chưa xác minh.
- ChatGPT có thể soạn/chỉnh nội bộ vài đoạn trong một lượt để giữ ngữ cảnh, nhưng **không xuất bản từng phần** hay xin duyệt mỗi đoạn; một **Q05** tổng thể trước khi trình toàn bộ script để người dùng duyệt **G05_SCRIPT**. `REVIEW_STORY_READY` không thay cho sự đồng ý `G05_SCRIPT`. Nếu có chỉnh sau khi duyệt thì giữ phiên bản, xin phê duyệt phần thay đổi theo các quy tắc hiện hành; **không tự chạy G06** khi thiếu duyệt.
- Nếu chưa đủ bằng chứng về plot/cảnh quan trọng, phải dừng phần phụ thuộc hoặc bỏ claim không có căn cứ, không che lỗi bằng review sáng tác. G05 sẽ ưu tiên tính đúng cốt truyện và định hướng hình ảnh, không lấy việc dịch từng câu phụ làm điều kiện chặn.

## 5. Trạng thái, checkpoint và không thay đổi các giai đoạn còn lại

- **Mỗi giai đoạn đúng một task_id, một checkpoint lineage và một QC tổng thể**; tiến độ nội bộ có thể lưu từng trang/frame/đoạn văn vào `JOB_DIR/temp` hay `logs`, nhưng không phải task/scope và không sinh Q01-Bxxx/Q03-Bxxx/Q05-Bxxx.
- Chỉ được cấp `PACKAGE_PASS` khi toàn bộ output/Gxx/Qxx thuộc phạm vi phê duyệt có thật, bản gốc còn nguyên hash, không có blocker cần sửa và cổng con người hợp lệ. `PARTIAL`, `BLOCKED`, `NOT_VERIFIED`, `WAITING_FOR_HUMAN_APPROVAL` là trạng thái thật, không sửa báo cáo cũ để giả PASS.
- **G02 giữ nguyên** hợp đồng `WHOLE_FILM_TRANSCRIPT_V1314.md`: `G02.ASR.FULL`, `NO_BATCH_SPLIT`, toàn bộ audio một lần ASR một lần Q02. Không quay lại B001–B010.
- **Các giai đoạn G04, G06, G07, G08, G09, G10, G11, G12, G13, G14, G15 và P00 giữ nguyên quy trình hiện tại**, bao gồm batch nội bộ có giới hạn, QC/approval theo microtask nếu hiện hành yêu cầu. Đặc biệt G04 xem hình/clip thật; G08 `SHOT_SELECTION_READY` và chỉ chọn clip `VERIFIED_VISUAL` đúng actor/action; G07_VOICE và G10_PILOT vẫn chặn theo đúng quyền, G09 preview trước G11 render, G14 quality technical/story/visual đủ, G15_DELETE cần phê duyệt riêng.
- Giữ khóa atomic `work_package.lock` không cướp, read/write roots, `plan_hash`, source/input hashes, GPU-FIRST, không tự cài/tải, không CPU fallback ngầm, không sửa phim nguồn hoặc dữ liệu đã duyệt; source movie chỉ read-only.
- **Fatman (2020):** G01 đã có checkpoint/Q01 từ trước thì chỉ reuse khi chứng cứ hợp lệ, không đánh lại PASS theo cảm tính. G02 plan mới `G02.ASR.FULL` vẫn cần duyệt; đổi plugin **không tự chạy** G02/G03/G05, không mở rộng scope của gói G02 cũ. Các `NOT_VERIFIED` lịch sử B001/B003 giữ nguyên; mọi phân loại lại cần một gói mới được duyệt.
