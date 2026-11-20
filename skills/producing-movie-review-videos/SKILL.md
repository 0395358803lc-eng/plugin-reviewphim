---
name: producing-movie-review-videos
description: Use when the user invokes REVIEW_PHIM, works with remote movie workspace/transcript/translation/audio, or produces Vietnamese movie recap videos G01–G15 including YouTube metadata, thumbnail and intro.
---

# REVIEW_PHIM v1.3.26 — Production First → User Review → Targeted Revision

Với gói mới đã duyệt `execution_mode=PRODUCTION_FIRST_V1325`, dùng duy nhất
[PRODUCTION_FIRST_AUTONOMOUS_V1325](references/PRODUCTION_FIRST_AUTONOMOUS_V1325.md)
và [PRODUCTION_RELIABILITY_V1326](references/PRODUCTION_RELIABILITY_V1326.md).
`tools/project_flow_v1325.py` là state machine chuẩn, CLI là cầu nối cho host.
Đọc nhánh Production First trong các tham chiếu; **không thực thi các quy tắc Legacy bên dưới**.
Gói cũ tiếp tục đúng chế độ đã duyệt, không tự chuyển schema/checkpoint.

P00 → G01 nguồn → G02 ASR → G03 dịch → G04 hiểu phim → G05 kịch bản → G06 beats
→ G07 giọng → G08 shots → G09 timeline → G10 pilot → G11 dựng full
→ G11A metadata → G11B thumbnail → G12 intro → G13 nhạc → G14 kiểm MP4
→ G15 bàn giao → `FINAL_REVIEW` → người dùng `ACCEPTED`/`REVISION_REQUESTED`.

Một phê duyệt gói rõ phạm vi cho phép chạy các task liên tục bằng công cụ thật.
Không dùng Q01–Q15, QC từng scene/beat/WAV/shot/clip/batch, web crosscheck bắt buộc,
hay G14 ba trục làm điều kiện chuyển bước. Không tự mở gói sửa thẩm mỹ trước phản hồi.
MP4 phải có container/video stream/duration hợp lệ và giải mã được bằng công cụ đã duyệt.
`technical_ready=True` không đủ. File bắt buộc thiếu hoặc hỏng → `FAILED`.
`WARNING` ghi lại cho nghiệm thu cuối, không chặn sản xuất.

G05/G07/G10/G11A/G11B tạo đề xuất trước; nếu chưa có ủy quyền sáng tạo cụ thể,
chỉ chờ khi cần sử dụng đề xuất đó. G07 chưa được duyệt chỉ tạo giọng mẫu theo
`stage_proposals.G07` và trả `PROPOSAL_READY`; sau duyệt tiếp tục cùng task G07
làm WAV toàn phần, dùng lại mẫu đã lưu.
G11B tạo ảnh thật, cho tải và nêu một đích Windows đầy đủ trong JOB_DIR;
người dùng tự chép. Xác nhận và kiểm file thật xong tiếp tục G12 trong cùng gói,
không xin duyệt triển khai lần hai, không tạo lại ảnh trong lúc chờ chép.

Trước mỗi lần chạy/resume kiểm khóa thật và SHA-256 nguồn. Tác vụ DONE chỉ được
tái dùng khi đủ approval_ref, WORK_PACKAGE_ID, plan_hash, inputs/outputs và file thật.
Retry hữu hạn đúng `repair_budget`; thiếu quyền thì dừng. Ledger append-only là
nguồn trạng thái chuẩn; snapshot có thể khôi phục từ ledger. Không tự chạy nền.
Revision chỉ chạy phần phụ thuộc bị ảnh hưởng, dùng đường dẫn mới, giữ video cũ.

P00: chọn thiết bị, phim, JOB_DIR và **CHỌN THƯ MỤC CHỨA LOGO** trước
**KIỂM TRA PHẦN CỨNG MÁY CHỦ**, kiểm inventory chỉ đọc trong REVIEW_PHIM_WORKSPACE
được cấp quyền, rồi **TRÌNH DANH MỤC CÀI ĐẶT CHUẨN** nếu cần.
Ưu tiên GPU-FIRST theo [GPU_FIRST_APPROVAL](references/GPU_FIRST_APPROVAL.md);
CPU smoke không chứng minh GPU. Không tự đổi driver/PATH, cài mới hay CPU fallback.
Các công cụ chưa được cấp quyền **không được tự cài/tự chạy**.
Không mặc định `hflip=false`, tỷ lệ 2,04, 24 FPS hay crop 8%; dùng profile được duyệt.
Phê duyệt xóa riêng G15_DELETE, không ghi đè nguồn hay checkpoint cũ.

