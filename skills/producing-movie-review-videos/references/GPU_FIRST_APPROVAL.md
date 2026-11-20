# GPU_FIRST_APPROVAL — GPU-FIRST và chủ động trình nút phê duyệt

**HỢP ĐỒNG BẮT BUỘC của REVIEW_PHIM cho P00, A01–A08/O01–O03 và G01–G15.** Ưu tiên tài liệu này trước mọi hướng dẫn cũ cho phép tùy ý chọn CPU khi GPU còn có thể hoạt động. Không thay danh mục ID, không nới quyền cài đặt, không vượt `MICROTASK_ACCEPTANCE_REPAIR.md`, và **không tự động cài** hoặc tự động phê duyệt.

## 1. Mặc định chọn và chủ động xin phê duyệt GPU

- **GPU-FIRST là lựa chọn mặc định** cho từng phép xử lý có backend GPU phù hợp, có lợi ích đáng kể và có khả năng đáp ứng VRAM: ASR/inference, TTS có backend GPU thực, vision/embedding/upscale, tăng tốc xử lý video và encoder NVENC/AMF/QSV. Không tự bịa mức tăng tốc; nếu bottleneck I/O hoặc GPU không có backend thì không ép GPU.
- **Chủ động hiển thị nút phê duyệt GPU trước khi đề xuất chuyển CPU hoặc bước cài đặt/kịch bản kế tiếp** đối với GPU có tiềm năng nhưng chưa chạy được. Người dùng không phải hỏi "tại sao không GPU?". Kèm `TASK_ID`, `deviceId`, `JOB_DIR`, tác vụ, phiên bản nguồn/hash, backend/precision, dung lượng/VRAM dự kiến, rủi ro, phạm vi và QC. Nếu bản thân công việc chưa được duyệt, xin duyệt công việc GPU trước khi làm; nếu thiếu dependency GPU, chủ động trình nút duyệt kế hoạch/khắc phục GPU riêng.
- **Cấp phê duyệt mặc định** ở đây nghĩa là *mặc định ĐỀ XUẤT nút xin phê duyệt* (opt-in), **không phải tự cho phép thay đổi máy**. Gọi `GenUI.issueNewTurn` chỉ từ nút thật với nội dung duyệt cụ thể; chưa nhận phản hồi duyệt thì không chạy. Không thay đổi mặc định quyền ứng dụng thành Never ask / full access.
- Với tác vụ CPU thuần: đọc/ghi metadata, hash, kiểm chứng nội dung thủ công, dịch văn bản bởi ChatGPT, quản lý file, không có GPU implementation thực, chọn CPU/I/O thường; không phát sinh nút GPU giả.

## 2. GPU eligibility và hậu kiểm — không kiểm kê phần mềm ở P00-05

1. Ở bước P00-05 chỉ đo **chỉ đọc** CPU/RAM/GPU/VRAM/OS/đĩa; không kiểm kê `PATH`, driver/CUDA Toolkit, thư viện hệ thống, runtime hoặc model. Hardware đủ VRAM = **GPU candidate**, không phải `GPU_READY`.
2. Kế hoạch cài P00-06 và đầu mỗi Axx/Oxx/Gxx có phép tính `gpu_candidate = YES / NO / UNKNOWN`, nêu backend, precision, giới hạn VRAM, bộ thư viện/dll dự kiến, và **nút phê duyệt GPU** nếu `YES` và cần triển khai. Axx/Gxx chỉ được smoke-test GPU trong phạm vi task được duyệt; không dò/tái dùng hệ thống ngoài `JOB_DIR`.
3. Trạng thái riêng `GPU_STATUS`:
   - `GPU_READY`: backend cục bộ có đủ dependency và smoke-test GPU thực sự chạy thành công, có lệnh và log/hash; có thể đề xuất GPU làm backend chính.
   - `GPU_NEEDS_SETUP`: phần cứng phù hợp nhưng dependency/runtime GPU còn thiếu, ví dụ `cublas64_12.dll`, cuDNN hoặc build GPU. **GPU_NEEDS_SETUP → GPU_APPROVAL**: phải chủ động trình nút **Phê duyệt kế hoạch/cài runtime GPU** với `TASK_ID` riêng trước khi đưa nút Axx tiếp theo.
   - `GPU_NOT_VERIFIED`: chưa được phép thử hoặc thiếu chứng cứ; đề xuất nút duyệt kiểm chứng GPU; không nói đã sẵn sàng.
   - `GPU_UNSUPPORTED`: không có GPU phù hợp hoặc không có backend/VRAM đáp ứng dựa trên bằng chứng; giải thích, đề xuất CPU mà không bịa GPU.
