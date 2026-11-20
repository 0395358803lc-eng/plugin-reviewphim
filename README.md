# REVIEW_PHIM — AI Movie Review Producer

Complete source snapshot of the **REVIEW_PHIM v1.3.20** ChatGPT plugin, published 2026-11-20.

## Contents

- `plugin.json`, `.codex-plugin/plugin.json` — manifests
- `skills/` — packaged skills, workflow documentation, tools and tests
- `.app.json` — existing Remote Desktop Commander binding metadata; actual App is not embedded

## Workflow

P00 prepares the approved workspace. G01–G15 cover source verification, speech transcription, translation, multimodal film understanding, review writing, beat planning, voiceover, scene matching, editing, pilot, rendering, branding, sound, QC and delivery.

v1.3.19 adds G11A YouTube metadata, G11B custom thumbnail and a 2-second title-card intro to G12. v1.3.20 adds short video/audio ZIP handoff for actual ChatGPT viewing/listening when media inspection is required.

Read `skills/producing-movie-review-videos/SKILL.md` and `skills/producing-movie-review-videos/references/WORKFLOW.md` before use. This repository does not supply remote access authorization or install dependencies. Source movies and media must be handled under applicable permissions and copyright requirements. See `skills/producing-movie-review-videos/references/THIRD_PARTY_NOTICES.md`.

## Tests and source hygiene

Validation files are in `skills/producing-movie-review-videos/tests/`. Generated `__pycache__`, `.pyc` and `.pytest_cache` are not tracked; all source files, manifests, reference policies and test sources from the plugin are included.

[Open ChatGPT plugin](https://chatgpt.com/plugins/plugins_6afb6aad3c788191aa502d68b438c937).
