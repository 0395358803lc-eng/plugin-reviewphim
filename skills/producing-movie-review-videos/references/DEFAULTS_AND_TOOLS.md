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

# DEFAULTS_AND_TOOLS — Preset, công cụ và bộ cài độc lập

**Ưu tiên `SKILL.md`, `SESSION_ORCHESTRATION.md`, `HARDWARE_PROFILE.md`, `INSTALLATION_CATALOG.md`.** Không mặc định máy, thư mục, phim, logo, thời lượng hay giọng, không mặc định ổ D: hoặc C:. Hỏi `FILM_DIR`, chọn `SOURCE_MOVIE`, `JOB_DIR=FILM_DIR\REVIEW_PHIM_WORKSPACE\<project-id>`; phim/logo gốc chỉ đọc.

| Thành phần | Preset/giới hạn | Khi thay đổi |
|---|---|---|
| Máy | Chọn từ `list_devices`, xác minh deviceId | Nếu user đã chọn thì không hỏi lại |
| Phim | Chọn thư mục và tệp chính xác | Không tự suy diễn |
| Logo | Hỏi logo PNG được chọn hoặc không logo | Không mặc định TUA PHIM CÓ GU |
| Giọng đọc | Trúc Ly 1.00x chỉ là tham khảo, VieNeu-TTS v3 Turbo | Cần user duyệt giọng |
| REVIEW | Kể chuyện tự nhiên, có căn cứ, không bịa | Tone tùy thể loại |
| Thời lượng | **Không mặc định thời lượng**, theo REVIEW/WAV | User quyết định |
| Hình ảnh | 16:9/1080p nếu phù hợp nguồn | Upscale không thành native |
| FPS | Theo nguồn/timeline, không ép 24 | Theo duyệt |
| Intro | Đề xuất 2 giây | Có thể bỏ/đổi |
| Nhạc | Không lời, crossfade, sidechain ducking | Không lấn át giọng |
| Đầu ra | MP4 H.264/AAC, báo cáo, gói nguồn | Tất cả trong JOB_DIR |

## Công cụ bắt buộc trình cài, không kiểm kê máy

**Luồng mới:** kiểm tra phần cứng CPU/RAM/GPU/VRAM/OS/disk chỉ đọc theo `HARDWARE_PROFILE.md` → in nguyên danh sách ID A01–A08 và O01–O03 trong `INSTALLATION_CATALOG.md` → xin duyệt phần bắt buộc và lựa chọn tùy chọn → cài mới vào JOB_DIR → hậu kiểm đúng runtime nội bộ → trình G01. **Không có bước hỏi hoặc rà phần mềm, thư viện, model nào đã cài trên máy. Không tái sử dụng FFmpeg, FFprobe, Python, venv, Faster-Whisper, PySceneDetect, OpenCV, Pillow, TTS, Node, Remotion, model/cache trên máy hay PATH ngoài JOB_DIR.** Kể cả máy khác có đủ gói, danh sách cài đặt vẫn y hệt; chỉ build/CPU-GPU backend/threads/batch/render và mức khuyến nghị Oxx được tối ưu theo phần cứng mỗi máy.

- `Remote Desktop Commander` là kênh điều phối máy từ xa; ChatGPT đọc trực tiếp ảnh/contact sheet/video thật khi công cụ cho phép, không đồng nhất metadata và đã xem hình. Đây không phải bộ cài trên máy.
- FFmpeg/FFprobe hỗ trợ probe, trích frames/clip, render, decode/QC; PySceneDetect/OpenCV/Pillow/NumPy hỗ trợ cảnh/contact sheet; Faster-Whisper/CTranslate2 phục vụ ASR; VieNeu-TTS tạo giọng; Node/Remotion dựng video.
- Vision local như Qwen-VL, CLIP/embedding là gói tùy chọn phải được duyệt ID riêng; ChatGPT vẫn chịu trách nhiệm xem/chọn cảnh, không để model tự quyết câu chuyện.
- Bộ cài nằm `tools/`, `.venv/`, `models/`, `cache/`, `npm-cache/`, `tools/remotion/node_modules/`; không có global install. Nếu gói không thể chạy trong JOB_DIR vì hệ thống, báo BLOCKED, xin giải pháp; không dùng gói có sẵn để thay.

## Cache và hậu kiểm theo JOB_DIR

`cwd=JOB_DIR`. Đặt biến theo process `TEMP`, `TMP`, `TMPDIR`, `HF_HOME`, `HUGGINGFACE_HUB_CACHE`, `XDG_CACHE_HOME`, `TORCH_HOME`, `PIP_CACHE_DIR`, `PYTHONPYCACHEPREFIX`, `npm_config_cache`, `COREPACK_HOME`, `PLAYWRIGHT_BROWSERS_PATH` trỏ vào JOB_DIR. Không sửa PATH toàn hệ thống, registry, firewall, driver; OS có thể sinh log bên ngoài do chính OS. Chưa có phê duyệt thì không chạy pip/npm/npx/tải model.

**Hậu kiểm chỉ sau cài**: xác minh đường dẫn nội bộ và smoke tests có chứng cứ. GPU/CPU test khi cần để chọn backend chạy, không phục vụ tiền kiểm/cắt giảm bộ cài.

## G04/G08/G11/QC

G04 chỉ tạo `analysis/frames/`, `analysis/contact_sheets/`, `analysis/motion_checks/` sau phê duyệt; cần `FILM_UNDERSTANDING_READY` trước đề xuất G05. G08 đối chiếu clip/actor/action/emotion không chỉ dựa scene timecode; không lấy sai tuyến. G11 `hflip=false`, không mặc định 2,04s/shot, zoom 8%, crop, LUT hay 24 fps. Hình đã upscale không gọi là native. G14 không tuyên bố 100% khi chưa xem–nghe liên tục.

Không ghi đè, không xóa trừ path được phê duyệt riêng, không lấy Traffic/UNABOMBER làm mặc định. Giữ phim/logo gốc, REVIEW, transcript, shot map, báo cáo, MP4 và ZIP nguồn.

</details>
