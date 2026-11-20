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

# STORY_FIRST_WORKFLOW_V1313 — Fast-track review phim, ưu tiên nội dung và hình ảnh

> **CẬP NHẬT ƯU TIÊN v1.3.16:** Với G02/Q02, chính sách [SIMPLE_G02_TEXT_QC_V1316](SIMPLE_G02_TEXT_QC_V1316.md) ghi đè yêu cầu kiểm tra nghi vấn nội dung, 17 cụm và gate theo ASR. G02 hoàn tất khi transcript toàn phim đã xuất và lỗi chữ/format được sửa an toàn; nghĩa phim và hình ảnh kiểm sau ở G04/G05/G08. Giữ nguyên các điều kiện bảo vệ dữ liệu và phê duyệt.


> v1.3.15: G01/G03/G05 tuân theo `ATOMIC_STAGES_V1315.md` ưu tiên cao hơn ví dụ chia nhỏ task nội bộ; G04 và G06–G15 vẫn theo quy trình cũ. G02 theo `WHOLE_FILM_TRANSCRIPT_V1314.md`.

> **ƯU TIÊN CAO — REVIEW_PHIM v1.3.13.** Áp dụng trước `WORKFLOW_CONSISTENCY_V1312.md`, `SMART_BATCH_APPROVAL.md`, `MICROTASK_ACCEPTANCE_REPAIR.md`, `APPROVAL_TRANSLATION_AUDIO.md`, `WORKFLOW.md`, `ACCEPTANCE_QC.md` **chỉ trong vấn đề phân loại ảnh hưởng lỗi ASR, chặn QC do lời thoại phụ, độ chi tiết cảnh và ưu tiên thực hiện**. Các giới hạn an toàn, nguồn/hashes, scope phê duyệt, quyền tải/cài/xóa, G05_SCRIPT/G07_VOICE/G10_PILOT, kiểm chứng hình ảnh, và lệnh không giả xác minh giữ nguyên.

**CẬP NHẬT v1.3.14 (ƯU TIÊN CAO HƠN):** Đọc [WHOLE_FILM_TRANSCRIPT_V1314](WHOLE_FILM_TRANSCRIPT_V1314.md) trước. Mọi lời hướng dẫn v1.3.13 đề xuất chạy `B004–B010`, "lô 10 phút", "QC riêng từng batch" hoặc tiếp `G02.M02.Bxxx` là **ví dụ lịch sử, không áp dụng cho tác vụ transcript mới**. G02 hiện nay dùng một `G02.ASR.FULL`, một WAV toàn phim, một lần gọi ASR, một Q02; streaming nội bộ không chia task. Các quy tắc triage STORY_FIRST và ưu tiên hình ảnh vẫn giữ nguyên.

## A. Mục tiêu sản phẩm — REVIEW-FIRST, VISUAL-FIRST

Đầu ra cuối là **video REVIEW tiếng Việt có cốt truyện chính xác, kể chuyện mạch lạc, cảnh phim đúng nhân vật/hành động/thời điểm và dựng nghe-xem tốt**, không phải biên bản giám định từng từ thoại. Mặc định `quality_mode=STORY_FIRST` (chế độ transcript forensic/STRICT chỉ dùng khi người dùng chủ động yêu cầu). **Không để 1–2 từ ASR sai ở cảnh phụ tiêu tốn nhiều lượt phê duyệt hoặc thời gian nghe WAV**; tập trung G02 đủ ý → G03 tóm/lược có kiểm soát → G04 thực sự quan sát phim → G05 viết REVIEW → G08 khớp cảnh với từng beat → G09/G10 preview → G11–G14 video cuối.

### Kết quả Q02 được đo theo hai trục riêng