Các skill `analyze-video-editing`, `editing-montage`, `find-broll` hỗ trợ sản xuất
theo [EDITORIAL_SKILLS_INTEGRATION](references/EDITORIAL_SKILLS_INTEGRATION.md),
không khôi phục cổng QC Legacy. Gói mới dùng hướng dẫn v1.3.26;
`templates/WORK_PACKAGE_BRIEF.md` và `templates/WORK_PACKAGE_FINAL.md` là mẫu Legacy,
không lấy yêu cầu QC của chúng áp cho Production First.

## Nhánh Legacy — chỉ dành cho gói đã duyệt theo chế độ cũ

<details>
<summary>Quy tắc lịch sử; không áp dụng cho PRODUCTION_FIRST_V1325</summary>

# REVIEW_PHIM v1.3.25 — Production First + Autonomous Project Flow


**ƯU TIÊN CAO NHẤT v1.3.25 — PRODUCTION FIRST + AUTONOMOUS FLOW:** Khi lập **gói mới** và user chọn/duyệt `execution_mode=PRODUCTION_FIRST_V1325`, đọc [PRODUCTION_FIRST_AUTONOMOUS_V1325](references/PRODUCTION_FIRST_AUTONOMOUS_V1325.md) **trước tất cả tài liệu bên dưới**. Chỉ kiểm `OUTPUT_EXISTS`/file không rỗng/đúng path/SHA, MP4 có thể đọc; **không dùng Q01–Q15, microtask QC, G14 story/visual QC, 2-source web crosscheck hay duyệt thẩm mỹ trung gian để chặn tiến độ**. Giai đoạn DONE tự sang giai đoạn hợp lệ tiếp theo nhờ `tools/project_flow_v1325.py` (executor callback là ChatGPT công cụ thật trên máy được cấp quyền), ghi checkpoint/ledger và không tạo nút triển khai thứ hai. `G15` giao thành phẩm `FINAL_REVIEW`; chỉ người dùng quyết định `ACCEPTED` hoặc `REVISION_REQUESTED`, revision cục bộ sau đó. Cổng duyệt sáng tạo G05_SCRIPT/G07_VOICE/G10_PILOT/G11A_METADATA/G11B_THUMBNAIL có thể **ủy quyền rõ một lần trong plan hash** qua `creative_delegations`; không mặc định tự duyệt nếu không có quyền. Vẫn dừng khi cần user chép thumbnail thật vào JOB_DIR, cần cài mới ngoài scope, nguồn/quyền/hash sai, xóa G15 hoặc công cụ thất bại. Chế độ legacy đang chạy tiếp tục quy tắc v1.3.24, không đổi checkpoint. Không tự chạy nền liên lượt ChatGPT hoặc nói đã render/video có thật nếu chưa có output. **Mọi yêu cầu QC của tài liệu cũ bên dưới là LEGACY-ONLY đối với Production First**.


**ƯU TIÊN TỐI CAO v1.3.24 — CHATGPT TẠO ẢNH, NGƯỜI DÙNG TỰ CHÉP:** Đọc bắt buộc [MANUAL_THUMBNAIL_HANDOFF_V1324](references/MANUAL_THUMBNAIL_HANDOFF_V1324.md) khi tới G11B. ChatGPT tạo và xem ảnh 16:9 thật, cho người dùng tải qua giao diện ChatGPT, chỉ định chính xác một đích `<JOB_DIR>\assets\youtube_thumbnail.png` (JPG thì giữ `.jpg`) trên đúng thiết bị đã duyệt. **Không yêu cầu ChatGPT tự chuyển ảnh sang máy remote**. Chờ người dùng nhắn **“ĐÃ CHÉP ẢNH VÀ DUYỆT G11B”**; dùng một xác nhận cho đặt file + phê duyệt thumbnail, không xin duyệt lại khâu triển khai. G11B giữ core `WAITING_FOR_HUMAN_APPROVAL`, substatus `WAITING_FOR_USER_IMAGE_PLACEMENT`, không tạo Q11B PASS khi chưa kiểm file thật, decode/hình và SHA-256. Dùng `tools/manual_thumbnail_handoff_v1324.py` kiểm đường dẫn, định dạng, hash, lựa chọn thật; chỉ là QC offline, không phải quyền chạy remote. G12 đọc trực tiếp asset đã duyệt từ `publish/thumbnail_approval.json:image_relpath` để tạo intro 2 giây; không buộc ảnh phải tự upload hay nhân bản `intro_card.png`. v1.3.24 ưu tiên hơn yêu cầu transfer tự động/`BLOCKED_TRANSFER` trong các bản cũ; giữ đầy đủ G11A_METADATA, G11B_THUMBNAIL, Q12, media thật, lock/hash và quyền người dùng.

