# REVIEW_PHIM v1.3.28 — Visual–Narration Matching Engine

## Effective mode and precedence

For a newly approved `execution_mode=PRODUCTION_FIRST_V1325` package, keep `PRODUCTION_FIRST_AUTONOMOUS_V1325.md` and `PRODUCTION_RELIABILITY_V1326.md` in control of workflow and artifacts. This document defines G04/G06/G08/G09 **production methodology**, NOT a new approval/QC gate. Never resurrect legacy `Q08/SHOT_SELECTION_READY` blocking, scene/beat microtasks, or extra user acceptance before rendering. If source/permissions/executables absent, stop according to the approved plan; if imagery weak/unverified, save warnings and deliver a draft for the user's final review.

## Real engine and boundaries

`tools/visual_narration_matcher_v1328.py` is a standard-library, deterministic, offline retriever/ranker and timing suggestion generator. It does NOT install models, run CLIP/Qwen3-VL, inspect a raw movie, listen to audio, recognize faces, prove motion, independently write a canonical EDL or render video. Executor must supply source-indexed evidence or use explicitly authorized source-inspection tools. Do not label outputs as machine-observed if the only source is captions or metadata.

G04: Keep `analysis/scene_catalog.json` with real source `src_in_s/src_out_s`, `visible_actor_ids`, `visible_actions`, `event_ids`, `storyline`, `visual_description`, `scene_status`, `frames`, `motion_clips`, optional `quality_flags/visual_purpose`. G04 `visual_events.json` links `event_id`, `scene_ids`, action, characters, verified visual evidence. Preserve source SHA/provenance. Scene detector frames are merely indexed, not verified.

G06: Provide `beats/beats.json` containing `beat_id`, `narration_text`, `actor`/`actor_ids`, `action`, `storyline`, `event_ids`, `visual_intent`, optionally `voice_in_s/voice_out_s`, and only *measured* `word_timestamps` (`text`, `start_s`, `end_s`). Maintain 100% approved review text; never generate or translate narration using this script. G07 provides WAV and real alignment if available; no fabricated word anchors.

G08: Reuse prior G04 index instead of reprocessing film unless evidence is absent/invalid. Run:

```text
python tools/visual_narration_matcher_v1328.py --job-dir <APPROVED_JOB_DIR> --source-duration <SOURCE_DURATION_S> --beats beats/beats.json --scenes analysis/scene_catalog.json --events analysis/visual_events.json
```

Optional `--similarities shots/precomputed_semantic_similarity.json` maps beat_id → scene_id → normalized 0..1 from a separately approved O02/CLIP retrieval executor. Optional O01/Qwen-VL observations may enrich G04 scene descriptors before this step. DO NOT install/use them automatically, infer `VERIFIED_VISUAL` from cosine, or let a visual model certify character/motion by itself. All input paths are relative to approved JOB_DIR and output never overwrites existing results; for revisions use a separately approved fresh JOB_DIR/revision output scope.

G08 artifacts:
- `shots/shot_candidates.json`: up to five valid ranked candidates per beat plus hard-rejected candidates/reasons; score includes event, actor, action, semantic hint, continuity/reuse. Score is a *ranking*, never a percentage accuracy guarantee.
- `shots/shot_selection_decisions.json`: selected and alternate scene/shot IDs, source in/out, reason, evidence, and `decision_by_chatgpt=PENDING` unless ChatGPT actually inspected media.
- `shots/shot_map.csv`: practical selected mapping; `CANDIDATE`, `VERIFIED_VISUAL` or `NO_MATCH` preserved.
- `shots/matching_warnings.json`: `NO_VISUAL_MATCH`, `UNVERIFIED_VISUAL`, `VISUAL_REUSE`, `SHORT_VISUAL`, `VOICE_ANCHOR_MISSING` when applicable. These are editorial warnings, not technical FAILED gates in Production First.

Hard reject: known wrong actor, explicit different storyline, contradicted action if flagged, invalid source interval, wrong source kind, or no defensible link. Unknown actors/actions stay unverified rather than forced rejection. Reaction/consequence/context cutaways are allowed when scene matches subject and meaning; avoid random filler. Mark `VERIFIED_VISUAL` ONLY when a source frame/clip was really reviewed, event had visual verification and motion evidence supports the asserted action. Otherwise `CANDIDATE` even when cosine is high.

G09: consume `timeline/visual_placement_suggestions.json` and actual G07 WAV/voice timing. Source timestamps remain movie seconds; timeline timestamps are output seconds. Clip shorter than voice beat produces `SHORT_VISUAL` and requires another supported shot to fill; never artificially extend source range, loop unrelated footage or change approved audio text. Word anchors are output only when supplied and validated; if no voice timestamp, leave unknown. Canonical EDL remains `timeline/edit_decisions.json` produced by approved G09 executor, not by matcher itself. Human editorial acceptance happens at FINAL_REVIEW, with targeted revisions keeping old MP4.

## Security and operational notes

The script is read-only on supplied scene/beat/event input and cannot access outside JOB_DIR through path traversal or symlinks. It creates only the five named sidecars in `shots/` and `timeline/`; no network calls, installation, source changes, third-party footage, or deletions. G08 executor must include these sidecars in the package's authorized stage outputs if the matcher is used. The project-flow state machine still requires actual files, correct hashes, plan lock, permissions and downstream playable MP4; the matcher alone does not advance stages.

No new A/O install catalog IDs. Existing optional Qwen3-VL / CLIP are available only if approved in the package and actually installed on the chosen device. Synthetic tests cannot establish production film accuracy; validate on an authorized film before advertising result percentages.
