# Implementation plan

1. Write executable tests for `match_beats` and `build_placement_suggestions`: actor/storyline hard reject, candidate retrieval, no fabricated verification, semantic weight cap, missing image warnings, duplicate/reuse limits, voice anchor provenance and time domains. Run first and observe failure.
2. Implement `tools/visual_narration_matcher_v1328.py` using standard library; pure matching API and CLI, safe read/write job-bound paths.
3. Run focused tests, then test CLI producing real JSON/CSV with a synthetic film fixture. Correct failures.
4. Add `references/VISUAL_NARRATION_MATCHING_V1328.md` integrating G04/G06/G08/G09, production-first no QC gate, source model optional, limitations.
5. Preserve account plugin manifests and existing SKILL; update version to 1.3.28 and add active skill direction. Package overlay preserving all other files.
6. Run syntax and full plugin tests where source is accessible, then use guarded Plugin Creator update with release ID; inspect update response/metadata and report any limitation.
