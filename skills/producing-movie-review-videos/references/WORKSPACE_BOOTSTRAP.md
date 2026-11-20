# WORKSPACE_BOOTSTRAP — Cấu trúc sạch cho từng phim, không sao chép bộ cài cũ

Sau khi xác minh đúng máy/deviceId, `FILM_DIR` tuyệt đối và `SOURCE_MOVIE` chính xác, trình duyệt scaffold và tạo cây `REVIEW_PHIM_WORKSPACE/<safe-project-id>` với `JOB_DIR` riêng. Đây **không phải G01**, **không yêu cầu phê duyệt cài đặt**, nhưng vẫn cần duyệt tạo workspace. Nếu chỉ cho phép **chỉ đọc/chưa thay đổi dữ liệu** thì không tạo.

## Điều kiện

- `safe-project-id` chỉ ký tự an toàn (chữ/số/`-`), không ghi đè dự án cùng tên của phim khác.
- Kiểm canonical path, junction/symlink/reparse point, quyền và dung lượng trước khi tạo; chỉ tạo thư mục còn thiếu, **không ghi đè**, không xóa, không chạm phim/logo nguồn.
- Scaffolding không dò/copy tool, model hay cache. P00-5 tiếp theo **có quyền kiểm kê software trong các REVIEW_PHIM_WORKSPACE cũ** sau khi được duyệt theo `WORKSPACE_REUSE_POLICY.md`; **không khám phá phần mềm trên máy** một cách tùy tiện ngoài các workspace đã duyệt.

```text
FILM_DIR/
  SOURCE_MOVIE                            # chỉ đọc
  REVIEW_PHIM_WORKSPACE/
    safe-project-id/                     # JOB_DIR mới
      analysis/                          # cảnh/transcript/sự kiện
      review/                            # kịch bản/evidence
      beats/                             # beat map
      voice/                             # TTS
      shots/                             # shot map
      timeline/                          # Remotion/EDL
      music/                             # cues
      assets/                            # branding đã duyệt
      out/                               # MP4
      qc/                                # nghiệm thu
      logs/                              # approvals, runtime_reuse_manifest.json khi duyệt
      temp/                              # writable temp
      cache/                             # writable caches mới
      models/                            # model mới khi duyệt
      tools/                             # runtime mới khi duyệt
      npm-cache/                         # npm cache mới
      # .venv/                           # chỉ sau duyệt cài mới
      # tools/remotion/node_modules/     # chỉ sau duyệt cài mới
```

**Không cần chép/di chuyển runtime từ workspace cũ vào cây mới:** nếu nguồn cũ được xác minh tương thích và người dùng duyệt, gọi bằng đường dẫn tuyệt đối và chỉ đọc từ nguồn; mọi ghi mới vào JOB_DIR. Không link chéo, không thay đổi workspace cũ.

Chỉ sau duyệt G04 mới tạo `analysis/frames/`, `analysis/contact_sheets/`, `analysis/motion_checks/`. Không tạo file trống giả hoàn thành. Sau scaffold: liệt kê nhánh đã tạo, hỏi logo, chạy P00-5 phần cứng **và reuse inventory**, rồi trình đủ danh mục theo `INSTALLATION_CATALOG.md`, dừng chờ duyệt; không tự chạy G01.

## Artifacts không tạo sớm

- G01: `analysis/media_probe.json`, `analysis/source_timeline.json`, `analysis/visual_source_profile.json`.
- G04: `analysis/scene_catalog.json`, `analysis/visual_events.json`, `analysis/story_map.json`, `analysis/evidence_index.json`, `analysis/visual_shot_profile.json`.
- G06: `beats/beat_visual_brief.json`.
- G08: `shots/shot_candidates.json`, `shots/shot_selection_decisions.json`.
- G09: `timeline/edit_decisions.json`, `timeline/pacing_report.json`.
- G10: `qc/g10_pilot_visual_review.md`.
- G11: `timeline/visual_transform_manifest.json`, `qc/g11_frame_comparison.json`.
- G12: `assets/brand_profile.json`.
- G14: `qc/visual_editing_qc.json`, `qc/visual_editing_qc.md`.

Resume chỉ theo source hash/approval/checkpoint đúng job; không được tái sử dụng phim, transcript hay sản phẩm cũ. Chỉ runtime/model trong REVIEW_PHIM_WORKSPACE cũ **đã kiểm chứng và được duyệt** mới được phép tham chiếu.
