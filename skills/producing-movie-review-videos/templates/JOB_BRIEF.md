# JOB_BRIEF — Tiếp nhận và duyệt riêng REVIEW_PHIM G01–G15

**Điền các thông tin đã có, chỉ hỏi khi thiếu.** Không chạy G01–G15 khi chưa phê duyệt riêng theo `references/SESSION_ORCHESTRATION.md`.

## P00 — Chọn máy/phim/logo

- Máy online đã chọn: `[hostname / deviceId]` — từ `mcp__Remote_Desktop_Commander__list_devices`, không dùng trí nhớ.
- Account/link Remote Desktop Commander: `[tài khoản đúng]` nếu có nhiều.
- Thư mục chứa phim `FILM_DIR`: `[path tuyệt đối]`.
- Phim gốc `SOURCE_MOVIE`: `[tệp chính xác đã xác nhận]`.
- Thư mục chứa logo `LOGO_DIR`: `[path]` hoặc `[KHÔNG DÙNG LOGO]` được xác nhận.
- Tệp logo: `[LOGO_FILE]` được chọn, phim/logo gốc chỉ đọc.
- Thư mục làm việc `JOB_DIR`: `FILM_DIR\REVIEW_PHIM_WORKSPACE\<project-id>`; scaffold rỗng đã có/được tạo/bị chặn.
- Disk/canonical path/quyền ghi/junction: `[kết quả]`.

## P01-HW — Báo cáo cấu hình phần cứng (CHỈ ĐỌC) trước danh mục

- Thời điểm/deviceId được xác minh: `[ ]`.
- CPU `[hãng/model]`, nhân vật lý `[ ]`, luồng `[ ]`, kiến trúc/ISA `[x64/ARM64/UNKNOWN]`.
- RAM tổng `[GB]`, khả dụng `[GB hoặc UNKNOWN]`.
- GPU(s) `[hãng/model/số GPU]`, VRAM thực `[GB hoặc UNKNOWN]`; khả năng GPU compute `[ĐÃ XÁC MINH / CHƯA XÁC MINH]`.
- Windows OS/arch `[ ]`, ổ chứa `JOB_DIR` và dung lượng trống `[GB]`.
- Trường chưa xác định/cảnh báo/nguồn kiểm chứng `[ ]`.
- Kế hoạch hiệu năng: `[CPU/GPU dự kiến | ASR precision/batch | render workers | TTS | vision Oxx | QC]`.
- **Chỉ đọc phần cứng, không kiểm kê phần mềm/model đã có.** Nếu chưa xác minh thì không tuyên bố đã tối ưu theo máy.

## P02 — Danh sách cài đặt chuẩn và phê duyệt

**Không kiểm kê công cụ/thư viện/model đã có trên máy.** Luôn trình toàn bộ các ID trong `references/INSTALLATION_CATALOG.md` để người dùng duyệt; không cắt danh sách theo PATH hay phần mềm đang có. Không dùng lại bản cài/global environment/model/cache bên ngoài `JOB_DIR`.

| ID | Công cụ/thư viện/model cần cài mới | Vai trò Gxx | Phiên bản/nguồn dự kiến | Đích trong JOB_DIR | Dung lượng hoặc chưa xác định | Tối ưu phần cứng/backend/batch/threads | Phê duyệt |
|---|---|---|---|---|---|---|---|
| A01 | FFmpeg/FFprobe portable | G01–G04/G08/G14 | | `tools/ffmpeg/` | | | |
| A02 | Python runtime + pip/venv | G02–G14 | | `tools/python/`, `.venv/` | | | |
| A03 | PySceneDetect/OpenCV/Pillow/NumPy | G04/G08 | | `.venv/` | | | |
| A04 | Faster-Whisper/CTranslate2 + Whisper Large V3 Turbo | G02 | | `.venv/`, `models/asr/` | | | |
| A05 | VieNeu-TTS engine; model/giọng cần duyệt | G07 | | `.venv/`, `models/tts/` | | | |
| A06 | Node.js/npm/React/Remotion portable | G09–G14 | | `tools/node/`, `tools/remotion/` | | | |
| A07 | Chromium portable (khi renderer cần) | G09–G14 | | `tools/browser/` | | | |
| A08 | Bộ tiện ích dựng contact sheet/khớp hash/QC | G01–G14 | | `tools/`, `.venv/` | | | |
| O01 | Vision Qwen-VL | G04/G08 tùy chọn | | `models/vision/` | | | |
| O02 | CLIP/embedding index | G04/G08 tùy chọn | | `models/embeddings/` | | | |
| O03 | Upscale/denoise | G11 tùy chọn | | `tools/upscale/` | | | |

