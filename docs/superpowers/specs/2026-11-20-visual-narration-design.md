# REVIEW_PHIM v1.3.28 — Visual–Narration Matching Engine

Approved intent: improve automatic shot retrieval, candidate evaluation and narration alignment without adding intermediate QC or approvals. This is a code-backed offline module, not a replacement for ChatGPT editorial observation or the approved G04/G06/G08/G09 executors.

## Design
- G04 emits source-scoped scene_catalog and visual_events. G06 emits beats with visual intent and real voice anchors when available. G08 runs offline metadata retrieval/ranking, uses event/actor/action/storyline and optional semantic similarities supplied by a separately authorized model. G09 consumes placement suggestions, validating independent source versus timeline time domains.
- Discard definite contradictions before ranking. Unknown information is not treated as verified. Return candidate, selected, alternate, rejected and unmatched paths with explicit reasons.
- When no exact shot exists, suggest verified reaction/consequence/context frames only if present in source evidence; otherwise `NO_MATCH`, not unrelated filler.
- Preserve 100% narration, never edit approved WAV or source film. Prefer not to reuse visual sequences needlessly. Use measured voice anchors only (never fabricate offsets). Do not assign VERIFIED_VISUAL from cosine/keyword match alone.
- Fail only for malformed/missing input, invalid path or file; `NO_MATCH` and other editorial issues are nonblocking warnings for FINAL_REVIEW.
- Keep Production First stages and ownership/permissions unchanged, and no downloads/installs by this module.

## Scope
- Pure standard-library Python CLI and API, deterministic candidate search/rank and timeline placement suggestions.
- Full editable plugin source update preserving existing App binding and all legacy files.
- Synthetic tests for hard rejects, ambiguous actor, temporal limits, semantic score non-verification, fallback behavior, overlaps, no timestamps, continuity/reuse, path security.
- No new GPU models, no actual film verified in release tests, no claim that model-generated captions prove motion.

## Alternatives considered
1. Keyword matching only: fast but misses semantics and risks wrong story.
2. Qwen/CLIP end-to-end automatic approval: expensive and can hallucinate/mark wrong motion as verified.
3. Hybrid evidence-first deterministic matching with optional embeddings and ChatGPT verification: selected as compatible with offline GPU-first and the user's Production First flow.
