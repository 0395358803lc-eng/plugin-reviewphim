# REVIEW_PHIM v1.3.26

Production First → User Review → Targeted Revision.

Xem [hướng dẫn v1.3.26](skills/producing-movie-review-videos/references/PRODUCTION_RELIABILITY_V1326.md)
và [báo cáo bàn giao](RELEASE_V1326.md).
Giữ nguyên App/định danh plugin. Không tự cài bản này vào tài khoản hay xuất bản video.

## Tài liệu phiên bản trước

# REVIEW_PHIM — AI Movie Review Producer

Full source snapshot of the current **REVIEW_PHIM v1.3.25** ChatGPT plugin, synchronized on 2026-11-20.

## Source layout

- `plugin.json` and `.codex-plugin/plugin.json`: source manifests, version and entry points
- `skills/`: the plugin's complete skills, policies, tools, templates and regression tests
- `.app.json`: existing ChatGPT Remote Desktop Commander **binding** (not its implementation, connection credentials or an independent worker)

## Current workflow — v1.3.25

**Production First + Autonomous Project Flow & End-to-End Acceptance:**

- A **single approved, bounded package** can start execution without a second approval just to begin.
- `PRODUCTION_FIRST_V1325` moves between stages based on usable completed artifacts rather than intermediate Q01–Q15 **quality gates**. It retains device/path permissions, source and output hashes, actual artifact checks, and authorized installation/deletion limits.
- The project-flow module and CLI provide planned-stage selection, completion recording, checkpoints/resume, final user review and targeted revision. Main CLI commands: `init`, `next`, `record`, `resume`, `review`.
- G04/G05 are each one bounded stage task. Evidence and output are reused when valid.
- For thumbnail G11B, ChatGPT generates the image and the **user downloads and copies PNG/JPG to the approved JOB_DIR/assets**; the remote file must be present and verified before the intro is created.
- Video delivery goes to `FINAL_REVIEW` so the user may accept or request revisions. Independent deletion or external publishing still requires explicit scope and permission.

Start with `skills/producing-movie-review-videos/SKILL.md` and `skills/producing-movie-review-videos/references/PRODUCTION_FIRST_AUTONOMOUS_V1325.md`.

## Important limitations

This is a **plugin source archive**, not a standalone Windows production application, bundled models, rendering binaries or an always-on agent. `project_flow_v1325.py` orchestrates through an executor supplied by the host; it **does not by itself connect to Remote Desktop Commander**, produce a real movie, or continue ChatGPT work after the chat ends.

The v1.3.25 tests include simulated artifacts; they do **not** constitute a successful real-film end-to-end acceptance. In particular, a valid file hash alone does not prove that an MP4 plays correctly; verify decoding before claiming a deliverable is usable.

The legacy QC-based workflow remains available for existing projects unless explicitly migrated with the relevant approvals. Do not use the legacy Qxx gates as automatic blockers for new `PRODUCTION_FIRST_V1325` work.

## Source hygiene

Only source files are tracked here, excluding `__pycache__`, `*.pyc`, and `.pytest_cache`. `skills/producing-movie-review-videos/history/PACKAGE_MANIFEST_V1325.json` is the **historical 1.3.25 changed-files overlay**, retained byte-for-byte; it is not a current repository checksum manifest.

[Original ChatGPT plugin](https://chatgpt.com/plugins/plugins_6afb6aad3c788191aa502d68b438c937).
