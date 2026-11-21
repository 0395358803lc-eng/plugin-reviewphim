---
name: visual-narration-matching
description: Use when REVIEW_PHIM finds or fixes shots matching Vietnamese voiceover or narration in G04, G06, G08, G09, including actor/action/event alignment, shot candidate scoring, B-roll, WAV timestamp placement, and continuity.
---

# REVIEW_PHIM — Visual–Narration Matching v1.3.28

For every new `PRODUCTION_FIRST_V1325` package, the parent `producing-movie-review-videos` skill and its Production First / reliability policies are authoritative. This skill adds **executable matching methodology**, not another QC gate, stage, beat approval, installation requirement or human confirmation.

Before G08, read [Visual–Narration Matching Engine protocol](../producing-movie-review-videos/references/VISUAL_NARRATION_MATCHING_V1328.md) and inspect the approved G04 `analysis/scene_catalog.json`, `analysis/visual_events.json`, G06 `beats/beats.json`, approved source duration and G07 WAV/voice alignments. Within the existing approved G08 task run:

```text
python skills/producing-movie-review-videos/tools/visual_narration_matcher_v1328.py --job-dir <APPROVED_JOB_DIR> --source-duration <DURATION_S>
```

Use `--beats`, `--scenes`, `--events` if the approved job uses different relative sidecar paths. Optional `--similarities <RELATIVE_JSON>` supports *precomputed*, authorized O02 embeddings (0..1), but the script will not execute or install a model. O01/Qwen3-VL observations can enrich scene catalogs only when the device/model/operation is actually approved and run. Do not claim that model inference or metadata proves motion/actor identity. Original film remains read-only.

The module writes five outputs in JOB_DIR: `shots/shot_candidates.json`, `shots/shot_selection_decisions.json`, `shots/matching_warnings.json`, `shots/shot_map.csv`, `timeline/visual_placement_suggestions.json`. G08/G09 executor must add needed files to the approved `stage_outputs` before execution; no post-hoc plan widening. It never overwrites an existing file; revise into a new authorized job/revision location.

`VERIFIED_VISUAL` requires actual visual observation evidence, visual-verified event and motion evidence when an action needs it. `CANDIDATE` is an unconfirmed shot. Known wrong actor/storyline/source/time hard-reject even if semantic similarity high. If no defensible original-film shot, record `NO_MATCH` and a nonblocking final-review warning, never fill with unrelated footage. Keep voice word timestamps only if measured; no fabricated anchor offsets.

G09 still creates canonical EDL from real WAV timings and approved editing choices; the matcher only suggests source/timeline placements. Production First continues G08→G09 upon usable artifacts; editorial warnings belong to `FINAL_REVIEW`, where the user can request targeted revisions. Do not launch standalone work, network downloads, or production without existing approved scope.