4. **GPU_CANDIDATE → GPU_SMOKE → GPU_READY** là luồng bằng chứng yêu cầu cho task dùng GPU: xác minh phiên bản/backend, memory, đầu ra của dữ liệu tổng hợp; QC ghi `device`, `precision`, `gpu_supported`, `gpu_test`, hash/log, thời gian nếu đo hợp lệ. Chỉ có RTX hoặc danh sách compute types không đủ chứng nhận GPU.
5. Nếu lỗi sau CPU smoke, **CPU PASS không che giấu GPU_NEEDS_SETUP**. Tách `QC_STATUS` theo task đã duyệt và `GPU_STATUS`; giữ công việc CPU đã PASS và issue GPU chưa giải quyết. Trước nút duyệt Axx/Gxx tiếp theo phải trình **GPU_APPROVAL** với issue và kế hoạch/nguồn/bằng chứng. Đừng trình nút cài A05 trước nếu A04 GPU còn có thể khắc phục mà người dùng chưa từ chối/hoãn.

## 3. Quy tắc chuyển CPU dự phòng

- Khi `GPU_READY`, mặc định đề xuất sử dụng GPU (đã phê duyệt) làm backend chính; CPU là phương án phục hồi lỗi runtime, không làm backend chính mặc định.
- Khi `GPU_NEEDS_SETUP`/`GPU_NOT_VERIFIED`, **không tự lẳng lặng chọn CPU để hoàn tất mục tiêu GPU**. Chỉ được dùng CPU dự phòng trong phạm vi smoke test CPU đã được duyệt, hoặc sau khi người dùng chọn `CPU_FALLBACK_APPROVAL`/bỏ qua GPU rõ ràng. Mọi công việc G02/G04/G08/G11 dài trên CPU dù GPU tiềm năng phải có đề xuất GPU và quyền lựa chọn CPU rõ ràng.
- Khi `GPU_UNSUPPORTED` được chứng minh hoặc user đã từ chối GPU, trình CPU option với lý do và giới hạn thực tế, không ép người dùng duyệt GPU không dùng được. Nếu người dùng yêu cầu CPU, ưu tiên lựa chọn có chủ ý đó.
- Không được biến CPU smoke PASS thành khẳng định GPU PASS; không biến GPU chưa thử thành `GPU_UNSUPPORTED` hoặc issue GPU không chặn thành `GPU_READY`.

## 4. Phạm vi theo công cụ — GPU khi thực sự có backend

| ID / quy trình | Ưu tiên GPU nếu đủ điều kiện | Khi thiếu runtime / phải chọn CPU |
|---|---|---|
| A01, G09–G12, G14 | Đề xuất encode NVENC/AMF/QSV sau khi test encoder thực; GPU không thay FFprobe hoặc kiểm tra SHA | Xin nút duyệt kiểm tra/bổ sung backend, hoặc CPU x264 có lý do |
| A04, G02 | Faster-Whisper + CTranslate2 CUDA; NVIDIA phù hợp đề xuất `int8_float16` batch 1 làm điểm xuất phát | Thiếu `cublas64_12.dll`/cuDNN: `GPU_NEEDS_SETUP`, chủ động xin duyệt kế hoạch hoặc runtime trong `JOB_DIR` trước A05; CPU INT8 là dự phòng |
| A05, G07 | VieNeu-TTS chọn backend GPU nếu phiên bản/model hỗ trợ thật; không suy diễn ONNX CPU = GPU | Khóa voice/model theo phê duyệt riêng; nếu chỉ có CPU runtime thì ghi rõ và đề xuất backend GPU khả thi |
| O01/O02, G04/G08 | Vision/CLIP embeddings GPU khi model/VRAM cho phép; điều chỉnh quant/batch, có test | Không chạy model GPU chỉ vì được khuyến nghị mà chưa được duyệt Oxx |
| O03, G11 | GPU upscaler nếu model và VRAM phù hợp, test tiled inference | Nếu memory không đủ đề xuất tiles nhỏ hoặc xin duyệt CPU có lý do |
| A02/A03/A06/A07/A08, G03/G05 và tác vụ I/O thuần | Chỉ đề xuất GPU cho thành phần thực có backend hoặc render được GPU gia tốc | Không đề xuất GPU vô nghĩa cho metadata, pip, dịch ChatGPT, QC hash |