- `TECHNICAL_QC`: nguồn đúng hash, WAV/ASR lưu được, timestamp/range bảo toàn, không mất lô và không bỏ bản ghi thô. `PASS` khi kiểm bằng file/ffprobe/hash, không có nghĩa tiếng nói nào cũng đúng.
- `STORY_QC`: mạch phim, sự kiện chính, nhân vật, nguyên nhân-hậu quả, timeline, các câu dùng làm **bằng chứng trong REVIEW**. Chỉ cần xác minh độ chính xác của những gì **sẽ được kể**; câu phụ không chắc thì **không dùng làm căn cứ**, có thể bỏ khỏi kịch bản review.
- QC riêng công đoạn G02 có thể ghi `QC_STATUS=PASS_WITH_WARNINGS` ở **lớp báo cáo nội dung** để người dùng hiểu cảnh báo nhỏ vẫn tồn tại. Nếu state machine/tool chỉ chấp nhận `PASS/NOT_VERIFIED/NEEDS_FIX/BLOCKED`, giữ **task QC=PASS** khi các tiêu chí bắt buộc của task đã đạt và thêm `warnings_nonblocking`, `story_relevance=LOW`, `impact_classification=MINOR_NONBLOCKING` (không tự sửa enum legacy). Không được đổi trạng thái của lỗi chưa chứng minh thành `HEARD_VERIFIED`.
- Q02 chính thức `PASS` sau **ASR toàn phim và QC chữ/format đơn giản** theo `SIMPLE_G02_TEXT_QC_V1316.md`; các nghi vấn nghĩa phim/đoạn thoại không khóa G02, chỉ ghi metadata để G04/G05/G08 đối chiếu khi cần. Không coi B001–B003 đã làm xong là hết G02.

## B. Triage 3 mức và quyết định có dừng hay không

| Mức | Điều kiện | Hành động mặc định |
|---|---|---|
| `MINOR_NONBLOCKING` | Câu chào/xã giao/thoại nền, lỗi lẻ 1–2 từ, lời ngắn không làm thay đổi ý cốt truyện, ASR nghi hallucination trong nhạc/SFX; **không được dùng làm chứng cứ REVIEW**, không liên kết sự kiện chính; audio/video nguồn vẫn đầy đủ | Giữ raw + quarantine/flag, đánh `UNVERIFIED_LOW_IMPACT`, **bỏ khỏi nội dung REVIEW** hoặc dùng tóm tắt trung lập đã xác minh độc lập; không đòi người dùng upload WAV, tiếp task/batch kế trong gói đã phê duyệt |
| `MATERIAL_REVIEW` | Không rõ mức ảnh hưởng, nghi sai tên nhân vật, **phủ định** đảo ý câu, mốc thời gian, động cơ, hành động quan trọng, ai thắng/thua, **tử vong**, bị mất lời dài liên quan plot | Kiểm thêm transcript cạnh bên và cảnh hình thật trong quyền được duyệt; nếu không thể bỏ chi tiết mà vẫn kể đúng thì dừng tại `MATERIAL_BLOCKER` và xin bằng chứng/nghe có mục tiêu |
| `MATERIAL_BLOCKER` | Thiếu cả batch/mất lô, source/**hash** sai, nguồn khác phim, sự kiện chính chưa xác minh nhưng chuẩn bị khẳng định, chuyển cảnh sai **nhân vật**/**actor** hoặc **action**, sai nhân quả, G05/G07/G10 chưa duyệt | Dừng phần phụ thuộc; không đoán/khai PASS, không tự chạy công cụ ngoài quyền; đề xuất hướng sửa có giới hạn và cổng phê duyệt phù hợp |

Một từ có thể là `MATERIAL_BLOCKER` nếu đảo kết luận (ví dụ “không”, tên hung thủ, số tiền, người chết); **số từ không phải tiêu chuẩn duy nhất**. Câu dài 30 giây nhưng chỉ ASR ra câu xã giao có thể là hallucination, cần cách ly, **không** lấy câu đó để khẳng định tình tiết. Nếu chi tiết không quan trọng thì không phải kéo user qua chu kỳ tải WAV–nghe–duyệt.

### Ngưỡng tự động không chặn

