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

# WORKSPACE_REUSE_POLICY — P00-5: Kiểm kê và tái sử dụng có kiểm chứng

**Hiệu lực:** áp dụng ngay từ P00-5, ưu tiên cao hơn mọi câu trước đây trong `HARDWARE_PROFILE.md`, `INSTALLATION_CATALOG.md`, `SESSION_ORCHESTRATION.md`, `WORKSPACE_BOOTSTRAP.md`, `WORKFLOW.md`, `DEFAULTS_AND_TOOLS.md` hoặc `SKILL.md` nói rằng phải cài mới từng `JOB_DIR`, tuyệt đối không kiểm kê hoặc cấm tái dùng ngoài `JOB_DIR`. Chỉ thay đổi nguồn **đọc/thực thi** runtime đã duyệt; không thay giới hạn **ghi** vào JOB_DIR, danh mục 11 ID hay quy trình phê duyệt.

## Mục tiêu

Ngay trong nhiệm vụ kiểm tra phần cứng P00-5, thực hiện thêm **P00-5.REUSE_DISCOVERY** ở chế độ chỉ đọc để tìm bộ cài đã tồn tại trong `REVIEW_PHIM_WORKSPACE` của **các phim/dự án trước trên chính máy `deviceId` đang được chọn**. Không cài lại ID đã kiểm chứng tương thích và được người dùng duyệt cho phép tái sử dụng. Không xem thư mục tồn tại là bằng chứng runtime hoạt động.

## Ranh giới tìm kiếm, quyền và ưu tiên

1. Chỉ tìm ở `FILM_DIR/REVIEW_PHIM_WORKSPACE` hiện tại và các **đường dẫn gốc `REVIEW_PHIM_WORKSPACE` đã được người dùng chỉ định hoặc đã xác thực trong cùng máy/deviceId**, ví dụ `D:\phim-3\REVIEW_PHIM_WORKSPACE\fatman-2020`. Không quét cả ổ, không dò `Program Files`, PATH, registry, pip/npm global, model hệ thống hoặc mọi ổ/máy chủ khác. Nếu chưa biết workspace cũ, liệt kê thư mục anh em trong cùng root hiện tại; hỏi quyền chọn root cũ khác thay vì đoán.
2. P00-5 phải được duyệt trước; giới hạn duyệt ghi rõ các root được phép **đọc**. Thao tác ban đầu chỉ đọc metadata, file manifest/lock, thông tin kích thước, hash và symlink/junction; không chạy executable/inference/benchmark. Chạy lệnh `--version`, import, inference, encode hay smoke test phải có **phê duyệt kiểm chứng riêng** sau khi đã trình danh sách ứng viên và rủi ro, chỉ chạy đúng binary tuyệt đối trong workspace cũ và output/cache ở JOB_DIR mới.
3. Không theo junction/symlink/reparse point ra khỏi root đã duyệt; canonical path và NTFS identity phải hợp lệ. Không tái dùng nếu đường dẫn không còn tồn tại, không đọc được, có nguy cơ bị thay đổi hoặc không xác nhận được chủ sở hữu. Không hardlink/symlink/copy tự động, không di chuyển hoặc sửa file trong workspace cũ.
4. Ưu tiên (a) runtime tương thích đã được người dùng phê duyệt tại workspace hiện tại; (b) ứng viên tương thích, đọc được, đã được kiểm chứng trong workspace cũ **cùng máy**; (c) trình kế hoạch **cài mới riêng cho ID thiếu/lỗi/không tương thích** sau khi duyệt. Nếu nhiều ứng viên tương đương, ưu tiên bản có manifest/hashes và QC gần nhất, ghi lý do chọn; không tự nâng phiên bản.

## Kiểm chứng cho từng ID A01–A08 / O01–O03

- A01: đường dẫn tuyệt đối FFmpeg/FFprobe, version/build, codec/capabilities và hash binaries; hậu kiểm thao tác mẫu sau phê duyệt.
- A02/A03/A08: Python/venv/site-packages và ABI, kiến trúc, interpreter location, lockfile/wheels, NumPy/Pillow/OpenCV/PySceneDetect/QC; **venv có đường dẫn tuyệt đối hoặc lệ thuộc workspace cũ** chỉ được gọi tại chỗ (không copy/relocate), và chỉ khi toàn bộ ghi tạm/cache được chuyển về JOB_DIR mới. Không trộn package từ hai venv.
- A04: Faster-Whisper/CTranslate2/VAD, model Large V3 Turbo, model revision, SHA-256, CPU/GPU backend và CUDA/cuDNN nếu áp dụng. CPU smoke PASS không chứng minh GPU_READY.
- A05: VieNeu-TTS engine, model/voice pack, phiên bản, hash, điều kiện cấp phép, backend và giọng do người dùng duyệt; không tự chọn giọng mới.
- A06/A07: Node/npm, React/Remotion/Chromium với lockfile, ABI, phiên bản renderer, runtime/browser paths, hashes; chỉ dùng node_modules cũ tại chỗ nếu dependency và đường dẫn tương thích; profile/browser cache xuất vào JOB_DIR mới.
- O01/O02/O03: nếu đã được duyệt cho job mới, đối chiếu model_id, revision, SHA-256, quantization, backend, VRAM và dependencies; optional không tự trở thành bắt buộc.
- Tất cả: xác nhận cùng máy/OS/arch, khả năng chạy trên CPU/RAM/GPU/VRAM đo được, đủ quyền đọc/thực thi, tình trạng file và cả điều kiện license/approval nếu có. Hash hoặc model metadata không có thì `CẦN KIỂM CHỨNG`, **không tự đánh dấu ĐÃ CÓ DÙNG ĐƯỢC**.

