# REVIEW_PHIM v1.3.28 — Visual–Narration Matching

- Added executable offline scene↔beat retrieval/ranking in `tools/visual_narration_matcher_v1328.py` with source time and voice timeline suggestions.
- Added safe multi-candidate search, explicit semantic/actor/storyline hard rejects, optional precomputed cosine hints, no fabricated visual verification, reuse-aware selection, no-filler `NO_MATCH` and nonblocking warnings.
- Added synthetic unit/CLI regression tests and executable protocol `references/VISUAL_NARRATION_MATCHING_V1328.md`.
- Production First unchanged: no intermediate QC gates, no extra per-beat approvals, G08/G09 run only within an approved work package; final video remains for user acceptance/revision.
- Limitations: metadata-based retrieval, optional models not invoked, no film dataset accuracy benchmark, executor still integrates model evidence and canonical EDL.
