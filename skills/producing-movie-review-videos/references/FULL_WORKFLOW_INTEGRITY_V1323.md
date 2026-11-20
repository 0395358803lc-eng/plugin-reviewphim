# FULL_WORKFLOW_INTEGRITY_V1323 — REVIEW_PHIM v1.3.23

> **v1.3.25 — PRODUCTION_FIRST_V1325:** Với gói mới đã duyệt mode này, ưu tiên [PRODUCTION_FIRST_AUTONOMOUS_V1325.md](PRODUCTION_FIRST_AUTONOMOUS_V1325.md). Các Qxx/QC thẩm mỹ, nghe/xem, web và phê duyệt sáng tạo giữa giai đoạn trong tài liệu dưới đây là **LEGACY-ONLY**; mode mới dùng DONE đầu ra kỹ thuật và chờ user nghiệm thu cuối. Giữ nguyên quyền thiết bị/source/install/delete và thao tác chép thumbnail thật.


> **BỔ SUNG v1.3.24:** Khi G11B tạo thumbnail ChatGPT, dùng [MANUAL_THUMBNAIL_HANDOFF_V1324.md](MANUAL_THUMBNAIL_HANDOFF_V1324.md): người dùng tự tải/chép vào JOB_DIR; Q11B chờ file thật và một thông điệp xác nhận+duyệt, không đòi upload tự động. G12 chỉ dùng ảnh theo `image_relpath/image_sha256` đã được khóa; state core giữ `WAITING_FOR_HUMAN_APPROVAL` cho đến khi user quyết định. Đây không phải lượt duyệt lại triển khai.

**ƯU TIÊN CAO NHẤT CHO ĐIỀU PHỐI P00–G15 (bao gồm G11A/G11B).** Đọc cùng `ONE_APPROVAL_START_POLICY_V1321.md`, `G04_G05_FAST_TRACK_V1322.md`, `MEDIA_EVIDENCE_HANDOFF_V1320.md`, `WORKFLOW_CONSISTENCY_V1312.md` và `ACCEPTANCE_QC.md`. Tài liệu này ghi đè **chỉ** các chỉ dẫn cũ bắt dừng xin duyệt mỗi Gxx/Mnn/Bxxx, chuyển plan→execution thành hai lần click, hoặc dùng nhiều quy tắc QC không thống nhất. **Không** ghi đè quyền người dùng, media thực, hash/lock, giới hạn cài đặt, script/voice/pilot/thumbnail approvals, hay quy tắc bảo toàn dữ liệu cũ.

## 1. Một nguồn sự thật về quyết định chạy task

- **BẮT BUỘC** trước khi trình package mới: `work_package_state.plan_hash/expand_tasks`, `tools/workflow_integrity_v1323.py::validate_new_package`. G01–G05 là FULL atomic; `G04.FILM.UNDERSTANDING.FULL`/`G05.REVIEW.FULL` có `NO_STAGE_SPLIT`, không tạo approval giữa scene/paragraph. G11A/B cũng là một task mỗi stage. Phê duyệt `APPROVE_PACKAGE` phải đến **tin nhắn người dùng thật**, đủ deviceId, source SHA-256, JOB_DIR, scope, plan_hash; một lần phê duyệt chuyển state sang RUNNING trong cùng lượt và gọi task đầu tiên đủ điều kiện, không thêm nút “bắt đầu triển khai”.
- **BẮT BUỘC trước MỌI task**, kể cả tiếp tục gói: sau khi xác minh lock đang thực sự thuộc owner và source/approval/output, gọi `tools/workflow_integrity_v1323.py::decide_dispatch(plan,state,task_id,session_owner=...)`. Đây là **một điểm kiểm soát quyết định** bao gồm khóa/phạm vi/Qxx/approval/visual QC; không trực tiếp gọi riêng `work_package_state.can_dispatch` hoặc `publish_workflow_state.can_start_stage` làm quyết định cuối. Khi guard báo BLOCKED thì dừng đúng task phụ thuộc và báo lý do; không dùng phê duyệt package làm giấy phép vượt human gate. Bộ kiểm là **logic offline**, không tự kết nối Remote Desktop Commander, không được xem là chứng cứ đã thi hành lệnh.
- Chỉ lưu `qc_gates_passed` làm trường QC thống nhất. `passed_qc` là alias lịch sử, được đọc **chỉ nếu không xung đột**; nếu cùng xuất hiện mà khác nhau phải tra chứng cứ, không lấy phép hợp (union) để mở gate. QC từ gói trước có thể sử dụng sau khi xác minh source hash/approval_ref/artifact còn đúng và ghi vào stage evidence ledger của phiên, **không đòi các giai đoạn trước nằm trong task_ids của gói đang chạy**.
- `tools/workflow_integrity_v1323.py::validate_package_completion` là tiền kiểm `PACKAGE_PASS`; sau đó vẫn gọi `work_package_state.transition(...,PACKAGE_PASS,...)`. Hai bước đều bắt buộc; không gọi PASS khi đầu ra chưa xác minh, tác vụ nào đó chưa QC hoặc còn human approval. Không sửa checkpoint đời cũ; với package legacy phải có provenance/hashes rõ và đánh dấu `legacy_package_verified`, không tự migrate.

