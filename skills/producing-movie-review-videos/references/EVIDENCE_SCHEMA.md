# EVIDENCE_SCHEMA — Hợp đồng dữ liệu G01–G04–G05–G06–G08–G14

**Quy ước:** JSON UTF-8, thời gian giây float trong video gốc với `0 <= start < end <= source_duration` (ngoại lệ sai ASR phải flag riêng), mọi path tương đối với `JOB_DIR`, không chứa `..`, tuyệt đối hoặc link ra ngoài. Tên/ID dùng một kiểu nhất quán. Không coi `confidence=0.99` của model như chứng nhận đúng nếu thiếu ảnh/clip. Mọi giá trị schema ví dụ, không phải nội dung phim có thật.

## G01 `analysis/source_timeline.json`

`source_path`, `source_sha256`, `duration_s`, `video_fps_or_timebase`, `audio_offset_s`, `vfr_detected`, `subtitles_burned_in` (`true/false/unknown`), `probe_ref`, `warnings`. `source_path` chỉ đọc và được phép là đường dẫn phim đã chọn ngoài JOB_DIR; **mọi output khác** phải dưới JOB_DIR.

## G02 `analysis/transcript_original.jsonl` và `analysis/asr_flags.json`

Mỗi dòng `segment_id`, `start_s`, `end_s`, `language`, `text`, `speaker_id` nếu có, `asr_status` = `VALID`/`NEEDS_REVIEW`/`REJECTED`, `audio_kind` = `SPEECH`/`NONSPEECH`/`UNKNOWN`. File flags ghi các trường hợp vượt duration, lặp/ảo giác, đoạn gộp dài, âm không rõ, khoảng không lời và ngôn ngữ xen kẽ. **VAD silence không đồng nghĩa không có hành động trong phim.**

## G03 `analysis/transcript_vi.jsonl`, `analysis/translation_flags.json`

Mỗi dòng giữ `segment_id` và timestamp từ G02, có `source_text`, `translated_text`, `translation_status`. Chuyển tên theo ngữ cảnh, không thêm lời thoại không có trong nguồn; lỗi mơ hồ = `[CẦN ĐỐI CHIẾU ÂM THANH]` và đối tượng flagged.

## G04 `analysis/scene_catalog.json`

Danh sách các object:

```json
{
  "scene_id": "SC-0101",
  "src_in_s": 744.1,
  "src_out_s": 772.8,
  "storyline": "qua_khu",
  "location_hint": null,
  "time_period_hint": null,
  "frames": [{"t_s": 750.0, "file_path": "analysis/frames/SC-0101_750.jpg"}],
  "motion_clips": [],
  "dialogue_refs": ["SEG-101"],
  "visible_actor_ids": ["CHAR-TED"],
  "objects": [],
  "visible_actions": [],
  "audio_cues": [],
  "scene_status": "INDEXED",
  "notes": "Chỉ mục khung hình; chưa xác minh hành động"
}
```

`scene_status` chỉ nhận `INDEXED`, `VISUALLY_REVIEWED`, `NEEDS_REVIEW`. `VISUALLY_REVIEWED` chỉ khi ChatGPT đã thật sự nhìn ảnh; `INDEXED` không chứng minh actor/action.

## G04 `analysis/visual_events.json`

```json
{
  "event_id": "EV-0042",
  "scene_ids": ["SC-0101"],
  "source_start_s": 744.1,
  "source_end_s": 772.8,
  "storyline": "qua_khu",
  "characters": ["CHAR-TED", "CHAR-MURRAY"],
  "action": "Ted đối chất với giáo sư",
  "visible_observations": ["Ted đứng trước bàn giáo sư"],
  "dialogue_summary": "Ted chất vấn về nghiên cứu",
  "emotion_interpretation": "căng thẳng — suy luận từ lời và hành vi",
  "causes": ["EV-0040"],
  "consequences": ["EV-0043"],
  "evidence": [
    {"kind": "frame", "ref": "analysis/frames/SC-0101_750.jpg"},
    {"kind": "transcript", "ref": "analysis/transcript_vi.jsonl", "start_s": 744.1}
  ],
  "verification": "VISUAL_AND_DIALOGUE_VERIFIED",
  "needs_review_reason": null
}
```