**ƯU TIÊN TỐI CAO v1.3.23 — MỘT ĐIỂM KIỂM SOÁT THỰC THI P00–G15:** Trước **mỗi task và mỗi lần resume**, đọc [FULL_WORKFLOW_INTEGRITY_V1323](references/FULL_WORKFLOW_INTEGRITY_V1323.md) và dùng `tools/workflow_integrity_v1323.py::validate_new_package` (gói mới), `decide_dispatch` (mỗi task) và `validate_package_completion` (trước PACKAGE_PASS). Không dùng riêng bộ kiểm core `can_dispatch` hoặc `publish_workflow_state.can_start_stage` làm kết luận cuối: QC alias `qc_gates_passed`/`passed_qc` phải nhất quán; mọi Q01–Q14, G11A/G11B, G07_VOICE, G10_PILOT, G15_DELETE phải được kiểm theo đúng stage và actual media. Áp dụng duyệt là chạy ngay v1.3.21; không xin duyệt từng batch, không sửa checkpoint cũ. G03 dùng transcript cleaned đã xác minh; G08 reuse G04 evidence; G09 chỉ EDL/preview, G10 một pilot; G12/G13 ưu tiên stream-copy video khi an toàn; G14 vẫn phải kiểm media thật. Công cụ policy offline không tự chạy Remote Desktop/FFmpeg và không thay quyền của người dùng.

**ƯU TIÊN TỐI CAO v1.3.22 — G04/G05 FAST TRACK, MỘT TASK / MỘT QC:** Đọc **bắt buộc** [G04_G05_FAST_TRACK_V1322](references/G04_G05_FAST_TRACK_V1322.md) ngay trước G04/G05 và trước lập package có hai stage này. Với **gói mới**, G04 duy nhất `G04.FILM.UNDERSTANDING.FULL` (scene index đầu-cuối, ChatGPT thực sự xem hình/clip các nút cốt truyện, tạo story_map/characters/visual_events/evidence_index, một Q04); G05 duy nhất `G05.REVIEW.FULL` (viết trọn kịch bản sáu bước, TTS/evidence map, kiểm narrative-only, web crosscheck tối thiểu hai nguồn độc lập và **một Q05**). CẤM sinh `G04.Mnn/Bxxx`, `G05.Mnn/Bxxx`, phê duyệt từng scene, từng đoạn hay từng vòng QC như những công việc mới. Các giới hạn 8 scene/24 ảnh hoặc 4 đoạn chỉ được xem là phân trang nội bộ, KHÔNG phải gate/danh sách task/phê duyệt. Phân tích shot đẹp/góc máy chi tiết chuyển trọng tâm sang G08, không chặn G04 bởi cảnh phụ UNKNOWN; chỉ xác minh thêm khi event chính hoặc claim G05 thực sự phụ thuộc. Dùng `tools/g04_g05_atomic_policy.py` xác thực cấu trúc package cùng `work_package_state.py` cho gói mới trước phê duyệt/thực thi. Giữ bằng chứng hình/clip thật, ZIP media v1.3.20 khi thiếu kênh xem/nghe, `G05_SCRIPT` duyệt trọn kịch bản, quyền hash/lock và ONE_APPROVAL_START v1.3.21. Quy tắc này ghi đè hướng dẫn Mnn/Bxxx/QC theo lô cũ của G04/G05 ở mọi tài liệu khác; không migrate gói legacy hay tự duyệt nội dung.

