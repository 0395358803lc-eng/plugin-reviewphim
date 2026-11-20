# REVIEW_PHIM v1.3.26 — báo cáo bàn giao

Ngày bàn giao: 20/11/2026 (Asia/Saigon).

Đã triển khai CV-01–CV-12 trong mã nguồn và kiểm thử tại máy.
Quy trình: Production First → User Review → Targeted Revision.
Tên mode `PRODUCTION_FIRST_V1325` và tên module cũ được giữ để tương thích;
schema hoàn thành mới là `stage-completion.v2`, ledger `project-flow-event.v2`.
Không sửa hoặc tự chuyển checkpoint Legacy; không cài plugin vào tài khoản,
không thay kết nối App, không đăng video và không tự merge nhánh chính.

## Thay đổi theo phiếu giao việc

| Hạng mục | Kết quả |
|---|---|
| CV-01 | Kiểm file bắt buộc/hash, FFprobe container/video stream/duration và FFmpeg giải mã toàn bộ. MP4 giả, audio-only, container bị cắt và packet hỏng đều FAILED. Bỏ tin cờ technical_ready. |
| CV-02 | Retry/recover CLI và API, phân loại lỗi, ngân sách hữu hạn theo stage, lưu nguyên nhân/số lần/kết quả. Lỗi quyền không tự retry. |
| CV-03 | DONE chứa package/approval/source/plan/input/output/device/JOB_DIR, record SHA-256 và provenance. Tái dùng kiểm file thật và cấu hình; từ chối dữ liệu thiếu hoặc đổi hash. |
| CV-04 | Mỗi dispatch/resume đọc work_package.lock thật, kiểm owner/package/device/plan. Không chiếm khóa; khôi phục khóa mất cần host xác minh writer đã dừng. |
| CV-05 | Tạo proposal trước rồi mới chờ duyệt sử dụng; delegation hợp lệ bỏ qua cổng sáng tạo. G07 có hai pha sample → approval → bulk trong cùng task. |
| CV-06 | Project Flow là nguồn trạng thái chuẩn; core/guard route Production First về cùng quyết định. PACKAGE_DONE khác PROJECT_FINAL_REVIEW. Ledger ghi trước snapshot, phát hiện state cũ và event hỏng. |
| CV-07 | Năm entrypoint skill và 32 reference có nhánh Production First/Legacy rõ ràng. Không dùng Q01–Q15, web crosscheck, QC từng scene/WAV/batch hoặc G14 ba trục để chặn chế độ mới. |
| CV-08 | Hai manifest lên 1.3.26, metadata/interface/App binding đồng bộ; cả chín defaultPrompt định tuyến Production First. `.app.json` giữ nguyên byte. |
| CV-09 | Vòng lặp đồng bộ gọi executor host, tự chuyển bước, lưu intent/completion/checkpoint, không giả worker chạy nền. CLI start/record và recover tránh chạy lại khi mất phiên. |
| CV-10 | Chỉ định đích tuyệt đối, người dùng chép ảnh, kiểm file/format/geometry/hash/title/approval thật; resume ghi DONE G11B và chạy G12, không gọi lại tạo ảnh. |
| CV-11 | ACCEPTED/REVISION_REQUESTED ghi ledger cùng version/hash/feedback. Đề xuất và khởi chạy revision đường dẫn mới, tái dùng phần không đổi, giữ video cũ. |
| CV-12 | Kiểm thử toàn bộ cùng video MP4 có thể giải mã, lỗi render/retry, mất kết nối/resume, khóa/hash/reuse/thumbnail/final review/revision. Có log, JUnit, ledger và file MP4 thật. |

## Kiểm thử và bằng chứng

**362 passed, 4 skipped, 25 subtests passed; không có bài thất bại.**
Bốn bài skip đều cần tạo symlink, quyền mà tài khoản Windows hiện tại không có.
Các test kiểm khóa sai/thiếu, path traversal, hash nguồn và hash đầu ra vẫn chạy.

- [Log pytest](release-evidence/v1.3.26/pytest.txt), [JUnit](release-evidence/v1.3.26/pytest.xml).
- [Báo cáo probe/decode, phiên bản công cụ và SHA-256](release-evidence/v1.3.26/verification.json).
- [Video tích hợp v1](release-evidence/v1.3.26/integration-v1.mp4) và [v2](release-evidence/v1.3.26/integration-v2.mp4).
- [Ledger append-only](release-evidence/v1.3.26/integration-ledger.jsonl), [tóm tắt tích hợp](release-evidence/v1.3.26/integration-summary.json), [checksum các bằng chứng](release-evidence/v1.3.26/sha256.json).

Bài tích hợp đi qua đủ P00–G15, gồm G11A/G11B, dùng một lần phê duyệt gói qua
`approve_and_start` thật. Render G11 thất bại một lần rồi retry; G11B chờ xác
nhận chép PNG, tiếp tục mà không tạo lại ảnh. G11/G12/G13/G14/G15 có MP4 giải mã
thật. Phản hồi yêu cầu sửa G14 tạo revision chỉ chạy G14/G15; bytes video v1
được giữ nguyên. Ledger ghi phê duyệt tiếp tục, retry, revision và ACCEPTED v2.

Đây là **kiểm thử tích hợp bộ điều phối tại máy với video thử nghiệm thật**.
Các đầu ra nghiệp vụ ASR/dịch/hiểu phim/TTS trong fixture không phải một lần
sản xuất review phim thật qua Remote Desktop Commander/ImageGen/model server.
Không tuyên bố đã nghiệm thu A–Z trên phim thật, kiểm chất lượng nội dung,
hoặc xác minh hoạt động của App sau khi cài. Nghiệm thu phim thuộc người dùng.

## Cách dùng và tái lập

Đọc [hướng dẫn Production First v1.3.26](skills/producing-movie-review-videos/references/PRODUCTION_RELIABILITY_V1326.md).
Host vẫn phải cung cấp executor thật, xác thực tin nhắn và quyền thao tác.
Chỉ chạy FFmpeg/FFprobe đã có và được duyệt; không tự tải/cài phụ thuộc.

```powershell
python skills/producing-movie-review-videos/tools/run_acceptance_v1326.py --output D:\review-phim-acceptance-new
```

Chọn thư mục output mới để không ghi đè bằng chứng. Test harness cần Python
3.11 trở lên, pytest và FFmpeg/FFprobe đã có trên PATH. CLI production yêu cầu
`--owner`; record yêu cầu task_id/plan_hash để tránh nhận nhầm kết quả stage.

Ledger mất đoạn hoặc hash sai sẽ dừng an toàn, không tự sửa lịch sử. Host cần
kiểm worker thực tế trước recover. Import kết quả yêu cầu cùng device/JOB_DIR,
nguồn/input/configuration khớp và schema mới đủ provenance; không hợp thức hóa
bản ghi Legacy thiếu dữ liệu. Giữ riêng nguồn cũ nếu cần mở gói với JOB_DIR mới.

Hai manifest giữ **hai định dạng tương thích hiện có**; identity/version,
description/interface/defaultPrompt và App binding giống nhau theo cấu trúc
tương ứng. Giữ chín prompt theo yêu cầu phiếu giao việc; không tự rút còn ba
hoặc thay cấu hình App để theo một định dạng đóng gói khác.

Danh sách file sửa/thêm: [RELEASE_FILES_V1326.txt](RELEASE_FILES_V1326.txt).
