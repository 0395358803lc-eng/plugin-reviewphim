# REVIEW_PHIM v1.3.26 — Production First

Mode ổn định: `PRODUCTION_FIRST_V1325`. Quy trình đang áp dụng là
[PRODUCTION_RELIABILITY_V1326](PRODUCTION_RELIABILITY_V1326.md).
**Đọc và thực thi tài liệu v1.3.26; phần v1.3.25 bên dưới chỉ lưu lịch sử.**

Production First → User Review → Targeted Revision. Không dùng Q01–Q15.
`OUTPUT_EXISTS` phải có file thật/hash khớp; MP4 phải qua FFprobe và giải mã
FFmpeg được cấp quyền. Không nhận cờ executor làm bằng chứng thay thế.
`DONE` tiếp tục; retry hữu hạn trong quyền/ngân sách; đọc khóa thật trước resume.
G05/G07/G10/G11A/G11B tạo proposal rồi mới chờ duyệt sử dụng nếu chưa ủy quyền.
G11B chờ người dùng chép ảnh, kiểm file xong tiếp tục G12 cùng gói.
`FINAL_REVIEW` chỉ sau video dùng được; người dùng chọn `ACCEPTED` hoặc
`REVISION_REQUESTED`. Revision giữ video cũ, chỉ dựng phần bị ảnh hưởng.
Host/Remote Desktop Commander thực thi công cụ thật; Python không tự gọi công
cụ ChatGPT và không tự chạy nền qua lượt chat.

Ledger append-only là nguồn trạng thái chuẩn. `work_package_state.can_dispatch`
nhận plan Production First sẽ route về project_flow, không áp QC Legacy.
Không sửa checkpoint cũ thiếu provenance. CLI v1.3.26 yêu cầu `--owner` thật.

## Lịch sử v1.3.25 — không dùng làm chỉ dẫn thực thi v1.3.26

<details><summary>Thiết kế trước bản sửa reliability</summary>

**CHÍNH SÁCH ƯU TIÊN CAO NHẤT cho gói mới có `execution_mode=PRODUCTION_FIRST_V1325`.** Thay thế toàn bộ các vòng QC về chất lượng nội dung, hình, giọng, web, storyboard, shot, pilot, edit và G14 trước khi có phim hoàn chỉnh. Các tài liệu v1.3.11–v1.3.24 vẫn dùng cho **gói legacy** hoặc tham khảo cách sản xuất, nhưng **Q01–Q15 không còn là cổng bắt buộc trong chế độ mới**. Không sửa các checkpoint/approval lịch sử; muốn chuyển gói đang chạy phải lập gói mới được người dùng duyệt rõ phạm vi.

## 1. Mục tiêu: làm xong video → người dùng nghiệm thu → sửa theo yêu cầu