**ƯU TIÊN TỐI CAO v1.3.21 — MỘT PHÊ DUYỆT LÀ CHẠY NGAY:** Đọc **BẮT BUỘC** [ONE_APPROVAL_START_POLICY_V1321](references/ONE_APPROVAL_START_POLICY_V1321.md) cho P00 và mọi G01–G15/G11A/G11B. GỘP lập kế hoạch + phạm vi triển khai vào **một** `WORK_PACKAGE_ID` và **một** nút **“PHÊ DUYỆT VÀ CHẠY GÓI”**. Khi nhận đúng tin nhắn người dùng phê duyệt `APPROVE_PACKAGE` + `plan_hash` + thiết bị/JOB_DIR/scope, kiểm quyền/hash/preflight, acquire lock, chuyển `PROPOSED → APPROVED → RUNNING` **nội bộ trong cùng lượt** và **gọi ngay các công cụ thực thi những task đủ điều kiện**; tuyệt đối KHÔNG hỏi “có triển khai tiếp không?” hay mở vòng phê duyệt thực thi thứ hai. Dùng `tools/one_approval_dispatch_v1321.py` như bộ kiểm policy nếu được duyệt chạy Python; code chỉ kiểm trạng thái, không tự chạy tác vụ. Lưu QC/checkpoint, skip đã PASS, một lần click trùng không chạy lại. Giữ nguyên các human gate G05_SCRIPT, G07_VOICE, G10_PILOT, G11A_METADATA, G11B_THUMBNAIL, G15_DELETE và mọi giới hạn cài/tải, bảo mật, media QC. Quy tắc mới ưu tiên hơn tài liệu cũ **chỉ tại điểm tách "duyệt kế hoạch" và "triển khai"**; không cấp quyền thực thi không rõ phạm vi. Không chạy nền liên lượt hoặc tuyên bố hoàn tất khi chưa có output thật.

**ƯU TIÊN MỚI v1.3.20 — XEM/NGHE MEDIA BẰNG CHỨNG THẬT:** [MEDIA_EVIDENCE_HANDOFF_V1320](references/MEDIA_EVIDENCE_HANDOFF_V1320.md) (đọc BẮT BUỘC trước xử lý mọi sự cố ở G02/G03/G04/G05/G07/G08/G09/G10/G11/G12/G13/G14 đòi xem clip hoặc nghe audio). Nếu media không thể xem/nghe trực tiếp qua Remote Desktop Commander, trong phạm vi được duyệt ChatGPT trích clip/audio ngắn đúng timecode, đóng ZIP với manifest+SHA-256 trong `JOB_DIR/analysis/media_for_chat/<request_id>/` bằng `tools/media_evidence_handoff.py`; phải thông báo rõ tại sao cần chứng cứ, tạo **link tải có thật** chỉ nếu file thực sự được chuyển và xác minh (không bịa sandbox link/localhost từ đường dẫn remote). Không có transfer → `CHƯA CÓ LINK TẢI TRỰC TIẾP` + đường dẫn máy tính cho người dùng lấy ZIP/upload lại chat. ChatGPT chỉ nói đã **xem** hoặc đã **nghe** nếu đã thật sự kiểm tra media sau upload; ZIP tạo/upload/manifest/ASR không đủ. Không thể nghe sau upload → yêu cầu file WAV/MP4 riêng hoặc giữ `NOT_VERIFIED`/`WAITING_FOR_AUDIO_UPLOAD`. Áp dụng xuyên mọi giai đoạn, không chẻ thành hàng chục gói xét duyệt mới; không tự cấp quyền export dữ liệu ngoài package. Đây là ngoại lệ v1.3.20 có ưu tiên cao hơn hướng dẫn audio upload cũ nếu xung đột, giữ nguyên workflow và human gates khác.