- `Remote Desktop Commander` và ChatGPT đọc ảnh không phải các gói cài trong JOB_DIR.
- Giới hạn: cache/temp/venv/models/tools/runtime mới chỉ ghi trong JOB_DIR; không tự cài lên ổ C: hoặc system PATH.
- Quyền phê duyệt cài: `[chưa / A01–A08 / các tùy chọn Oxx / giới hạn riêng]`.
- Hậu kiểm sau cài: `[đường dẫn nội bộ, lệnh smoke test, PASS/NEEDS_FIX/BLOCKED]` — **chỉ trên bộ cài vừa cài**.
- Cài đặt không đồng nghĩa phê duyệt chạy G01.

## Thông số review và story design

- Tên phim: `[đã xác minh]`, ngôn ngữ: `[ASR]`, timeline: `[VFR/FPS/duration]`.
- Kiểu REVIEW: kể chuyện cuốn hút có nguồn hình/thoại; không bịa; giọng/tone: `[kênh/thể loại]`.
- **Không mặc định thời lượng**; mục tiêu `[theo user nếu có]`.
- Giọng: Trúc Ly 1.00x chỉ preset tham khảo; giọng thực `[duyệt]`.
- Phân giải: theo nguồn; Full HD 1080p nếu phù hợp, intro 2 giây đề xuất, logo đã chọn hoặc không logo.
- Nhạc nền: không lời, nhỏ hơn voice, sidechain ducking nếu duyệt; nguồn rõ.
- Output: MP4, tài liệu phân tích, transcript, review, shot map, timeline, QC, ZIP trong JOB_DIR.

## Gate G04 — FILM_UNDERSTANDING_READY

- Scene catalog: `[analysis/scene_catalog.json]`; số cảnh/chỉ mục `[ ]`.
- Contact sheets thực sự đã ChatGPT đọc: `[batch ids, số frame, time ranges]`.
- Motion checks clip: `[số, IDs và lý do]`; vùng im lặng có sự kiện: `[ ]`.
- Story map: `[analysis/story_map.json]` (chronological/on_screen_order và tuyến).
- Visual events/evidence index: `[path, số event chính verified]`.
- Core unresolved claims: `[đếm, mô tả, cách xử lý]`.
- QC gate: `[READY / BLOCKED]` + `qc/g04_evidence_report.md`; **chỉ READY mới trình duyệt G05**.

## Gate G05 — REVIEW_STORY_READY

- Outline 6 bước: `[review/review_outline.json]` + event id trọng yếu.
- Kịch bản kể/TTS: `[review/review_ke_chuyen.txt]`, `[review/review_loi_binh_tts.txt]`.
- Evidence map: `[review/review_evidence_map.json]` + claim supported/qualified/unresolved/external.
- Độ dài: `[số từ, thời lượng ước tính không ép]`, phân biệt review draft và đã duyệt.
- QC: `[READY / NEEDS_FIX]`; chỉ qua gate và được duyệt G06 riêng mới chuyển.

## Phê duyệt giai đoạn và resume

- Giai đoạn đề xuất `[G01..G15]`, input, output, công cụ, path ghi, rủi ro; trạng thái `[PROPOSED / APPROVED / RUNNING / REPORTED / NEEDS_FIX / BLOCKED]`.
- Đã phê duyệt rõ đúng Gxx: `[chưa / phạm vi đã duyệt]`, bằng chứng giai đoạn trước: `[path và hash]`.
- Không tự chạy bước tiếp theo; **G15 cần phê duyệt xóa riêng** theo từng path.

## v1.3 — Phê duyệt lựa chọn dựng hình (theo từng stage, KHÔNG tự áp mặc định)

- G01 nguồn hình: active picture, bar/subtitle, `visual_source_profile.json`, vùng UNKNOWN.
- G04: số batch đã ChatGPT xem, shot_type/camera_motion/visual_purpose đã xác minh, cần motion clips, `visual_shot_profile.json`.
- G05: visual_intent_hints chỉ gợi ý, giữ chính xác REVIEW sáu bước.
- G06: `beat_visual_brief.json`, ưu tiên CLOSE_UP/MEDIUM/WIDE/DETAIL theo từng beat, `pacing_intent`, `continuity_requirement`.
- G08: `shot_candidates.json`/decisions, actor/action hard reject, `SHOT_SELECTION_READY`, cần user duyệt riêng G09.
- G09: FPS rational mong muốn `[duyệt/chưa]`, EDL source/timeline thời gian tách biệt, WAV thực, transition/cut theo beat, reuse_reason, không mặc định 2,04 giây.
- G10: pilot có bối cảnh+chuyển ý+phản ứng/hành động, user duyệt kết quả nghe nhìn.
- G11: yêu cầu crop/reframe `[NONE/CROP/PAD]`, phụ đề nguồn, vùng chữ, `hflip=false` mặc định (nếu muốn bật phải duyệt theo shot), nâng nét `[chỉ khi cần]`, before/after.
- G12: `brand_profile.json`, logo theo kênh được user chọn, safe area và opacity, overlay sau transform.
- G14: ba trạng thái QC kỹ thuật/cốt truyện/visual editing, issue severity/timecode và điều kiện xuất bản; chưa xem-nghe liên tục thì `NOT_VERIFIED`.