Các giá trị `verification` hợp lệ: `VISUAL_AND_DIALOGUE_VERIFIED` (ảnh/chuỗi và thoại đều đối chiếu), `VISUAL_ONLY_VERIFIED` (clip/chuỗi chứng minh hành động không lời), `DIALOGUE_ONLY` (chỉ biết qua thoại, không khẳng định hình), `NEEDS_REVIEW`, `REJECTED`. Tránh gán `VISUAL_ONLY_VERIFIED` cho chuyển động chỉ có một frame. `evidence.kind` = `frame`, `motion_clip`, `transcript`, `audio`, `external_source`; mỗi `ref` nội bộ phải tồn tại, thời điểm đúng duration. Với external fact: dùng `external_source` có URL hoặc thông tin được kiểm chứng riêng, không giả thành media evidence.

## G04 `analysis/story_map.json`

`chronological_events` (list event ID có ý nghĩa trong thời gian câu chuyện), `on_screen_order` (list event ID theo thứ tự trình chiếu), `storylines` (id, mô tả, nhãn thời kỳ), `causal_links` (`from_event`, `to_event`, `verification`), `turning_points` (role, event_id), `unresolved_claims` (claim, reason, impact, next_action). Các event IDs phải tham chiếu từ `visual_events`; không tự tạo sự kiện chỉ để lấp vị trí. `analysis/characters.json` chứa `character_id`, aliases, storylines, evidence_refs, identification_status. `analysis/evidence_index.json` tra cứu path + SHA-256/timestamp/mime nếu phù hợp.

## G05 `review/review_evidence_map.json`

```json
{
  "paragraph_id": "P-0012",
  "review_text_range": [1220, 1384],
  "event_ids": ["EV-0042"],
  "claim_type": "FILM_FACT",
  "evidence_refs": ["EV-0042"],
  "review_status": "SUPPORTED",
  "notes": null
}
```

`review_text_range` tính theo chuỗi UTF-8 đã giải mã trong `review_ke_chuyen.txt` (ký tự Python/codepoints), khoảng `[start,end)`; non-overlap, biên hợp lệ; `paragraph_id` duy nhất. `claim_type` = `FILM_FACT`, `CHARACTER_INFERENCE`, `NARRATOR_COMMENTARY`, `EXTERNAL_FACT`. `review_status` = `SUPPORTED`, `QUALIFIED`, `NEEDS_REVIEW`, `REJECTED`. `FILM_FACT` trọng yếu phải có `event_ids` VERIFIED hoặc `QUALIFIED` khi bằng chứng giới hạn; `EXTERNAL_FACT` cần link nguồn khác xác minh hoặc loại, không lấy REVIEW mẫu làm bằng chứng nguồn.

## G06 `beats/beats.json`, `beats/beat_evidence_coverage.json`

Mỗi beat: `beat_id`, `paragraph_id`, `narration_text`, `event_ids`, `source_scene_ids`, `storyline`, `actor`, `action`, `emotion`, `intent`, `evidence_refs`, `match_status`. Ghép lời beat theo thứ tự phải khôi phục **100%** `review_loi_binh_tts.txt` đã duyệt (xác minh bằng hash/chuỗi), không đổi nghĩa hay tự thêm nhân vật. Coverage file ghi các orphaned beat/claim, unresolved evidence.

## G08 `shots/shot_map.csv`, `shots/shot_evidence.json`

Các cột shot: `beat_id`, `source_scene_id`, `src_in_s`, `src_out_s`, `actor_evidence`, `action_evidence`, `transcript_evidence`, `visual_evidence`, `match_status`, `evidence`. `match_status` chỉ nhận `VERIFIED_VISUAL`, `CANDIDATE`, `NEEDS_REVIEW`, `REJECTED`. Event ID không tự nâng `CANDIDATE` lên verified; phải xem clip ứng viên theo voiceover.

## G14 `qc/g14_story_consistency.md`

Ghi riêng: **kết quả kỹ thuật** và **kết quả biên tập/cốt truyện**; số claim sự kiện kiểm chứng/thiếu, sai nhân vật/tuyến/hành động/nguyên nhân-kết quả, các clip bị REJECTED, bảng timestamp và phương án sửa. `ĐẠT kỹ thuật` không đồng nghĩa `ĐẠT nội dung`; còn sai cốt truyện trọng yếu thì `CẦN SỬA`/`TẠM DỪNG`.

## Biến cố trọng yếu thiếu bằng chứng

Nếu thiếu nguồn hình, file mất hoặc mâu thuẫn ASR, báo `NEEDS_REVIEW`; ChatGPT không được tạo kết luận, tự chấm confidence cao, tự đổi timestamp hay cho G05 qua gate. Chỉ lấy thêm chứng cứ hoặc viết lại outline bỏ/giảm chắc chắn biến cố và trình nghiệm thu G04 lại.

## v1.3.0 — Mở rộng optional tương thích ngược