**QUY TẮC MỚI SAU RENDER (ưu tiên v1.3.19):** [YOUTUBE_METADATA_POLICY_V1319](references/YOUTUBE_METADATA_POLICY_V1319.md), [THUMBNAIL_INTRO_POLICY_V1319](references/THUMBNAIL_INTRO_POLICY_V1319.md), [INTRO_CARD_INTEGRATION_V1319](references/INTRO_CARD_INTEGRATION_V1319.md). Giữ 15 giai đoạn chính và P00; chèn **G11A tạo tiêu đề/mô tả YouTube** và **G11B tạo thumbnail ChatGPT thực có chữ theo tiêu đề được chọn** giữa G11 và G12. G12 dùng ảnh được lưu thật vào JOB_DIR làm intro tĩnh **2 giây** và giữ logo/brand profile đã duyệt. G13 nhạc, G14 QC thật, G15 bàn giao thumbnail riêng/metadata/MP4. Bắt buộc tạo ảnh thật, thực sự xem và kiểm chữ tiếng Việt; người dùng tự tải/chuyển ảnh vào JOB_DIR theo v1.3.24, sau đó ChatGPT kiểm file/hash và ảnh thật. Chưa đặt ảnh => chờ người dùng, KHÔNG mặc định BLOCKED_TRANSFER vì không có kênh upload tự động. Không được PASS nhờ prompt hoặc log. Thumbnail riêng phải upload custom vào YouTube Studio nếu muốn chọn hiển thị; intro 2 giây không bảo đảm YouTube tự lấy ảnh đó. Không tự upload YouTube. Mỗi giai đoạn bổ sung một task/QC; không mở thêm phê duyệt vi mô. Human gates `G11A_METADATA` (chọn tiêu đề) và `G11B_THUMBNAIL` (chọn ảnh) trước G12; cần phân biệt gói cũ không có G11A/B và gói mới có chúng. Không đổi checkpoint hoặc quyền của dự án đang chạy.

**ƯU TIÊN SỐ 0 CHO G05:** [G05_WEB_STORY_CROSSCHECK_V1318](references/G05_WEB_STORY_CROSSCHECK_V1318.md) — sau khi viết xong REVIEW, trước Q05, ChatGPT trực tiếp tìm kiếm web, đọc ít nhất hai nguồn độc lập về đúng phim, đối chiếu logic/cốt truyện quan trọng với lời review và chứng cứ G04; chỉ sửa nếu phim/G04 hỗ trợ. Ghi sources/finding vào `review/g05_web_story_crosscheck.v1.json` và `qc/g05_web_story_crosscheck.v1.md`, tuyệt đối không đưa vào lời kể. Không tìm web thật -> Q05_WEB_STORY_CROSSCHECK=NOT_VERIFIED, không tự PASS.

**ƯU TIÊN TUYỆT ĐỐI G05 / LỜI REVIEW:** [G05_NARRATIVE_ONLY_V1317](references/G05_NARRATIVE_ONLY_V1317.md) — `review_ke_chuyen.txt` và `review_loi_binh_tts.txt` **chỉ kể chuyện phim**, cấm nhắc ASR, transcript, bản dịch, ChatGPT, hình đã xem, báo cáo, QC, web, tiến độ. Evidence/cảnh báo nằm riêng trong review_evidence_map/QC. Chạy `tools/g05_narrative_only_policy.py` trên hai bản trước Q05; giữ sáu bước, một G05 và cổng `G05_SCRIPT` riêng.

**ƯU TIÊN SỐ 1 CHO G02:** [SIMPLE_G02_TEXT_QC_V1316](references/SIMPLE_G02_TEXT_QC_V1316.md) — G02.ASR.FULL toàn phim, một Q02 cho transcript sạch Unicode/format/chính tả rõ ràng; không ép QC 17 cụm hội thoại nhỏ hoặc sửa nội dung từ đoán. Xác minh cốt truyện chuyển sang G04/G05/G08.

**ĐỌC TIẾP:** [ATOMIC_STAGES_V1315](references/ATOMIC_STAGES_V1315.md), [WHOLE_FILM_TRANSCRIPT_V1314](references/WHOLE_FILM_TRANSCRIPT_V1314.md), [STORY_FIRST_WORKFLOW_V1313](references/STORY_FIRST_WORKFLOW_V1313.md), [WORKFLOW_CONSISTENCY_V1312](references/WORKFLOW_CONSISTENCY_V1312.md), [SMART_BATCH_APPROVAL](references/SMART_BATCH_APPROVAL.md). Phần cũ G01–G11 và G13–G15 giữ nguyên trừ QC/delivery liên quan intro, không tự thay cấu trúc các task trước.

## Nhiệm vụ sản xuất