1. Một lần trình `WORK_PACKAGE_ID` đầy đủ với `plan_hash`, thiết bị, phim, root, tools/models/budget, task scope P00/G01–G15 + G11A/G11B và `execution_mode=PRODUCTION_FIRST_V1325` và `creative_delegations` được hiển thị rõ. **Một nút “PHÊ DUYỆT VÀ CHẠY GÓI”** cho phép khởi chạy ngay trong cùng lượt; không tách riêng phê duyệt kế hoạch và thực thi.
2. ChatGPT gọi công cụ thật cho từng công việc đã được duyệt; sau khi hoàn thành, **chỉ kiểm `OUTPUT_EXISTS`/file đọc được, không rỗng, đúng đường dẫn và SHA-256, mã thoát chương trình**, và khi có MP4 cần kiểm tối thiểu container/codec bằng công cụ thực. Không chạy QC thẩm mỹ, không buộc ChatGPT nghe/xem từng đoạn hoặc đối chiếu 2 nguồn web để qua bước; không tạo Qxx, CHECKLIST, QC report, báo cáo lỗi nhỏ, nhánh sửa chất lượng giữa các giai đoạn.
3. `DONE` → tự động chọn và chạy công việc hợp lệ tiếp theo trong phạm vi. `WARNING` về thẩm mỹ/cốt truyện/âm lượng/giọng/crop/chữ… chỉ được ghi lại cho người dùng nghiệm thu cuối, **không** mở task sửa hay hỏi duyệt để sửa. `FAILED` chỉ khi công cụ lỗi, đầu ra thiết yếu không tồn tại/không dùng được, sai hash/path hoặc thiếu dữ liệu làm cho bước sau không chạy. Hỗ trợ retry hữu hạn trong `repair_budget` cho **lỗi kỹ thuật**, không làm nhiều vòng QC.
4. G14 trong mode mới chỉ xác định MP4 cuối có thật, đọc được và phép kiểm decode/container tối thiểu đã chạy thành công. Không xem/nghe liên tục, không yêu cầu TECHNICAL/STORY/VISUAL_EDITING `PASS`, không áp quy tắc `CONTINUOUS_END_TO_END` làm cổng. G15 bàn giao MP4 thực + source/EDL/voice/metadata/thumbnail có trong scope và hashes; khi có G15, đánh `FINAL_REVIEW`, **không tự đánh `ACCEPTED`**.
5. User xem thành phẩm: `ACCEPTED` hoặc `REVISION_REQUESTED` qua tin nhắn người dùng thật. Bản dựng cũ/ảnh/EDL không bị sửa hay xóa; yêu cầu sửa phải chỉ đích stage/clip/timecode cần sửa và mở revision scope được duyệt, tận dụng cache/artifacts còn đúng. Không tự bắt đầu lại P00–G05 vì một lỗi phụ thuộc đã khoanh vùng.

## 2. Một nguồn sự thật và trạng thái

- Runner chính: `tools/project_flow_v1325.py` với `validate_plan`, `decide_next`, `validate_artifacts`, `run_until_hinge`, `checkpoint`, `read_checkpoint`, `resume_after_user`, `merge_verified_completions`, `user_review`. **Công cụ chỉ chạy liên tiếp khi host cung cấp executor callback đang thực thi lệnh thật trên thiết bị đã duyệt** (Remote Desktop Commander, FFmpeg/ASR/TTS/Remotion hoặc ImageGen từ ChatGPT theo khả năng thực tế). Đây là mã điều phối có thể dùng trên máy cục bộ, **không tự có kết nối Remote Desktop Commander, không tự gọi image generation và không tự chạy nền qua lượt chat**. ChatGPT là executor adapter: gọi từng công cụ được duyệt trong cùng lượt, đọc kết quả và lập record.
- Trước lập gói mới, kiểm `work_package_state.plan_hash`, `workflow_integrity_v1323.validate_new_package` (route production mode sang `project_flow_v1325.validate_plan`). Trước từng task dùng `workflow_integrity_v1323.decide_dispatch` ở mode này, kiểm khóa/device/source/approval/task order và artifact của mọi stage đã DONE; **không gọi `work_package_state.can_dispatch` để chặn bằng Qxx**. Sau mỗi tác vụ lưu atomically `JOB_DIR/logs/project_flow_v1325.json`, append-only `JOB_DIR/logs/project_flow_v1325.jsonl` gồm task, output checksum, trạng thái thực tế, user gates và warning.
- State task: `PENDING`, `RUNNING`, `DONE`, `WARNING`, `FAILED`, `WAITING_USER`. State project: `PACKAGE_DONE` (đã hết stage trong scope nhưng chưa có G15), `FINAL_REVIEW` (bàn giao qua G15), `ACCEPTED`, `REVISION_REQUESTED`. Chỉ `FINAL_REVIEW` có quyền ghi nhận người dùng nghiệm thu cuối. Trên gói đang có trạng thái `WAITING_USER`, phải có tin nhắn/điều kiện ngoài được giải quyết thật trước khi resume; không tự sửa state để giả hết blocker.
- **Không dùng Q01–Q15** hoặc `QC=PASS` để xác nhận tiến độ mới, không ghi ngược trạng thái lịch sử. `validate_package_completion()` có nhánh production để xác minh stage artifacts và trả completion, **không** gọi core `transition(...,PACKAGE_PASS)` của legacy vì core vẫn đòi QC/human gate cũ; dùng `PACKAGE_DONE`/`FINAL_REVIEW` ở project flow.
- `G01/G02/G03/G04/G05/G11A/G11B` dùng task ID FULL duy nhất. G06–G15 cũng chỉ một nhiệm vụ mỗi giai đoạn trong gói Production First (các chunk nội bộ được xử lý trong executor). Một task cần có output contract `stage_outputs`, không có việc hết batch là tạo thêm phê duyệt. Không tự cập nhật work package nếu `allowed_stages`, source SHA, nguồn, thiết bị hay write roots đổi.