## Ghi dữ liệu và cấu hình chạy

- **JOB_DIR mới là điểm ghi duy nhất**: toàn bộ transcript, frame, render, temp, logs, các cache mới, model download mới, pip/npm caches, Chromium profiles, HF_HOME, HUGGINGFACE_HUB_CACHE, XDG_CACHE_HOME, TORCH_HOME, PIP_CACHE_DIR, PYTHONPYCACHEPREFIX, npm_config_cache, COREPACK_HOME, PLAYWRIGHT_BROWSERS_PATH, TEMP/TMP đều nằm trong JOB_DIR mới.
- Gọi binary/model qua **đường dẫn tuyệt đối** trong `REUSE_SOURCE` cũ ở chế độ read-only; `cwd=JOB_DIR` mới; không đổi PATH hệ thống hoặc môi trường global. Tắt/redirect pycache (`PYTHONDONTWRITEBYTECODE=1`) và mọi ghi phát sinh; nếu tool bắt buộc ghi vào workspace cũ thì từ chối reuse ID đó và đề nghị cài mới có duyệt.
- Nếu runtime cũ cần thay đổi, update, tải model, xóa cache, migrate DB hoặc sửa cấu hình, **không được thực hiện trên workspace cũ**. Đề nghị cài bản cô lập trong JOB_DIR mới và xin phê duyệt riêng.
- Không chia sẻ output, checkpoint, transcript, cảnh phim hay log job cũ; chỉ tái sử dụng runtime/tool/library/model, tuyệt đối không dùng lại kết quả dự án khác như thể đã nghiệm thu.

## Trạng thái kết quả và hành động

| Trạng thái | Điều kiện | Quyết định |
|---|---|---|
| `REUSE_READY` | Có root hợp lệ, đủ manifest/hash/ABI/backend/approval và **smoke test riêng PASS** khi cần | Đề xuất **Phê duyệt dùng lại ID**; sau duyệt không cài ID này |
| `FOUND_NOT_VERIFIED` | Có ứng viên nhưng thiếu bằng chứng hoặc chưa được duyệt smoke test | Trình **Phê duyệt kiểm chứng ID**, không dùng/chưa cài |
| `INCOMPATIBLE` | Sai phiên bản/ABI/OS/GPU/backend, không thể bảo đảm cô lập ghi hoặc smoke test FAIL | Không reuse; trình phương án cài mới/sửa theo phê duyệt |
| `MISSING` | Không tìm thấy trong các root được phép | Trình phương án cài mới theo phê duyệt |
| `BLOCKED` | Không truy cập được hoặc quyền/path không an toàn | Nêu blocker, không tự quét nơi khác |

`REUSE_READY` là trạng thái ứng viên được nghiệm thu về mặt kỹ thuật; **chưa tự cấp quyền sử dụng cho job mới**. Khi người dùng duyệt `P00-06.REUSE.<ID>`, ghi map nguồn tại `JOB_DIR/logs/runtime_reuse_manifest.json` hoặc báo trong chat khi đang chỉ đọc. Map tối thiểu: `schema_version`, `device_id`, `job_dir`, `catalog_id`, `source_workspace`, `canonical_binary_or_model_path`, `version`, `hashes`, `abi`, `backend`, `compatibility_evidence`, `smoke_qc_ref`, `approval_ref`, `status`, `timestamp`. Không ghi vào root cũ. Mọi thay đổi map phải được phê duyệt/ghi phiên bản mới, không âm thầm chuyển binary.

## Báo cáo P00 bắt buộc

Sau hardware profile, bảng đủ **11 ID** `ID | công cụ/model | vị trí workspace cũ | phiên bản/hash | CPU/GPU/ABI phù hợp | trạng thái | bằng chứng/smoke | đề xuất: reuse/verify/install | dung lượng tiết kiệm ước tính`. Phân biệt rõ **tồn tại file**, **đã kiểm chứng** và **đã được duyệt**; nếu chưa đo dung lượng thì ghi UNKNOWN. Trình nút phê duyệt tái dùng và cài mới theo từng ID/nhóm đã liệt kê; không bỏ hàng tùy chọn. QC P00-5 ghi PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED theo `MICROTASK_ACCEPTANCE_REPAIR.md`, và không chạy G01 dù đã tái sử dụng thành công.

## Kịch bản kiểm thử bắt buộc

1. Cùng máy, FFmpeg hash/codec PASS → reuse khi được duyệt, không cài lại.
2. Có Python venv nhưng ABI khác/đường dẫn hard-code → INCOMPATIBLE, không dùng lẫn.
3. Có model Whisper nhưng thiếu revision/hash → FOUND_NOT_VERIFIED, không đánh dấu sẵn sàng.
4. GPU RTX và CPU smoke PASS nhưng CUDA/cuDNN lỗi → không gắn GPU_READY, đề xuất GPU approval/fallback đúng quy tắc.
5. Workspace cũ là junction trỏ ngoài root → BLOCKED; không theo link.
6. Runtime cố ghi log/cache vào workspace cũ → INCOMPATIBLE và phải cài mới có duyệt.
7. Nhiều workspace ứng viên → chọn bằng bằng chứng, không tự lấy bản mới nhất mơ hồ.
8. Không có workspace cũ → MISSING, trình cài mới, không quét PATH toàn hệ thống.
9. Cùng root có phim cũ nhưng transcript/output cũ → không dùng dữ liệu phim cũ làm sản phẩm mới.

</details>