- **P00**: chọn thiết bị qua Remote Desktop Commander, chọn nguồn, kiểm tra workspace cũ/runtime/model/cache có thể tái sử dụng, hardware preflight và danh mục cài; chưa được phép thì không tải/cài.
- **G01**: `G01.SOURCE.FULL`, kiểm FFprobe/hash/timebase/media manifest/visual source profile và một Q01. G01 PASS/evidence hash còn hợp lệ được tái sử dụng.
- **G02**: `G02.ASR.FULL`, WAV toàn phim, ASR toàn phim, transcript/Q02 đơn nhất; lỗi lặt vặt không chặn hiểu phim.
- **G03**: `G03.TRANSLATE.FULL`, ưu tiên transcript_cleaned đã xác minh theo v1.3.16; ChatGPT dịch toàn bộ transcript theo segment/timecode và một Q03. Cửa sổ nội bộ 40 segment/1.000 từ không phải microtask hoặc approval; không dùng script/local model/API để dịch.
- **G04**: ChatGPT xem frame/clip thật, lập scene catalog/characters/story_map/visual events và `FILM_UNDERSTANDING_READY`; model AI tạo candidates không được tự `VERIFIED_VISUAL` nếu ChatGPT chưa xem evidence thật.
- **G05**: `G05.REVIEW.FULL`, một kịch bản REVIEW sáu bước hoàn chỉnh, một Q05, đối chiếu web, kiểm NARRATIVE_ONLY; bắt buộc phê duyệt `G05_SCRIPT` trước G06.
- **G06–G07**: phân beats khôi phục 100% lời TTS đã duyệt; giọng VieNeu và kiểm chất lượng WAV, cổng `G07_VOICE` trước TTS hàng loạt.
- **G08**: beat → event → scene → clip, kiểm actor/action/storyline/emotion thật; chỉ shot có `VERIFIED_VISUAL` thích hợp mới chọn; `SHOT_SELECTION_READY`.
- **G09–G10**: EDL/timeline/Remotion preview → pilot thực, `G10_PILOT` người dùng duyệt trước khi render full.
- **G11**: render full đã duyệt theo EDL, visual transforms cần thiết; Q11 kỹ thuật/hình, không ép upscale hoặc làm sai nguồn.
- **G11A**: `G11A.YOUTUBE_METADATA.FULL`, tạo 3–5 tiêu đề + mô tả + hashtags/tags từ review đã duyệt và phim thực; một Q11A, chọn title với human gate `G11A_METADATA`, lock hash title.
- **G11B**: `G11B.THUMBNAIL.FULL`, dùng ChatGPT thực sự tạo thumbnail 16:9, có chữ từ title và kiểm hình/tiếng Việt bằng mắt. Người dùng tải ảnh từ ChatGPT và tự chép vào `JOB_DIR/assets/youtube_thumbnail.png` hoặc JPG đúng định dạng, rồi gửi một xác nhận đặt file + duyệt G11B. ChatGPT kiểm file, SHA-256, định dạng, decode/visual thật trước Q11B. Không nhầm prompt với ảnh, không yêu cầu remote upload tự động.
- **G12**: sử dụng ảnh G11B làm `assets/intro_card_2s.mp4`, ghép đúng 2 giây vào đầu video full G11, đẩy lời thuyết minh trọn vẹn sang sau intro, đặt logo theo `brand_profile` đã được duyệt, tránh chèn trùng intro; một Q12 gồm xác minh MP4/frame/audio thực.
- **G13**: nhạc nền/sidechain, kiểm âm lượng A/B, không tải nhạc ngoài quyền đã duyệt.
- **G14**: QC MP4 cuối thực tế, ba trạng thái độc lập TECHNICAL/STORY/VISUAL_EDITING cùng PASS mới sẵn sàng xuất bản; kiểm thêm intro 2 giây, chữ, logo, thời gian voiceover, hash thumbnail và metadata khớp. Không tuyên bố kiểm 100% nếu chưa thực sự nghe/xem đủ.
- **G15**: bàn giao MP4, Remotion/EDL, thumbnail JPG/PNG riêng, metadata title/description/hashtag, source/manifest/hash/ZIP; xóa chỉ nếu có `G15_DELETE` theo file cụ thể.

## Phê duyệt, an toàn và trạng thái

