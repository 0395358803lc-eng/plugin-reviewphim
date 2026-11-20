# HARDWARE_PROFILE — P00-5: Phần cứng và bộ cài REVIEW_PHIM_WORKSPACE cũ

## Mục tiêu

Sau chọn đúng máy/deviceId → phim → scaffold rỗng nếu duyệt → logo/không logo, chạy **kiểm tra phần cứng máy chủ và kiểm kê workspace cũ ở chế độ chỉ đọc**. Quy tắc ưu tiên [WORKSPACE_REUSE_POLICY](WORKSPACE_REUSE_POLICY.md). Không thay thế đo phần cứng bằng inventory; cả hai là hai nhánh đầu việc P00-5, đều phải có phê duyệt phù hợp. Không tự cài, không chạy G01.

## Nhánh A: đo phần cứng CHỈ ĐỌC

| Trường | Dữ liệu bắt buộc | Ứng dụng |
|---|---|---|
| CPU | model/hãng, nhân vật lý, luồng, kiến trúc/ISA nếu đo được | ABI, số workers/threads |
| RAM | tổng và khả dụng | batch/concurrency |
| GPU/VRAM | từng GPU, model/VRAM, điều kiện compute nếu xác minh được | CPU/GPU backend, precision |
| Windows | phiên bản và arch | đúng binary portable |
| Storage/disk | tổng/trống GB trên ổ JOB_DIR, quyền ghi/path an toàn | hạn mức cache/render/cài mới |
| UNKNOWN | các trường chưa có căn cứ | bắt buộc ghi rõ, không đoán |

Dùng truy vấn chỉ đọc Windows như `Get-CimInstance Win32_Processor`, `Win32_ComputerSystem`, `Win32_OperatingSystem`, `Win32_VideoController`, `Get-Volume`. Với NVIDIA được gọi `nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits` **chỉ để đọc phần cứng**. `Win32_VideoController.AdapterRAM` có thể bị cắt ở 4 GiB nên phải xác minh độc lập khi nghi sai. Không benchmark/inference để đo hardware chưa được duyệt. Lưu `JOB_DIR/logs/hardware_profile.json` chỉ khi được phê duyệt ghi; nếu không, báo trong chat.

## Nhánh B: kiểm kê phần mềm/model đã có CHỈ TRONG WORKSPACE CŨ

- Từ các gốc `REVIEW_PHIM_WORKSPACE` đã duyệt trên **cùng deviceId**, xem `tools/`, `.venv/`, `models/`, lockfiles và package/model manifests trong các thư mục con dự án trước. Không quét toàn máy, `Program Files`, registry, global PATH, Python/Node hệ thống hay cache global.
- Đọc thư mục, tên file, version/lockfile được ghi, SHA-256 và canonical path; kiểm junction/symlink trước khi đi vào. Không chạy `ffmpeg -version`, `python --version`, `pip list`, `npm -v`, import/inference hoặc encode trong bước khám phá chưa có phê duyệt smoke test riêng.
- Bảng đủ **11 ID A01–A08/O01–O03** gồm: nơi cũ, version/hash, điều kiện CPU/GPU/ABI, khả năng ghi tách khỏi nguồn, trạng thái `REUSE_READY` / `FOUND_NOT_VERIFIED` / `INCOMPATIBLE` / `MISSING` / `BLOCKED`, bằng chứng và việc cần duyệt. Không lấy sự có mặt file làm `REUSE_READY`.
- Khi người dùng cho phép kiểm chứng ứng viên, chạy một smoke test nhỏ trong phạm vi đã duyệt; binary ở workspace cũ chỉ đọc, `cwd` và toàn bộ writable caches/profiles/tmp/output ở JOB_DIR mới. Chỉ khi PASS và tương thích mới đề nghị dùng lại; quyền **dùng lại** cho job mới vẫn phải được duyệt riêng.

## Tối ưu từng ID, không thay danh mục

- A01: FFmpeg/FFprobe portable, codec và encoder CPU; NVENC/AMF/QSV chỉ là khả năng, không tự khẳng định chạy.
- A02/A03/A08: Python/NumPy/Pillow/OpenCV/PySceneDetect, OS/arch/ABI/venv, số threads. Không trộn package, không relocate venv cũ.
- A04: Faster-Whisper/CTranslate2/Whisper Large V3 Turbo; CPU INT8 hay CUDA FP16/INT8 theo phần cứng và smoke test. CPU smoke PASS không chứng minh GPU_READY.
- A05: VieNeu-TTS, voice pack đã được duyệt, backend và batch RAM/VRAM.
- A06/A07: Node/React/Remotion/Chromium, dependency lock, kiến trúc, rendering workers/profile dir.
- O01 Qwen-VL, O02 CLIP, O03 upscale: model_id/revision/quantization/SHA-256/backend, VRAM, quyền sử dụng; optional vẫn optional.

Với VRAM chưa biết, không đoán GPU_READY; GPU dưới ~6 GB phải rất thận trọng với model lớn, từ ~8 GB có thể khảo sát ASR GPU hoặc vision nhỏ nhưng chỉ hậu kiểm mới kết luận. RAM dưới 16 GB giảm concurrency; 32 GB trở lên có thể cân nhắc chạy song song, không phải bảo đảm.

## Báo cáo và quyền

Thứ tự: (1) hardware `[deviceId | CPU | cores/threads | RAM | GPU/VRAM | Windows | disk | UNKNOWN]`; (2) khả năng CPU/GPU; (3) workspace cũ đã được phép khám phá và rủi ro; (4) bảng đủ 11 ID với trạng thái và tối ưu; (5) **nút duyệt kiểm chứng/dùng lại/cài mới** theo `WORKSPACE_REUSE_POLICY.md`. `REUSE_READY` chỉ được gán sau chứng cứ phù hợp, và vẫn cần duyệt dùng lại. Không có root cũ không có nghĩa phần cứng có lỗi: ghi MISSING, dự toán cài mới. Mỗi P00 task có QC theo `MICROTASK_ACCEPTANCE_REPAIR.md`, dừng trước G01.
