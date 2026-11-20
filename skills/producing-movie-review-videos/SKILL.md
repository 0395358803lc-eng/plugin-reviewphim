---
name: producing-movie-review-videos
description: Use when the user invokes REVIEW_PHIM, works with remote movie workspace/transcript/translation/audio, or produces Vietnamese movie recap videos G01–G15 including YouTube metadata, thumbnail and intro.
---

# REVIEW_PHIM v1.3.20 — Media Evidence ZIP Handoff + YouTube Metadata / Thumbnail / 2-second Intro, preserving G01–G15

**ƯU TIÊN MỚI v1.3.20 — XEM/NGHE MEDIA BẰNG CHỨNG THẬT:** [MEDIA_EVIDENCE_HANDOFF_V1320](references/MEDIA_EVIDENCE_HANDOFF_V1320.md) (đọc BẮT BUỘC trước xử lý mọi sự cố ở G02/G03/G04/G05/G07/G08/G09/G10/G11/G12/G13/G14 đòi xem clip hoặc nghe audio). Nếu media không thể xem/nghe trực tiếp qua Remote Desktop Commander, trong phạm vi được duyệt ChatGPT trích clip/audio ngắn đúng timecode, đóng ZIP với manifest+SHA-256 trong `JOB_DIR/analysis/media_for_chat/<request_id>/` bằng `tools/media_evidence_handoff.py`; phải thông báo rõ tại sao cần chứng cứ, tạo **link tải có thật** chỉ nếu file thực sự được chuyển và xác minh (không bịa sandbox link/localhost từ đường dẫn remote). Không có transfer → `CHƯA CÓ LINK TẢI TRỰC TIẾP` + đường dẫn máy tính cho người dùng lấy ZIP/upload lại chat. ChatGPT chỉ nói đã **xem** hoặc đã **nghe** nếu đã thật sự kiểm tra media sau upload; ZIP tạo/upload/manifest/ASR không đủ. Không thể nghe sau upload → yêu cầu file WAV/MP4 riêng hoặc giữ `NOT_VERIFIED`/`WAITING_FOR_AUDIO_UPLOAD`. Áp dụng xuyên mọi giai đoạn, không chẻ thành hàng chục gói xét duyệt mới; không tự cấp quyền export dữ liệu ngoài package. Đây là ngoại lệ v1.3.20 có ưu tiên cao hơn hướng dẫn audio upload cũ nếu xung đột, giữ nguyên workflow và human gates khác.

**QUY TẮC MỚI SAU RENDER (ưu tiên v1.3.19):** [YOUTUBE_METADATA_POLICY_V1319](references/YOUTUBE_METADATA_POLICY_V1319.md), [THUMBNAIL_INTRO_POLICY_V1319](references/THUMBNAIL_INTRO_POLICY_V1319.md), [INTRO_CARD_INTEGRATION_V1319](references/INTRO_CARD_INTEGRATION_V1319.md). Giữ 15 giai đoạn chính và P00; chèn **G11A tạo tiêu đề/mô tả YouTube** và **G11B tạo thumbnail ChatGPT thực có chữ theo tiêu đề được chọn** giữa G11 và G12. G12 dùng ảnh được lưu thật vào JOB_DIR làm intro tĩnh **2 giây** và giữ logo/brand profile đã duyệt. G13 nhạc, G14 QC thật, G15 bàn giao thumbnail riêng/metadata/MP4. Bắt buộc tạo ảnh thật, thực sự xem và kiểm chữ tiếng Việt, chuyển được file thật đến JOB_DIR và kiểm hash; thiếu kênh truyền file => BLOCKED, không được PASS nhờ prompt hoặc log. Thumbnail riêng phải upload custom vào YouTube Studio nếu muốn chọn hiển thị; intro 2 giây không bảo đảm YouTube tự lấy ảnh đó. Không tự upload YouTube. Mỗi giai đoạn bổ sung một task/QC; không mở thêm phê duyệt vi mô. Human gates `G11A_METADATA` (chọn tiêu đề) và `G11B_THUMBNAIL` (chọn ảnh) trước G12; cần phân biệt gói cũ không có G11A/B và gói mới có chúng. Không đổi checkpoint hoặc quyền của dự án đang chạy.

**ƯU TIÊN SỐ 0 CHO G05:** [G05_WEB_STORY_CROSSCHECK_V1318](references/G05_WEB_STORY_CROSSCHECK_V1318.md) — sau khi viết xong REVIEW, trước Q05, ChatGPT trực tiếp tìm kiếm web, đọc ít nhất hai nguồn độc lập về đúng phim, đối chiếu logic/cốt truyện quan trọng với lời review và chứng cứ G04; chỉ sửa nếu phim/G04 hỗ trợ. Ghi sources/finding vào `review/g05_web_story_crosscheck.v1.json` và `qc/g05_web_story_crosscheck.v1.md`, tuyệt đối không đưa vào lời kể. Không tìm web thật -> Q05_WEB_STORY_CROSSCHECK=NOT_VERIFIED, không tự PASS.