- `WORK_PACKAGE_ID`, `schema_version=work-package.v2`, finite task IDs hoặc bounded batches, canonical `plan_hash`, deviceId, roots, source hash, tool/model/install budget, repair budget, stop condition, expected artifacts. Human gates nội dung `G05_SCRIPT`, `G07_VOICE`, `G10_PILOT`, mới `G11A_METADATA`, `G11B_THUMBNAIL` khi phạm vi bao gồm chúng; riêng `G15_DELETE` cho xóa. Từ v1.3.23 sử dụng **duy nhất** `tools/workflow_integrity_v1323.py::decide_dispatch` để ra quyết định chạy, đồng thời vẫn dùng `work_package_state.py` cho hashing/transition/lock. `publish_workflow_state.py` là tài liệu API legacy, không tự làm kết luận điều phối; không coi policy check là quyền thực thi.
- Package mới chứa `G11A` và `G11B`: bắt buộc Q11 trước G11A, Q11A + G11A_METADATA trước G11B, Q11B + G11B_THUMBNAIL trước G12; không làm sai phê duyệt G05/G07/G10. Gói legacy chưa bổ sung hai stage chỉ được tiếp tục theo quyền được cấp; không tự mở rộng scope hay làm lại G11.
- Không tự chạy nền giữa các lượt chat; không download/install, CPU fallback, thay OS/PATH/driver, đăng YouTube, chuyển file vào remote hoặc xóa dữ liệu khi chưa được cấp quyền phù hợp. Giữ source movie/logo read-only, ghi trong JOB_DIR, snapshot append-only; `work_package.lock` atomic không cướp, `NOT_VERIFIED` cũ không tự đổi PASS.
- Chỉ nói đã xem/nghe/tạo/tải/ghép ảnh hoặc video nếu công cụ thật chạy và có bằng chứng. Mẫu ảnh người dùng cung cấp là tham chiếu mỹ thuật, không sao chép nhãn hiệu/kênh người khác. Thay title hoặc ảnh sau phê duyệt phải có revision mới, invalidate Q11B/G12/G14/G15 phụ thuộc và phê duyệt tương ứng.

## Tham chiếu

- [MEDIA_EVIDENCE_HANDOFF_V1320](references/MEDIA_EVIDENCE_HANDOFF_V1320.md) và `tools/media_evidence_handoff.py` là quy trình bắt buộc khi vấn đề quan trọng đòi **actual short media** qua ZIP upload.

- [WORKFLOW](references/WORKFLOW.md), [DEFAULTS_AND_TOOLS](references/DEFAULTS_AND_TOOLS.md), [MODEL_ROLE_POLICY](references/MODEL_ROLE_POLICY.md), [ACCEPTANCE_QC](references/ACCEPTANCE_QC.md), [EVIDENCE_SCHEMA](references/EVIDENCE_SCHEMA.md), [FILM_UNDERSTANDING](references/FILM_UNDERSTANDING.md), [SCENE_MATCHING](references/SCENE_MATCHING.md), [VISUAL_EDITING](references/VISUAL_EDITING.md), [REVIEW_STORYTELLING](references/REVIEW_STORYTELLING.md).
- [GPU_FIRST_APPROVAL](references/GPU_FIRST_APPROVAL.md), [WORKSPACE_REUSE_POLICY](references/WORKSPACE_REUSE_POLICY.md), [INSTALLATION_CATALOG](references/INSTALLATION_CATALOG.md), [WORKSPACE_BOOTSTRAP](references/WORKSPACE_BOOTSTRAP.md), [HARDWARE_PROFILE](references/HARDWARE_PROFILE.md).
- [MICROTASK_ORCHESTRATION](references/MICROTASK_ORCHESTRATION.md), [MICROTASK_ACCEPTANCE_REPAIR](references/MICROTASK_ACCEPTANCE_REPAIR.md), [SESSION_ORCHESTRATION](references/SESSION_ORCHESTRATION.md), [APPROVAL_TRANSLATION_AUDIO](references/APPROVAL_TRANSLATION_AUDIO.md).
- `tools/youtube_metadata_policy.py` và `tools/thumbnail_intro_policy.py` chỉ QC cấu trúc/dữ liệu offline, **không phải** công cụ tạo hình, render, nghe/xem hay cấp quyền. Không mặc định thời lượng review, `hflip`, FPS, crop % hay số shot/beat; intro được người dùng chọn 2 giây là ngoại lệ đã xác nhận.

</details>