**Tích hợp điều khiển trên máy:** Nếu ChatGPT chỉ có một terminal Remote Desktop, dùng `tools/project_flow_cli_v1325.py` (`init`, `next`, `record`, `resume`, `review`) làm cầu nối kiểm soát trạng thái. Ví dụ sau khi duyệt, host lưu `approved_plan.json` và state đã xác thực vào JOB_DIR đã duyệt; chạy `python tools/project_flow_cli_v1325.py init --plan <APPROVED_PLAN.json> --approved-state <AUTHENTICATED_RUNNING_STATE.json>`, rồi gọi `next`, thực thi đúng task bằng công cụ thật, ghi JSON result vào JOB_DIR, gọi `record --result <RESULT.json>`; lặp lại đến `WAITING_USER`, `PACKAGE_DONE` hoặc `FINAL_REVIEW`. **CLI không thực thi tác vụ thay ChatGPT**; công cụ remote vẫn do ChatGPT lựa chọn và gọi theo quyền. Có thể dùng `run_until_hinge(plan,state,executor)` để chạy nhiều bước trong một lượt nếu host tích hợp executor callback thật. Mọi `FILE_ACCEPTED`/audio/MP4/thumbnail phải là kết quả công cụ, không tự viết cờ TRUE.

**Tái dùng kết quả gói trước:** `merge_verified_completions(plan,state,previous,expected_inputs=...)` chỉ nhập stage DONE khi có old package ID, approval_ref thật, source hash, input hashes hiện tại và bytes output khớp; không tự import Qxx PASS hoặc state `NOT_VERIFIED` cũ. Không cần lặp lại stage chỉ vì sang package. `PACKAGE_DONE` cho gói chưa chứa G15 **không** đồng nghĩa nghiệm thu thành phẩm; chỉ gói G15 mới có `FINAL_REVIEW`. Dữ liệu tiếp tục/handoff được kiểm lại trước mỗi lần chạy và phải giữ đúng scope.

## 3. Quy tắc dừng còn cần, không phải QC

