# INSTALLATION_CATALOG — 11 ID bất biến, tái sử dụng có kiểm chứng trước khi cài

**Hợp đồng mới:** Danh mục A01–A08/O01–O03 là danh sách thành phần cần có cho quy trình, **không còn có nghĩa phải cài lại từ đầu mỗi `JOB_DIR`**. Sau P00-5, đối chiếu 11 ID với workspace cũ được phép theo `WORKSPACE_REUSE_POLICY.md`. Mọi câu cũ bắt buộc cài mới hoặc cấm khảo sát runtime trong workspace cũ đều bị thay thế; cấm kiểm tra và dùng package ngoài phạm vi root đã duyệt. Không xóa hay thay mã ID khi phát hiện bộ cài hợp lệ.

## Danh mục không thay ID/tên/phạm vi

| ID | Thành phần cần cài/dùng lại | Chức năng | Nơi cài mới nếu cần trong JOB_DIR | Phạm vi |
|---|---|---|---|---|
| A01 | FFmpeg + FFprobe portable | Probe/audio/frame/clip/render/QC | `tools/ffmpeg/` | Bắt buộc |
| A02 | Python portable/embedded, pip, venv và dependency lock | Runtime xử lý phim | `tools/python/`, `.venv/`, `cache/pip/` | Bắt buộc |
| A03 | NumPy, Pillow, OpenCV headless, PySceneDetect | Phân tích cảnh/ảnh | `.venv/` | Bắt buộc |
| A04 | Faster-Whisper, CTranslate2, VAD, Whisper Large V3 Turbo | ASR transcript gốc | `.venv/`, `models/asr/`, `cache/` | Bắt buộc |
| A05 | VieNeu-TTS v3 Turbo, model/voice pack đã duyệt | Thuyết minh WAV | `.venv/`, `models/tts/`, `voice/` | Engine bắt buộc, voice theo duyệt |
| A06 | Node.js portable/npm/React/Remotion phiên bản khóa | Timeline và render video | `tools/node/`, `tools/remotion/`, `npm-cache/`, `tools/remotion/node_modules/` | Bắt buộc |
| A07 | Chromium/browser runtime | Render nếu thiết kế cần | `tools/browser/` hoặc `cache/browser/` | Có điều kiện |
| A08 | FFmpeg/Python contact sheet, frame, hash và QC helpers | Trích chứng cứ | `tools/`, `.venv/` | Bắt buộc |
| O01 | Qwen-VL local và inference dependencies | Gợi ý shot/subject | `models/vision/`, `.venv/` | Tùy chọn; duyệt riêng |
| O02 | Embedding/CLIP và index tìm cảnh | Truy hồi ứng viên cảnh | `models/embeddings/`, `.venv/`, `analysis/` | Tùy chọn; duyệt riêng |
| O03 | Upscale/denoise/model | Tăng chất lượng video G11 | `tools/upscale/`, `models/upscale/` | Tùy chọn; duyệt riêng |

`Remote Desktop Commander`, khả năng ChatGPT đọc ảnh, OS GPU driver và MSVC hệ thống **không phải gói cài trong JOB_DIR**. Không tự sửa driver, PATH, registry, firewall hoặc OS. Không được tự dùng `latest`, tải/cài từ skill bên ngoài danh mục hoặc thay model/ngôn ngữ.

## Khám phá → kiểm chứng → lựa chọn

1. P00-5 đọc CPU/RAM/GPU/VRAM/OS/ổ trống và inventory **chỉ tại REVIEW_PHIM_WORKSPACE cũ có root được duyệt**. Không dùng `where`, `Get-Command`, pip/npm global caches hoặc PATH để phát hiện phần mềm toàn máy. Không cài, chạy binary hay model chỉ vì thấy file.
2. Với mỗi ID, xác minh canonical path, lockfile/revision/hash, OS/architecture/ABI, GPU backend/precision, quyền truy cập và khả năng redirect **toàn bộ ghi** sang JOB_DIR mới. Riêng Python venv/Node dependencies có thể phụ thuộc absolute paths và không thể chuyển chỗ. Kết quả `REUSE_READY`, `FOUND_NOT_VERIFIED`, `INCOMPATIBLE`, `MISSING`, `BLOCKED` theo `WORKSPACE_REUSE_POLICY.md`.
3. Smoke test runtime cũ chỉ sau phê duyệt kiểm chứng. Kết quả test thuộc workspace mới (`JOB_DIR/qc/` hoặc chat khi chỉ đọc). Một CPU smoke không chứng minh backend GPU.
4. Từng ID `REUSE_READY`: trình nút **Phê duyệt dùng lại Axx/Oxx**. Sau duyệt gọi đường dẫn tuyệt đối cũ tại chỗ, **không cài lại**. `FOUND_NOT_VERIFIED`: trình kiểm chứng. `MISSING`/`INCOMPATIBLE`: đưa vào kế hoạch **cài mới chọn lọc**. `BLOCKED`: báo blocker. Không tự fallback dùng bản hệ thống hoặc cài mới chưa được duyệt.
5. Với O01/O02 chỉ chốt `model_id`, `revision`, `SHA-256`, `quantization`, `backend`, `VRAM` khi có căn cứ theo `MODEL_ROLE_POLICY.md`; không tự nâng một model tương tự thành bản đã duyệt.

## Trình phê duyệt trước cài

Bảng phải bao phủ đủ 11 ID: `ID | tên/phiên bản | source_workspace hoặc target JOB_DIR | version/hash | trạng thái | build/ABI/backend/batch/threads | cần mạng? | dung lượng tải/cài mới dự trù | smoke QC | đề xuất reuse/verify/install | phê duyệt`. Nêu nguồn chính thức, checksum/size khi xác minh được; chưa xác minh ghi UNKNOWN. Với ID reuse PASS **không tính vào ngân sách download/cài lại**. Nếu tất cả bắt buộc reuse và được duyệt, ngân sách tải mới có thể bằng 0; không khẳng định trước khi kiểm chứng.

**Chưa duyệt thì chỉ được trình kế hoạch**; không tải/cài hoặc tự chạy các giai đoạn. Cài lại chỉ đúng ID cần thiết đã được duyệt. Phê duyệt cài **không** là phê duyệt G01.

## Sau duyệt cài/tái sử dụng

- `cwd=JOB_DIR` mới; nếu reuse, dùng executable/model **đường dẫn tuyệt đối** ở `REUSE_SOURCE` cũ với quyền chỉ đọc, tuyệt đối không sửa/cập nhật nguồn; nếu cài mới, đích ghi trong JOB_DIR.
- `TEMP`, `TMP`, `TMPDIR`, `HF_HOME`, `HUGGINGFACE_HUB_CACHE`, `XDG_CACHE_HOME`, `TORCH_HOME`, `PIP_CACHE_DIR`, `PYTHONPYCACHEPREFIX`, `npm_config_cache`, `COREPACK_HOME`, `PLAYWRIGHT_BROWSERS_PATH` và browser profile đều về JOB_DIR mới. Không `pip install --user`, `npm -g`, `npx` auto-download hoặc thay PATH hệ thống. Nếu runtime ghi vào workspace cũ thì **không cho reuse**.
- Lưu mapping `JOB_DIR/logs/runtime_reuse_manifest.json` có deviceId, ID, path, hashes, version, QC, approval và backend; lưu log/QC từng ID, không ghi đè lịch sử. Sau test báo `REUSED_AND_TESTED`/`INSTALLED_AND_TESTED`/`NEEDS_FIX`/`NOT_VERIFIED`/`BLOCKED`; dừng trước G01.