Với một lần nhận dạng toàn phim có `N` ứng viên thô: tối đa `max(2, ceil(0.02*N))` **2 ứng viên hoặc 2% theo ngưỡng rộng hơn** có thể là `MINOR_NONBLOCKING` nếu từng ứng viên đều không thuộc tình tiết cốt lõi, chưa được dùng trong REVIEW, và không thiếu đoạn phim/tiếng nói kéo dài ảnh hưởng truyện. Vượt ngưỡng thì rà soát nhóm cờ một lượt (không tạo từng vòng phê duyệt cho mỗi từ), ưu tiên quyết định ảnh hưởng câu chuyện hơn là đếm flag. Với `N` rất nhỏ, ngưỡng này không cấp quyền bỏ qua nội dung chính.

**B001/B003 Fatman:** ứng viên `G02-B001-S0101` “Thank you.” bị cách ly và người dùng nói chỉ nhạc/SFX; `G02-B003-S0062` “I don't know.” là ASR không chắc (đoạn 29,98 giây). **Đây là ứng viên để đánh giá `MINOR_NONBLOCKING` nếu không có liên hệ plot**, không phải chứng cứ đã nghe chính xác. Các câu này **không sử dụng làm chứng cứ** cho REVIEW nếu không được xác minh độc lập. Giữ nguyên raw, file quarantine, `NOT_VERIFIED` lịch sử, không chèn lời không tồn tại vào bản review; tránh xin user upload âm thanh thêm cho riêng hai câu này.

## C. Chuỗi công việc hiệu quả G01–G15

1. **G01** xác nhận phim nguồn, audio/video timing/hash một lần, giữ artifacts reuse hợp lệ; không cài lại thứ đã PASS.
2. **G02** ASR **toàn phim một tác vụ `G02.ASR.FULL`** theo `NO_BATCH_SPLIT`; hậu kiểm tự động và phân loại warning trong **một QC toàn phim**. Không lập gói mới chỉ có B004–B010; một lần duyệt toàn bộ source movie và đầu ra `analysis/transcript_original.jsonl`. Bao phủ hết nguồn trước Q02.
3. **G03** ChatGPT trực tiếp đọc & dịch bản transcript nguồn của tất cả ứng viên được giữ, ghi rõ `[LỜI THOẠI PHỤ CHƯA XÁC MINH]` cho chi tiết không cần dùng, không bịa câu khác. Khâu G05 không phải sao chép mọi câu; chỉ dựng dàn ý review từ sự kiện đáng tin cậy. Không dùng model/script dịch.
4. **G04 là hạng mục ưu tiên cao:** dùng scene detection + contact sheet/timeline toàn phim, ChatGPT **thực sự quan sát** ảnh/clip quan trọng để lập `scene_catalog`, `story_map`, `visual_events`, `characters`; rà các tình huống không lời và quan hệ thời gian. Bằng chứng video quan trọng hơn một câu thoại phụ bị nghi hallucination.
5. **G05** review 6 bước: kể đủ biến cố cốt lõi, mạch nhân quả, nút thắt, cao trào, kết; lời Việt tự nhiên, không lặp lời thoại nhỏ không giúp ích; dựng `review_outline` với `event_ids`, `source_scene_ids` và `visual_intent`. Giữ cổng duyệt **G05_SCRIPT**.
6. **G06–G07** chuẩn hóa beat/narration và WAV giọng theo quyền đã duyệt; giữ cổng duyệt **G07_VOICE**. Không mất chữ trong WAV đã duyệt.
7. **G08 là hạng mục ưu tiên cao nhất sau kịch bản:** mỗi beat chọn 2–3 candidate nếu có, đối chiếu `scene_catalog` với **hình ảnh/clip thật** để xác nhận **actor**, **action**, cảm xúc, tuyến truyện, đúng vị trí phim; ghi rejected candidates. Chọn clip dựa trên nội dung REVIEW, **không chọn chỉ vì ASR trùng chữ hoặc embedding similarity**. Beat quan trọng không có clip đã xem → `SHOT_SELECTION_READY=NOT_VERIFIED`; tìm shot thay thế hoặc điều chỉnh outline trước khi nó được duyệt, không lấy hình sai để lấp thời gian.
8. **G09** chỉ EDL/preview; **G10_PILOT** duyệt pilot mới được G11 full render. **G12–G14** QC video thật: `TECHNICAL_STATUS`, `STORY_STATUS`, `VISUAL_EDITING_STATUS` đều PASS. Người dùng chọn khi cần dựng/crop/nhạc không tự đặt ngoài phạm vi. G15 xuất thành phẩm; xóa file tách quyền `G15_DELETE`.