## 5. Hợp đồng phê duyệt, cô lập và QC

- Mọi nút `GPU_APPROVAL` phải chỉ rõ `TASK_ID`, `deviceId`, `JOB_DIR`, `GPU_STATUS` đầu vào, runtime/phụ thuộc, phiên bản cố định, nguồn chính thức, SHA-256, nơi cài, dung lượng, tác động, smoke test và `acceptance_criteria` 2–6 tiêu chí. Đề xuất **một hành động xin phê duyệt rõ ràng**, không hứa auto cài, không phê duyệt thay người dùng.
- Nếu muốn nghiên cứu nhưng chưa đủ nguồn/version/hash, trước tiên đề xuất **Phê duyệt P00-06.<ID>.GPU.PLAN** chỉ lập kế hoạch không ghi file. Sau kế hoạch `PASS`, trình **Phê duyệt P00-06.<ID>.GPU.RUNTIME** riêng để tải/cài. Các tên ID minh họa; dùng ID thực và không gộp các việc chưa duyệt.
- Phê duyệt cài A04 không mặc nhiên cho phép sửa/cài cuBLAS/cuDNN, driver hoặc đổi CUDA/PATH. Có quyền cài GPU theo task riêng thì phải kiểm sha-256, vị trí, xung đột, hỗ trợ ABI, lưu hồ sơ và QC. **Không tự** dò/copy runtime ngoài workspace, không sử dụng hardlink hoặc sửa driver/registry/**PATH hệ thống**, không ghi đè file cũ; nếu chỉ chạy được bằng cách sửa hệ điều hành, báo `BLOCKED` và xin **quyền riêng**.
- QC báo `QC_STATUS` của task và `GPU_STATUS` tách biệt: `cpu_smoke`, `gpu_smoke`, `gpu_backend`, `gpu_memory`, `fallback_reason`, log/hash và issue. `GPU_NEEDS_SETUP` phải có `issue_id`, `next_action=GPU_APPROVAL` trước nhiệm vụ kế nếu khả thi. Tôn trọng `MICROTASK_ACCEPTANCE_REPAIR.md`: task kỹ thuật `PASS` không tự cấp quyền thực hiện task mới; GPU lỗi có thể là gate riêng chưa đạt, không sửa giả QC cũ.

## 6. Ví dụ kiểm tra bắt buộc (RTX 4060, A04)

Đã cài Faster-Whisper 1.2.1 + CTranslate2 4.9.0 và CPU INT8 transcribe thành công, nhưng GPU test báo `Library cublas64_12.dll is not found or cannot be loaded`. Kết luận đúng: `QC_STATUS=PASS` cho phần sửa PyAV nếu đủ tiêu chí, **`GPU_STATUS=GPU_NEEDS_SETUP`**, `gpu_smoke=FAIL`, GPU **chưa sẵn sàng**. Hành động kế **mặc định** là nút **Phê duyệt P00-06.A04.GPU.PLAN** (xác minh cuBLAS/cuDNN tương thích, checksum, runtime riêng trong JOB_DIR) thay vì nút A05. Chỉ sau phê duyệt kế hoạch, triển khai runtime GPU bằng phê duyệt riêng rồi smoke test CUDA. Không tự cài GPU runtime, không chạy G01–G15.