- **An toàn/quyền:** phạm vi write/read, nguồn phim/logo read-only, work_package.lock, xác minh source SHA/plan hash/approval của người dùng thật, công cụ/model và ngân sách, cài mới/driver/OS/network/scope, ghi đè output đã chấp nhận, đăng YouTube, công khai dữ liệu, xóa bất cứ file nào (đặc biệt `G15_DELETE`) luôn cần quyền riêng khi chưa có trong gói. Không tự mở gói quyền vô hạn chỉ để chạy một mạch.
- **Ủy quyền sáng tạo một lần:** với gói PRODUCTION_FIRST, đề nghị người dùng ủy quyền rõ các quyết định `G05_SCRIPT`, `G07_VOICE`, `G10_PILOT`, `G11A_METADATA`, `G11B_THUMBNAIL` qua `creative_delegations` (đã nằm trong plan hash được user duyệt). **Không tự giả chữ ký/phê duyệt từng gate**; thay vào đó runner bỏ qua câu hỏi duyệt trung gian khi ủy quyền cụ thể tồn tại. Nếu chưa ủy quyền, dừng `WAITING_USER` đúng gate. Sản xuất và bàn giao không đồng nghĩa tự đăng video.
- **G11B vẫn có thao tác thủ công:** ChatGPT tạo thumbnail như trước, cho user tải và chép vào đích `JOB_DIR/assets/youtube_thumbnail.png|jpg|jpeg` trên device được duyệt. `manual_thumbnail_handoff_v1324.verify_drop(...,production_first=True)` chỉ xác minh **bytes, file format, 16:9, SHA256, title binding và xác nhận chép ảnh thật của người dùng**, không mở QC thẩm mỹ; không giả đã upload tự động. Khi ảnh chưa được chép, ghi `WAITING_USER` lý do `USER_IMAGE_PLACEMENT` và trả duy nhất đường dẫn cần chép. Chỉ sau file thật mới DONE G11B và qua G12; không tạo nút phê duyệt khởi chạy thứ hai.
- **G15_DELETE không được ủy quyền bằng creative_delegations.** Cần phạm vi xóa cụ thể, xác nhận con người riêng, hậu kiểm trong job. Không tự phá dữ liệu gốc.
- Nếu cần người dùng upload media/audio phục vụ **đầu vào thiết yếu** mà không có đường truyền, chỉ chờ đúng dữ liệu, không đòi gửi clip để ChatGPT nghe/xem/QC chất lượng trung gian. Không nói đã nghe/xem khi chưa thật kiểm tra.

## 4. Luồng A–Z dự kiến

`P00 → G01 nguồn phim → G02 ASR → G03 dịch → G04 bản đồ phim → G05 REVIEW hoàn chỉnh → G06 beat → G07 WAV → G08 shot map → G09 EDL → G10 pilot nếu cần → G11 MP4 full → G11A title/metadata → G11B thumbnail người dùng chép → G12 intro/logo → G13 nhạc → G14 kiểm file MP4 đã tạo → G15 bàn giao → FINAL_REVIEW → user ACCEPTED/REVISION_REQUESTED`.

- Đầu vào quan trọng phải có thật; không xem `DONE` chỉ từ prompt, thời gian đã trôi hay báo cáo JSON. `OUTPUT_EXISTS` nghĩa là file trên máy tồn tại, không rỗng, đúng root, hash kiểm được. Đối với MP4, executor phải cung cấp chứng cứ probe/đọc media **tối thiểu**; không đánh giá hay chấm nội dung.
- G09 không dựng pilot G10 lặp lại, G11 chỉ render theo dữ liệu hiện có, G12/G13 tránh reencode toàn video nếu concat/stream copy/remux an toàn; không làm giảm chất lượng xuất file bằng cách ép shortcut hỏng codec.
- Khi hạn chế lượt ChatGPT: lưu `PARTIAL`/checkpoint và đề nghị **“Tiếp tục cùng gói”**, không xin duyệt lại một kế hoạch. Chỉ được nói quá trình thực thi vẫn chạy khi remote process thật đã được khởi động và quản lý bởi công cụ được cấp quyền, không suy đoán agent tự chạy nền.

## 5. Nghiệm thu bản nâng cấp và giới hạn kiểm thử

Test cần chứng minh: full stage traversal trong scope với callback executor, không Qxx; fail khi file/hash sai; không vượt scope/lock/device/approval; STOP khi thiếu quyền, không auto xóa; checkpoint/restart skip DONE và phát hiện file bị sửa; thumbnail user copy giữ nguyên; G15 → `FINAL_REVIEW` rồi user `ACCEPTED` hoặc targeted `REVISION_REQUESTED`. Kiểm thử Python giả lập output **không** là nghiệm thu phim thật hoặc việc MCP App đã tự dispatch mọi lệnh; phải thử một bộ phim thực có log/MP4/thumbnail sau khi gói đã triển khai.

</details>