### Đánh giá thành công theo sản phẩm

Ưu tiên số 1: **cảnh hình đúng ý lời bình và phim gốc**, các nhân vật/sự kiện chính chính xác; ưu tiên số 2: review hấp dẫn, liền mạch; ưu tiên số 3: âm thanh giọng đọc và nhịp dựng; ưu tiên số 4: chi tiết transcript phụ. Nghiệm thu beat trọng yếu bằng `beat_id → review_claim → event_id → scene_id → src_in/out → visual_evidence_ref → match_status=VERIFIED_VISUAL`. `G08` không được nâng bằng chứng chưa xem thành VERIFIED_VISUAL, và `G14` phải kiểm sự phù hợp hình + lời thật.

## D. Quy tắc vận hành, phê duyệt, checkpoint

- Mỗi **WORK_PACKAGE_ID** vẫn cần scope hữu hạn, `plan_hash`, nguồn/đầu vào/đầu ra, đường dẫn, `approval` thật. Khóa `work_package.lock` phải atomic exclusive và không tự giành lock. Một gói có thể bao trùm nhiều batch đã chốt, QC nội bộ rồi chạy tiếp. Không tự chạy nền, không tải/cài ngoài quyền, không sửa nguồn phim/logo, không bật CPU fallback ngầm.
- `MINOR_NONBLOCKING` không phải hành động sửa transcript gốc: phân loại metadata là hành động QC hợp lệ **chỉ trong package được phê duyệt cho triage/tiếp tục**; không tự thêm hành động mới vào gói đã kết thúc. Không làm lại B001/B003, không ghi đè `NOT_VERIFIED`/legacy report cũ; tạo checkpoint **append-only** mới kèm `previous_state`, `warning_ids`, `reason_not_used_in_review`, `source_hash`, `plan_hash` và approval mới khi mở gói tiếp theo.
- Phân biệt `QC_STATUS=PASS` kỹ thuật với `STORY_QC=PROVISIONAL`: không ép `PACKAGE_PASS` hay Q02 PASS nếu chưa bao phủ toàn phim. Báo rõ tổng bao nhiêu đoạn đã được giữ, bao nhiêu đoạn bị cô lập và **không dùng làm chứng cứ**.
- Chỉ yêu cầu audio người dùng upload khi `MATERIAL_BLOCKER` không thể giải quyết bằng **xem hình/khảo sát bối cảnh** hoặc không thể bỏ khỏi review mà vẫn giữ ý đúng. Nếu người dùng không muốn nghe 1–2 từ phụ, ghi warning và tiếp công việc hợp lệ.
- Không tự tuyên bố ChatGPT đã nghe WAV chưa thực sự nghe được. Không được bịa câu thoại, không được bịa `HEARD_VERIFIED`, không gán một tình tiết chưa chứng minh thành fact.
- Khi gói kết thúc, **báo tổng sản phẩm và cảnh/beat**, không buộc người dùng phê duyệt từng flag/câu thoại; chỉ hỏi các quyết định sáng tạo thật sự quan trọng.

## E. Dòng quyết định kiểm thử

```text
ASR source + raw + flags
        |
        v
hash/coverage/lineage hợp lệ? -- NO --> MATERIAL_BLOCKER
        |
       YES
        |
        v
ứng viên có thay đổi sự kiện chính / được REVIEW sử dụng? -- YES --> MATERIAL_REVIEW
        |                                                       |
        NO                                                      v
        |                                         xem context/visual có đủ căn cứ?
        v                                                       |
đủ ngưỡng minor? -- YES --> MINOR_NONBLOCKING --> archive warning, không dùng trong REVIEW
        |                                |                      |
        NO                               v                      NO
        |                           tiếp batch               MATERIAL_BLOCKER
        v                                                       |
kiểm flags cả lô rồi quyết định theo mức ảnh hưởng            yêu cầu xác minh có mục tiêu
```

</details>