**ƯU TIÊN TUYỆT ĐỐI G05 / LỜI REVIEW:** [G05_NARRATIVE_ONLY_V1317](references/G05_NARRATIVE_ONLY_V1317.md) — `review_ke_chuyen.txt` và `review_loi_binh_tts.txt` **chỉ kể chuyện phim**, cấm nhắc ASR, transcript, bản dịch, ChatGPT, hình đã xem, báo cáo, QC, web, tiến độ. Evidence/cảnh báo nằm riêng trong review_evidence_map/QC. Chạy `tools/g05_narrative_only_policy.py` trên hai bản trước Q05; giữ sáu bước, một G05 và cổng `G05_SCRIPT` riêng.

**ƯU TIÊN SỐ 1 CHO G02:** [SIMPLE_G02_TEXT_QC_V1316](references/SIMPLE_G02_TEXT_QC_V1316.md) — G02.ASR.FULL toàn phim, một Q02 cho transcript sạch Unicode/format/chính tả rõ ràng; không ép QC 17 cụm hội thoại nhỏ hoặc sửa nội dung từ đoán. Xác minh cốt truyện chuyển sang G04/G05/G08.

**ĐỌC TIẾP:** [ATOMIC_STAGES_V1315](references/ATOMIC_STAGES_V1315.md), [WHOLE_FILM_TRANSCRIPT_V1314](references/WHOLE_FILM_TRANSCRIPT_V1314.md), [STORY_FIRST_WORKFLOW_V1313](references/STORY_FIRST_WORKFLOW_V1313.md), [WORKFLOW_CONSISTENCY_V1312](references/WORKFLOW_CONSISTENCY_V1312.md), [SMART_BATCH_APPROVAL](references/SMART_BATCH_APPROVAL.md). Phần cũ G01–G11 và G13–G15 giữ nguyên trừ QC/delivery liên quan intro, không tự thay cấu trúc các task trước.

## Nhiệm vụ sản xuất

- **P00**: chọn thiết bị qua Remote Desktop Commander, chọn nguồn, kiểm tra workspace cũ/runtime/model/cache có thể tái sử dụng, hardware preflight và danh mục cài; chưa được phép thì không tải/cài.
- **G01**: `G01.SOURCE.FULL`, kiểm FFprobe/hash/timebase/media manifest/visual source profile và một Q01. G01 PASS/evidence hash còn hợp lệ được tái sử dụng.
- **G02**: `G02.ASR.FULL`, WAV toàn phim, ASR toàn phim, transcript/Q02 đơn nhất; lỗi lặt vặt không chặn hiểu phim.
- **G03**: `G03.TRANSLATE.FULL`, ChatGPT dịch toàn bộ transcript theo segment/timecode và một Q03. Cửa sổ nội bộ 40 segment/1.000 từ không phải microtask hoặc approval; không dùng script/local model/API để dịch.
- **G04**: ChatGPT xem frame/clip thật, lập scene catalog/characters/story_map/visual events và `FILM_UNDERSTANDING_READY`; model AI tạo candidates không được tự `VERIFIED_VISUAL` nếu ChatGPT chưa xem evidence thật.
- **G05**: `G05.REVIEW.FULL`, một kịch bản REVIEW sáu bước hoàn chỉnh, một Q05, đối chiếu web, kiểm NARRATIVE_ONLY; bắt buộc phê duyệt `G05_SCRIPT` trước G06.
- **G06–G07**: phân beats khôi phục 100% lời TTS đã duyệt; giọng VieNeu và kiểm chất lượng WAV, cổng `G07_VOICE` trước TTS hàng loạt.
- **G08**: beat → event → scene → clip, kiểm actor/action/storyline/emotion thật; chỉ shot có `VERIFIED_VISUAL` thích hợp mới chọn; `SHOT_SELECTION_READY`.
- **G09–G10**: EDL/timeline/Remotion preview → pilot thực, `G10_PILOT` người dùng duyệt trước khi render full.
- **G11**: render full đã duyệt theo EDL, visual transforms cần thiết; Q11 kỹ thuật/hình, không ép upscale hoặc làm sai nguồn.
- **G11A**: `G11A.YOUTUBE_METADATA.FULL`, tạo 3–5 tiêu đề + mô tả + hashtags/tags từ review đã duyệt và phim thực; một Q11A, chọn title với human gate `G11A_METADATA`, lock hash title.
- **G11B**: `G11B.THUMBNAIL.FULL`, dùng ChatGPT thực sự tạo thumbnail 16:9, có chữ từ title, QC hình/tiếng Việt bằng mắt, lưu ảnh thật vào JOB_DIR; một Q11B và human gate `G11B_THUMBNAIL` khóa hash ảnh. Không nhầm prompt với ảnh và không giả đã truyền file qua Remote Desktop.
- **G12**: sử dụng ảnh G11B làm `assets/intro_card_2s.mp4`, ghép đúng 2 giây vào đầu video full G11, đẩy lời thuyết minh trọn vẹn sang sau intro, đặt logo theo `brand_profile` đã được duyệt, tránh chèn trùng intro; một Q12 gồm xác minh MP4/frame/audio thực.
- **G13**: nhạc nền/sidechain, kiểm âm lượng A/B, không tải nhạc ngoài quyền đã duyệt.
- **G14**: QC MP4 cuối thực tế, ba trạng thái độc lập TECHNICAL/STORY/VISUAL_EDITING cùng PASS mới sẵn sàng xuất bản; kiểm thêm intro 2 giây, chữ, logo, thời gian voiceover, hash thumbnail và metadata khớp. Không tuyên bố kiểm 100% nếu chưa thực sự nghe/xem đủ.
- **G15**: bàn giao MP4, Remotion/EDL, thumbnail JPG/PNG riêng, metadata title/description/hashtag, source/manifest/hash/ZIP; xóa chỉ nếu có `G15_DELETE` theo file cụ thể.

