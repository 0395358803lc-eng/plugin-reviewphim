# REVIEW_PHIM — AI Movie Review Producer

Complete source snapshot of the existing **REVIEW_PHIM v1.3.24** ChatGPT plugin, synchronized on 2026-11-20.

## Source layout

- `plugin.json` and `.codex-plugin/plugin.json`: source manifests and version
- `skills/`: all plugin skill instructions, policies, scripts, templates and tests
- `.app.json`: the existing ChatGPT Remote Desktop Commander App *binding* only (not the App implementation or credentials)

## Latest behavior (v1.3.24)

- **v1.3.21:** one package approval starts authorized execution, without a second approval to begin
- **v1.3.22:** G04 film understanding and G05 full-review writing use one stage task each, with one stage-level QC
- **v1.3.23:** unified P00–G15 dispatch checks (including G11A/G11B), dependency and human approvals, evidence reuse, and reduced redundant pilot/render work
- **v1.3.24:** ChatGPT generates the YouTube thumbnail; the user downloads it and copies the real PNG/JPG to the approved `JOB_DIR/assets/` destination. G11B checks its presence, dimensions, SHA-256, image and title approval before G12 uses it for the 2-second intro

Read `skills/producing-movie-review-videos/SKILL.md` and `skills/producing-movie-review-videos/references/MANUAL_THUMBNAIL_HANDOFF_V1324.md` for the current workflow. Source film/media must be processed only with appropriate rights and permissions.

## Execution and verification

This repository contains **plugin source**, not bundled AI models, Windows runtimes or a remotely executable application. The plugin's App binding does not itself install or grant access to Remote Desktop Commander; authorized connection and scoped work-package approvals are still required. Log/FFprobe/JSON alone do not substantiate visual or audio QC where actual inspection is required.

Tests and tools live in `skills/producing-movie-review-videos/tests/` and `skills/producing-movie-review-videos/tools/`. Python and pytest caches are excluded. The packaged `PACKAGE_MANIFEST.json` describes the plugin's original update-overlay artifact and is **not** a repository-wide checksum manifest.

[Open the original ChatGPT plugin](https://chatgpt.com/plugins/plugins_6afb6aad3c788191aa502d68b438c937).