## 2. Dependency map và cổng nội dung thực

| Stage | Q bắt buộc trước khi bắt đầu | Gate/điều kiện bổ sung |
|---|---|---|
| P00 | Không | Device/root được duyệt; hardware read-only, inventory runtime cũ đúng root; không tự tải/cài |
| G01 | P00/scope thực | G01.SOURCE.FULL → Q01 một lần, reuse source profile hợp lệ |
| G02 | Q01 | G02.ASR.FULL, ASR đúng toàn phim và transcript cleaned Q02 một lần |
| G03 | Q02 | G03.TRANSLATE.FULL: **ưu tiên `analysis/transcript_cleaned.v*.jsonl`** khi QC/hash hợp lệ, chỉ dùng raw/original nếu cleaned không được tạo và original được QC hợp lệ; không tự dịch bằng model khác |
| G04 | Q03 | G04.FILM.UNDERSTANDING.FULL, ChatGPT thực xem cảnh chính, Q04 một lần; thiếu media thật thì chờ |
| G05 | Q04 | G05.REVIEW.FULL, kể trọn sáu bước, web đối chiếu hai nguồn, Q05 rồi **G05_SCRIPT** trước G06 |
| G06 | Q05 + G05_SCRIPT | Beat coverage khôi phục đúng 100% lời TTS đã duyệt, Q06 |
| G07 | Q06 | Chọn giọng, tạo sample trước; phải có **G07_VOICE** trước TTS hàng loạt, Q07 sau audio thật |
| G08 | Q07 | Reuse G04 evidence, kiểm actor/action/clip thật, Q08 SHOT_SELECTION_READY |
| G09 | Q08 | Một EDL canonical, QC timeline Q09, **không render full** hoặc dựng thêm pilot trùng |
| G10 | Q09 | Dựng/xem-nghe một pilot đại diện (reuse nếu đã đúng hash), Q10 rồi **G10_PILOT** trước G11 |
| G11 | Q10 + G10_PILOT | Render video full một lần theo EDL, Q11 |
| G11A | Q11 | Metadata một lần Q11A; user chọn title qua **G11A_METADATA** |
| G11B | Q11A + G11A_METADATA | Thumbnail ChatGPT → người dùng tải/chép vào một đích JOB_DIR → remote file/hash/visual QC thật, Q11B rồi **G11B_THUMBNAIL** |
| G12 | Q11B + G11B_THUMBNAIL | 2s intro/logo/voice offset từ `image_relpath` đã được người dùng đặt/duyệt; Q12, không chèn trùng, kiểm ảnh thật |
| G13 | Q12 | Music ducking, verify license + nghe A/B, Q13 |
| G14 | Q13 | Technical/story/visual 3 trục PASS với actual media inspections; Q14 |
| G15 | Q14 + G14 evidence 3 trục | Deliver mp4/thumb/metadata/hash/ZIP, Q15; **G15_DELETE** chỉ nếu đã duyệt cụ thể delete_paths |

**G07_VOICE, G10_PILOT, G11A_METADATA, G11B_THUMBNAIL** không phải quyền cần có trước khi **tạo bản sample/pilot/title/thumbnail để người dùng quyết định**; chỉ chặn các hành động tiêu thụ kết quả đã duyệt (TTS hàng loạt/G11 full/G11B/G12). G05_SCRIPT là quyết định trên toàn bộ kịch bản đã hình thành. G15 delivery không chặn vì người dùng không yêu cầu xóa. Legacy packages trước G11A/G11B không được tự chèn bước mới; phải xác minh lineage cũ rồi mới dùng legacy override và không bỏ QC.

## 3. Tối ưu G06–G10, tránh tạo việc nhỏ liên tiếp