## Phê duyệt, an toàn và trạng thái

- `WORK_PACKAGE_ID`, `schema_version=work-package.v2`, finite task IDs hoặc bounded batches, canonical `plan_hash`, deviceId, roots, source hash, tool/model/install budget, repair budget, stop condition, expected artifacts. Human gates nội dung `G05_SCRIPT`, `G07_VOICE`, `G10_PILOT`, mới `G11A_METADATA`, `G11B_THUMBNAIL` khi phạm vi bao gồm chúng; riêng `G15_DELETE` cho xóa. Trong package mới có G11A/G11B, dùng thêm `tools/publish_workflow_state.py` để kiểm tra dependency/human gates bên cạnh `tools/work_package_state.py` cũ, không coi nó là quyền thực thi.
- Package mới chứa `G11A` và `G11B`: bắt buộc Q11 trước G11A, Q11A + G11A_METADATA trước G11B, Q11B + G11B_THUMBNAIL trước G12; không làm sai phê duyệt G05/G07/G10. Gói legacy chưa bổ sung hai stage chỉ được tiếp tục theo quyền được cấp; không tự mở rộng scope hay làm lại G11.
- Không tự chạy nền giữa các lượt chat; không download/install, CPU fallback, thay OS/PATH/driver, đăng YouTube, chuyển file vào remote hoặc xóa dữ liệu khi chưa được cấp quyền phù hợp. Giữ source movie/logo read-only, ghi trong JOB_DIR, snapshot append-only; `work_package.lock` atomic không cướp, `NOT_VERIFIED` cũ không tự đổi PASS.
- Chỉ nói đã xem/nghe/tạo/tải/ghép ảnh hoặc video nếu công cụ thật chạy và có bằng chứng. Mẫu ảnh người dùng cung cấp là tham chiếu mỹ thuật, không sao chép nhãn hiệu/kênh người khác. Thay title hoặc ảnh sau phê duyệt phải có revision mới, invalidate Q11B/G12/G14/G15 phụ thuộc và phê duyệt tương ứng.

## Tham chiếu

- [MEDIA_EVIDENCE_HANDOFF_V1320](references/MEDIA_EVIDENCE_HANDOFF_V1320.md) và `tools/media_evidence_handoff.py` là quy trình bắt buộc khi vấn đề quan trọng đòi **actual short media** qua ZIP upload.

- [WORKFLOW](references/WORKFLOW.md), [DEFAULTS_AND_TOOLS](references/DEFAULTS_AND_TOOLS.md), [MODEL_ROLE_POLICY](references/MODEL_ROLE_POLICY.md), [ACCEPTANCE_QC](references/ACCEPTANCE_QC.md), [EVIDENCE_SCHEMA](references/EVIDENCE_SCHEMA.md), [FILM_UNDERSTANDING](references/FILM_UNDERSTANDING.md), [SCENE_MATCHING](references/SCENE_MATCHING.md), [VISUAL_EDITING](references/VISUAL_EDITING.md), [REVIEW_STORYTELLING](references/REVIEW_STORYTELLING.md).
- [GPU_FIRST_APPROVAL](references/GPU_FIRST_APPROVAL.md), [WORKSPACE_REUSE_POLICY](references/WORKSPACE_REUSE_POLICY.md), [INSTALLATION_CATALOG](references/INSTALLATION_CATALOG.md), [WORKSPACE_BOOTSTRAP](references/WORKSPACE_BOOTSTRAP.md), [HARDWARE_PROFILE](references/HARDWARE_PROFILE.md).
- [MICROTASK_ORCHESTRATION](references/MICROTASK_ORCHESTRATION.md), [MICROTASK_ACCEPTANCE_REPAIR](references/MICROTASK_ACCEPTANCE_REPAIR.md), [SESSION_ORCHESTRATION](references/SESSION_ORCHESTRATION.md), [APPROVAL_TRANSLATION_AUDIO](references/APPROVAL_TRANSLATION_AUDIO.md).
- `tools/youtube_metadata_policy.py` và `tools/thumbnail_intro_policy.py` chỉ QC cấu trúc/dữ liệu offline, **không phải** công cụ tạo hình, render, nghe/xem hay cấp quyền. Không mặc định thời lượng review, `hflip`, FPS, crop % hay số shot/beat; intro được người dùng chọn 2 giây là ngoại lệ đã xác nhận.