Các file JSON/JSONL tiếp tục là UTF-8. Các artifact **mới** có `schema_version: "1.3.0"`, `source_sha256`, `source_duration_s`, `generated_by`, `tool_version`, `created_at` nếu biết; không giả metadata. Artifact v1.2 không có field mới **vẫn hợp lệ**, gán `null`, `[]` hoặc `UNKNOWN` cho field optional, tuyệt đối không tự cấp event/verification để lấp schema. Các field và trạng thái cũ giữ nguyên.

**Bảo toàn đường dẫn:** path output tương đối với `JOB_DIR`, từ chối `..`, ổ đĩa, UNC, symlink thoát root. `source_path` ở G01 là ngoại lệ **đã xác minh** (chỉ đọc). Định danh: `SC-*`, `EV-*`, `BEAT-*`, `SHOT-*`, `ISSUE-*` ổn định theo sự kiện đã được duyệt. Model confidence ≠ verification; chỉ ChatGPT kiểm trực tiếp mới xác nhận hình.

**Bảo toàn thời gian:** `src_in_s`, `src_out_s`, `source_in_s`, `source_out_s` luôn là giây phim gốc, `0<=start<end<=source_duration_s`; `voice_in_s`, `voice_out_s`, `timeline_in_frame`, `timeline_out_frame_exclusive` thuộc timeline đầu ra; frame nguyên, duration = `timeline_out_frame_exclusive - timeline_in_frame`, FPS rational `output_fps_num/output_fps_den` được duyệt, không mặc định 24/25. Từ chối thời gian NaN/Infinity, out-of-range và frame âm hoặc 0-duration. Nhóm edit trong EDL không được chồng nhau vô ý, WAV thật là time anchor.

**G01 — `analysis/visual_source_profile.json`:** frame sample timestamps/index, letterbox/pillarbox estimated ranges, active-picture ratio, brightness, `subtitle_regions` theo vùng/time, `burned_subtitle=YES/NO/UNKNOWN`, text risks, `unknowns`, source hash; nhiều mẫu và quan sát thực, không đo từ một dark scene.

**G04 — `analysis/visual_shot_profile.json`:** `scene_id`, `event_ids`, shot boundaries/source time, primary subjects/visible expressions vs emotion interpretation, `shot_type`, `camera_motion`, `visual_purpose`, subtitle/quality flags, `inspection_status`, `motion_verification`, evidence. Ảnh đơn không thể chứng minh motion. Các `scene_catalog` field mới đều optional.

**G05:** `review_outline.json.visual_intent_hints` optional; giữ đủ 6 bước REVIEW, không biến gợi ý thành `FILM_FACT`.

**G06 — `beats/beat_visual_brief.json`:** `beat_id`, `event_ids`, `narration_text`, `visual_intent`, `preferred_shot_types`, `emotional_intensity`, `pacing_intent`, `cut_priority`, `continuity_requirement`, `subject_visibility_requirement`, `avoid_shot_types`, `visual_intent_status` (DRAFT/NEEDS_REVIEW/SUPPORTED). Không sửa text TTS; đủ 100% số ký tự/hashes.

**G08 — `shots/shot_candidates.json`, `shots/shot_selection_decisions.json`:** hard reject sai người/hành động/tuyến/nguồn, `CANDIDATE` không tự verified; selected shot có `selection_reason`, `evidence_refs`, `alternate_shot_ids`, `decision_by_chatgpt`. Giữ các cột shot_map cũ (`beat_id`, `source_scene_id`, `src_in_s`, `src_out_s`, `actor_evidence`, `action_evidence`, `transcript_evidence`, `visual_evidence`, `match_status`, `evidence`) rồi mới thêm cột optional.

**G09 — `timeline/edit_decisions.json`:** EDL canonical; FPS đầu ra rational, `source_in/out_s`, `timeline_in_frame/out_frame_exclusive`, `shot_id`, `beat_ids`, `transition`, `continuity_id`, `reuse_reason`, `transform.hflip=false` mặc định. Giao Remotion và FFmpeg từ **cùng EDL**, không rebuild khác cut. `timeline/pacing_report.json` đo các điểm cắt và lặp, không giả số scene detection là số cut thực.

**G11:** `timeline/visual_transform_manifest.json` ghi requested/applied transform, ảnh before/after, lý do; `qc/g11_frame_comparison.json` cho từng shot, không tự cho PASS khi mất chứng cứ/crop che mặt.

**G12 — `assets/brand_profile.json`:** chỉ theo kênh/logo đã duyệt, `logo_path`, `anchor`, `size_percent`, `opacity`, `safe_margin_percent`, `show_from_s`, `show_to_s`, `intro_enabled`, `intro_duration_s`, `text_watermark` tùy chọn; overlay sau transform không bị lật.

