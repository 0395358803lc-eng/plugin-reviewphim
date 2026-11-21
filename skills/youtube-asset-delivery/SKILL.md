---
name: youtube-asset-delivery
description: Must use with REVIEW_PHIM for G11A/G11B YouTube thumbnail creation, G12 logo/watermark overlay, G13/G14 export, and G15 MP4/thumbnail delivery. v1.3.29 separates thumbnail from video and removes 2-second intro.
---

# REVIEW_PHIM v1.3.29 — YouTube Thumbnail & Persistent Logo

**IMPORTANT: Apply to all NEW work packages or explicit new revisions.**
This skill overrides older thumbnail/intro portions of `producing-movie-review-videos/SKILL.md` and references v1.3.19–v1.3.28 only where those parts conflict. All other established rules (P00 source/device/logo selection, permissions, PRODUCTION_FIRST_V1325, SHA and locks, human creative gates, real media, no background work, user final acceptance) remain. Do not alter checkpoints or approval scope for already-running packages without a user-approved revision.

Read `../producing-movie-review-videos/references/THUMBNAIL_WATERMARK_DELIVERY_V1329.md` before drafting a new G11B/G12/G13/G14/G15 execution plan. Read the base skill and its v1.3.26 reliability rules alongside this override.

## Required output behavior

- **G11B:** Create a real 16:9 1280×720 preferred JPEG/PNG YouTube thumbnail, show it, and provide a genuine download. User will manually upload thumbnail in YouTube Studio when posting. Never insert thumbnail into the MP4, never add a 2-second image intro, and do not require user to copy thumbnail into the render machine before G12.
- **G12:** Start video with actual G11 content at t=0, overlay the user-selected P00 logo **top-left throughout every frame** (persistent watermark), not a 2-second logo animation/introduction. Keep original narration start timestamp and duration; no added 2s offset. Preserve logo aspect ratio/transparency and use safe margin, suggested width 8–12% of video width. Use actual FFmpeg/Remotion within the approved device/tool plan.
- **G13/G14:** Continue with G12's logo-overlaid MP4. Check actual MP4 and decode. In Production First do not restore content/style QC gates; final judgment belongs to user.
- **G15:** Deliver final MP4 with persistent logo and separate thumbnail download/reference + YouTube metadata. Do not claim upload to YouTube was performed.

## New Production First execution route

For explicitly opted-in v1.3.29 work packages set:

```
production_config.thumbnail_delivery = DOWNLOAD_SEPARATELY_UPLOAD_IN_YOUTUBE_STUDIO
production_config.thumbnail_embed_in_video = false
production_config.intro_card_enabled = false
production_config.g12_input_thumbnail = false
production_config.logo_overlay = {enabled: true, position: top_left, start: first_frame, end: last_frame, mode: persistent_watermark}
stage_config.G12 = {logo_overlay: true, intro_card_enabled: false}
stage_outputs.G11B = [publish/thumbnail_handoff_v1329.json]
stage_inputs.G12 = {FULL_APPROVED_LOGO_PATH: logo_sha256}
stage_dependencies.G12 = [G11]
```

The host/ChatGPT must generate and actually inspect the thumbnail, deliver a verified download, and write a real G11B JSON handoff file under the approved JOB_DIR with actual generation/download refs, title/hash, image SHA if available and dimensions. **The JSON manifest alone does not prove that an image exists.** If the image cannot be inspected/downloaded, remain WAITING_USER or FAILED honestly; do not substitute a fictional URL or promote status from a flag. G12 does **not** read this manifest or thumbnail.

For opted-in packages use `tools/project_flow_v1329.py` as the Python runner adapter. For CLI use `tools/project_flow_cli_v1329.py`; do **not** start opted-in v1.3.29 jobs with the legacy CLI v1325, which still requires user placement. The new runner preserves the underlying v1325 ledger/reliability engine but validates v1.3.29 contracts instead of v1.3.24 manual-image placement. For all old jobs keep using their approved existing runner and parameters.

## Rendering example (adapt to approved codecs/paths)

```powershell
ffmpeg -i "G11_review.mp4" -loop 1 -i "channel_logo.png" -filter_complex "[1:v]scale=iw*min(1\,192/iw):ih*min(1\,192/iw)[wm];[0:v][wm]overlay=x=main_w*0.02:y=main_h*0.02:shortest=1:format=auto[v]" -map "[v]" -map "0:a?" -c:v h264_nvenc -c:a copy "G12_with_logo.mp4"
```

This command is illustrative; resize to output width for an 8–12% watermark, use GPU encoding only if available and approved, preserve source audio/timestamps, and verify MP4 on the actual machine. It **does not** add a still intro. Do not use FFmpeg commands containing `concat` of 2-second intro or shifting narration by 2 seconds.

## Acceptance/revision constraints

1. The thumbnail is an independent download, and G12 has no G11B dependency. Changing the thumbnail does not require re-rendering G12/G13/G14.
2. The MP4 starts with live film content; voice narration is not delayed by a branding clip. The top-left logo remains visible across the review timeline, subject to any explicitly approved brand exceptions.
3. Do not use fake URLs, assume a tool generated an image, or treat a manifest as equivalent to the image. Preserve authentic artifact provenance in G15 handoff.
4. Keep old packages compatible; user-approved revisions target changed stages only. Do not install, upload, overwrite or delete without proper scope.