- G06 một Q06 tổng; `beat_visual_brief.json` optional, không tạo task riêng cho từng beat khi không cần.
- G07 tạo một bộ sample hữu hạn, trình lựa chọn `G07_VOICE` khi phải hỏi; WAV theo beat có cache `text_hash+voice/model/settings`, chỉ reuse khi file bytes SHA256 và input đã duyệt khớp, sample không được coi là full TTS.
- G08 tìm candidate từ G04 `evidence_index`, không chạy lại nhận diện toàn phim nếu checksum và evidence phù hợp; clip quan trọng phải do ChatGPT xem thực, mở rộng có mục tiêu khi thiếu; chunk 12 beat là phân trang **nội bộ** không phải microtask/approval/WORK_PACKAGE_ID mới, một Q08 tổng thể.
- G09 **không** tự render thêm pilot lớn và **không** tự render full; một edit_decisions.json làm EDL source of truth. G10 tạo đúng một pilot đại diện theo EDL/WAV và ghi `pilot_id` từ sha256 EDL+selected beat range+voice/profile. Nếu pilot đã PASS và hash thật còn đúng, reuse; không dựng lại chỉ vì chuyển giai đoạn hoặc nhận tin nhắn “tiếp tục”. Chỉ xuất thêm pilot nếu style/scope thay đổi và người dùng duyệt.
- Rủi ro quan trọng về motion, nhân vật, phát âm hoặc crop phải dùng ZIP media ngắn và xem/nghe thật; lỗi phụ không gây đổi cốt truyện là warning, không biến thành package mới.

## 4. Tối ưu G11–G15, tránh encode vòng lặp

- G11 render full đúng một lần (single-pass khi khả thi) khi Q10/G10_PILOT đủ. G12 dùng thumbnail đã duyệt và nối 2s + logo; ưu tiên concat/remux bằng **stream copy chỉ khi codec, resolution, fps, timebase, extradata và audio layout tương thích**; nếu cần reencode, ghi lý do/sha, không làm lại G11. Tránh intro cũ chồng intro mới; kiểm PTS, audio delay và frame 2s thật.
- G13 mix nhạc/voice: khi tương thích, **copy video stream** từ G12 và encode lại **audio-only**, không encode lại toàn hình. Chỉ reencode video nếu bắt buộc và có lý do/giới hạn duyệt rõ; không tự tải nhạc không giấy phép. Một Q13 tổng.
- G14 phải **kiểm decode/toàn file bằng công cụ** và kiểm **thật** các video clip/âm thanh có ý nghĩa; lưu timecode, hash, reviewer, vấn đề. Nếu chưa xem/nghe liên tục toàn phim, ghi riêng `CONTINUOUS_END_TO_END=NOT_VERIFIED`, **không** nói “đã xem/nghe 100%”; nếu chính sách phát hành của job yêu cầu toàn bộ thì giữ Q14 `NOT_VERIFIED` và dùng việc trích media có giới hạn đã duyệt. Metadata hoặc model auto-score không là bằng chứng cảm giác nghe/nhìn. Chỉ Q14 PASS khi cả `TECHNICAL_STATUS/STORY_STATUS/VISUAL_EDITING_STATUS` đều PASS theo QC thực và những đoạn bắt buộc đã được xác minh.
- G15 bàn giao không tự bật nhánh delete. `delete_paths` phải rõ ràng và phê duyệt G15_DELETE; không xóa source movie/logo/workspace cũ. Gói delivery có thể PASS với `DELETE_NOT_REQUESTED`.

## 5. Checkpoint, cache, xử lý lỗi và nghiệm thu

- Trước skip tác vụ đã PASS, xác minh nguồn SHA256, input hashes, file tồn tại dưới JOB_DIR và bytes SHA256 thật; dùng `tools/workflow_integrity_v1323.py::reuse_evidence` cho các file nằm trong JOB_DIR; không coi JSON hay `QC_STATUS=PASS` một mình là cache hợp lệ. Không copy runtime/model ngoài quyền.
- `NOT_VERIFIED`, `WAITING_FOR_AUDIO_UPLOAD`, `WAITING_FOR_HUMAN_APPROVAL`, `BLOCKED`, `WAITING_FOR_JOB`, `PARTIAL` là trạng thái thật. Một package đã được duyệt chỉ yêu cầu người dùng “Tiếp tục cùng gói” sau khi lượt chat dừng; không xin phê duyệt thiết kế/thi hành lại.
- Nếu action ngoài budget, thay source/movie/hash, thay model/runtime/driver, thay stage/scope, xóa file hay mở network mới: dừng và xin duyệt gói hữu hạn mới. Vẫn theo giới hạn sửa 2/issue, 4/gói khi được duyệt.
- Kiểm thử `tests/test_workflow_integrity_v1323.py` là **hợp đồng offline**; không chứng minh app đã thật gọi guard trước mỗi lệnh Remote Desktop, media đã được nghe/xem, hoặc tốc độ render được cải thiện. Nghiệm thu trên job thật phải có measured runtime và artifact thật.
