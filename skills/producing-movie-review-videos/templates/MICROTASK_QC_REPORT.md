# MẪU BÁO CÁO NGHIỆM THU — sau MỌI TASK_ID

**TASK_ID:** `<Gxx.Mnn.Bxxx hoặc P00-...>`  
**QC_STATUS:** `PASS | NEEDS_FIX | NOT_VERIFIED | BLOCKED | PARTIAL | WAITING_FOR_JOB | WAITING_FOR_AUDIO_UPLOAD`  
**Kết luận:** `ĐẠT | CHƯA ĐẠT — CẦN SỬA | CHƯA XÁC MINH | TẠM DỪNG | CHƯA HOÀN TẤT`  
**Máy / deviceId:** `<deviceId>`  
**FILM_DIR / JOB_DIR:** `<đường dẫn đã duyệt>`

## 1. Việc đã làm và sản phẩm

- Phạm vi đã duyệt: `<approved_scope>`, phê duyệt `<approval_ref>`.
- Đầu vào: `input_hashes` / đường dẫn; đầu ra: `output_hashes` / file/bytes/**SHA-256** (đo thật, nếu chưa thể đo ghi UNKNOWN).
- Bằng chứng đọc/xem/nghe thực tế: `<file_id/timecode/evidence refs hoặc NOT_VERIFIED>`.

## 2. Nghiệm thu từng tiêu chí

| criterion_id | expected | actual | evidence_refs | status | blocking |
|---|---|---|---|---|---|
| `<criterion_id>` | `<expected>` | `<actual>` | `<link file/timecode/hash>` | `PASS/FAIL/NOT_VERIFIED/BLOCKED` | `<bool>` |

**Tổng:** `checks_passed/checks_total`. Thiếu bằng chứng hoặc không mở được tệp không được tính PASS.

## 3. Vấn đề và cách sửa

| issue_id | severity | failed_criteria | expected vs actual | evidence_refs | proposed recheck |
|---|---|---|---|---|---|
| `<issue_id hoặc không>` | `BLOCKING/MAJOR/MINOR` | `<criterion>` | `<mong đợi/thực tế>` | `<timecode/path/hash>` | `<phép nghiệm thu lại>` |

**next_action:** `APPROVE_NEXT | APPROVE_REPAIR | VERIFY_EVIDENCE | RECOVER | CHECK_JOB | UPLOAD_AUDIO | STOP`.

- Khi QC_STATUS=`PASS`: trình **Phê duyệt công việc tiếp theo <NEXT_TASK_ID>**, không tự chạy.
- Khi QC_STATUS=`NEEDS_FIX`: trình **Phê duyệt sửa chữa <REPAIR_ID>**; nêu mã lỗi, `repair_scope`, `repair_plan_hash`, đầu vào/đầu ra và cách recheck; không trình nút bước tiếp theo.
- Khi QC_STATUS=`NOT_VERIFIED`: xin kiểm chứng/chờ file âm thanh hoặc clip, không coi thiếu chứng cứ là lỗi chắc chắn.
- Khi `BLOCKED/PARTIAL/WAITING_FOR_JOB`: trình một nút khắc phục hoặc kiểm tra lại tương ứng, giữ checkpoint.

**Lưu:** `qc/microtasks/<safe_TASK_ID>/acceptance.v<attempt>.json` và `.md`, `logs/microtask_ledger.jsonl` khi JOB_DIR đã tồn tại và được phép ghi; nếu chưa có JOB_DIR thì báo trong chat.
