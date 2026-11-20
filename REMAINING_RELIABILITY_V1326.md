# REVIEW_PHIM 1.3.26 — remaining reliability fixes

MP4 completion now enforces the approved audio and duration contract. A narrated
review without a valid audio stream fails before delivery. Full FFmpeg decoding
checks both video and audio. Explicitly silent outputs remain supported.

Verification cache entries bind the actual file identity, size, change metadata,
SHA-256 and FFprobe/FFmpeg binary identity/version. Read access is checked on every
hit. Source hashes are forced at run/resume/import/review boundaries. Stored
completion evidence can avoid duplicate decoding after a process restart;
executor flags cannot. Same-size writes with restored mtime, replacement files,
changed tool versions, corrupt audio packets and revoked read access are covered.

New journals store deltas with full snapshots every 32 events and at important
states. Sequence, hash chain and reconstructed state hashes remain checked.
Cold reads audit the entire chain; unchanged warm reads reuse the verified head.
A process-scoped OS writer lock protects appends. Durable events precede atomic
snapshots. Existing v2 journals retain their schema and bytes; standalone Legacy
snapshots are not silently migrated. Incomplete tails fail closed and remain
untouched for recovery inspection.

The old overlay manifest moved byte-for-byte to
`skills/producing-movie-review-videos/history/PACKAGE_MANIFEST_V1325.json`.
The user subsequently authorized release 1.3.27 because Plugin Creator cannot
republish the same semantic version; both active manifests are synchronized to
1.3.27. The optional packaging helper now
writes a separately named current manifest using the actual root version.
Plugin/App identity and connector configuration are unchanged.

## Reproducible validation

- Before: 362 passed, 4 Windows symlink skips, 25 subtests; 6.93 seconds.
- After: 378 passed, 4 Windows symlink skips, 25 subtests; 9.00 seconds.
- Linux: 381 passed, 1 Windows-only junction skip, 25 subtests; 6.40 seconds.
  The separate four-test symlink run passed all four without skips in 0.13 s.
  [CI evidence](https://github.com/0395358803lc-eng/plugin-reviewphim/actions/runs/44700525759).
- Windows junction containment: passed with real junction creation, no security
  configuration changes. Together the Windows and Linux runs execute every
  platform-specific path-containment regression.
- Existing interruption, durable-ledger/snapshot-crash recovery, bounded retries
  and targeted revision regressions all pass.
- Tests use real local codec fixtures; they are not user acceptance of a film.

Run `python skills/producing-movie-review-videos/tools/run_acceptance_v1326.py
--output <new-evidence-directory>` with installed pytest and FFmpeg.

The benchmark adds one 4 KiB completion record per event and performs checkpoint
plus read after every event, for 200 events. Baseline is commit `da820b4`.

| Measurement | Before | After |
| --- | ---: | ---: |
| Checkpoint + read total | 131.707 s | 10.071 s |
| Ledger bytes | 84,169,507 | 3,711,251 |
| Cold resume | 0.754 s | 0.500 s |
| Warm resume | 0.747 s | 0.00180 s |

This fixture reduces elapsed time 92.35% and ledger size 95.59%; it is not a
promise about all project sizes or filesystem types. Raw measurements and test
logs are in `release-evidence/v1.3.26-remaining/`. Reproduce using
`tools/benchmark_journal_v1326.py --baseline <old-flow.py> --output <new-dir>`.

## Real film validation in progress

The supplied Fatman source has H.264 1280×720 video and stereo AAC, duration
5823.552 seconds. A separate job uses source interval 10:00–11:00; the source and
old workspace are preserved. Faster Whisper large-v3-turbo has transcribed the
real clip on the RTX 4060. VieNeu v3 Turbo has generated a real Vietnamese voice
proposal on CUDA. ChatGPT generated a real thumbnail for manual placement.

The user approved the 48-second narrated review package and its specific
creative delegations. Real narration, shot selection, timeline, pilot and the
46-second body have been rendered with CUDA VieNeu and NVENC. An intentional
abrupt host exit at G11 left TASK_STARTED durable; the host verified the worker
was inactive, recovered and retried only G11. Earlier completed stages were
preserved. The actual state is WAITING_USER / USER_IMAGE_PLACEMENT at G11B.
Final intro/music rendering, manual image confirmation, user review and the
requested revision are pending. TEST-02 is not complete and no acceptance has
been inferred from synthetic tests.

Technical references: Windows file USN information follows
[Microsoft's read-only file USN API](https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_read_file_usn_data).
The CI uses pinned commits from [actions/checkout](https://github.com/actions/checkout)
and [actions/setup-python](https://github.com/actions/setup-python).