**G14 — `qc/visual_editing_qc.json`:** issue IDs, severity (`INFO/WARNING/NEEDS_FIX/BLOCKING`), timeline frames, beat/shot, expected vs actual, evidence, action. Độc lập `TECHNICAL_STATUS`, `STORY_STATUS`, `VISUAL_EDITING_STATUS` enum `PASS/NEEDS_FIX/NOT_VERIFIED/BLOCKED`, chỉ phát hành khi cả ba PASS và gate phê duyệt đã có.

### Năm ví dụ v1.3 — DỮ LIỆU MINH HỌA, không phải chứng cứ phim thật

**Ví dụ 1**

```json
{
  "schema_version": "1.3.0",
  "scene_id": "SC-0101",
  "source_start_s": 744.1,
  "source_end_s": 752.3,
  "event_ids": ["EV-0042"],
  "primary_subject_ids": ["CHAR-TED"],
  "shot_type": "CLOSE_UP",
  "camera_motion": "STATIC",
  "visual_purpose": "REACTION",
  "facial_expression_observed": "cau mày, nhìn về phía người đối thoại",
  "emotion_interpretation": "căng thẳng; cần ngữ cảnh thoại để kết luận",
  "subtitle_region": "UNKNOWN",
  "quality_flags": [],
  "inspection_status": "VISUALLY_REVIEWED",
  "motion_verification": "UNKNOWN",
  "evidence_refs": ["analysis/frames/SC-0101_750.jpg"],
  "notes": "Cỡ cảnh có thể thấy từ frame; không suy chuyển động từ ảnh đơn"
}
```

**Ví dụ 2**

```json
{
  "schema_version": "1.3.0",
  "beat_id": "BEAT-0012",
  "event_ids": ["EV-0042"],
  "narration_text": "Ted bắt đầu mất bình tĩnh khi cuộc tranh luận căng thẳng hơn.",
  "visual_intent": "Ưu tiên phản ứng nét mặt của Ted; tránh cảnh không liên quan",
  "preferred_shot_types": ["CLOSE_UP", "MEDIUM"],
  "emotional_intensity": "HIGH",
  "pacing_intent": "ADAPTIVE",
  "cut_priority": "MEDIUM",
  "continuity_requirement": "CAN_INTERCUT",
  "subject_visibility_requirement": ["CHAR-TED"],
  "visual_intent_status": "DRAFT"
}
```

**Ví dụ 3**

```json
{
  "shot_id": "SHOT-0019",
  "beat_id": "BEAT-0012",
  "scene_id": "SC-0101",
  "event_ids": ["EV-0042"],
  "src_in_s": 746.2,
  "src_out_s": 750.8,
  "match_status": "CANDIDATE",
  "hard_reject_reasons": [],
  "selection_reason": "Đúng chủ thể và phản ứng; chuyển động đang cần clip để kiểm chứng",
  "evidence_refs": ["analysis/frames/SC-0101_750.jpg"],
  "decision_by_chatgpt": "PENDING",
  "alternate_shot_ids": [],
  "transform_hint": {"hflip": false, "crop_mode": "NONE"}
}
```

**Ví dụ 4**

```json
{
  "schema_version": "1.3.0",
  "output_fps_num": 25,
  "output_fps_den": 1,
  "edits": [
    {
      "edit_id": "EDIT-0019",
      "shot_id": "SHOT-0019",
      "beat_ids": ["BEAT-0012"],
      "source_scene_id": "SC-0101",
      "source_in_s": 746.2,
      "source_out_s": 750.8,
      "timeline_in_frame": 1500,
      "timeline_out_frame_exclusive": 1615,
      "transform": {
        "hflip": false,
        "crop_mode": "NONE",
        "scale_mode": "FIT",
        "position_x": 0.5,
        "position_y": 0.5
      },
      "transition": "CUT",
      "continuity_id": "CONT-0042",
      "reuse_reason": null
    }
  ]
}
```

**Ví dụ 5**

```json
{
  "issue_id": "ISSUE-0031",
  "severity": "BLOCKING",
  "timeline_in_frame": 1500,
  "timeline_out_frame_exclusive": 1615,
  "beat_id": "BEAT-0012",
  "shot_id": "SHOT-0019",
  "check": "SOURCE_MATCH",
  "expected": "Ted phản ứng trong cảnh tranh luận",
  "actual": "Ứng viên chưa có clip xác minh chuyển động",
  "evidence_refs": ["analysis/frames/SC-0101_750.jpg"],
  "status": "NEEDS_REVIEW",
  "action": "Xem clip thực; không chấp nhận chỉ một frame"
}
```
