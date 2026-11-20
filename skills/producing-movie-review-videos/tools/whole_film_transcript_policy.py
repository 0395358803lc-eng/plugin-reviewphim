"""Offline policy helpers for a single whole-film G02 ASR task; does not run ASR.

These helpers cannot grant approval, execute tools, verify spoken words, or
modify a movie. Their outputs are advisory inputs for a separately approved
work-package (review-phim v1.3.16).
"""
from __future__ import annotations

import math
import re
from typing import Any

_TASK = "G02.ASR.FULL"


def make_asr_scope(*, source_sha256: str, source_duration_s: float,
                   source_movie: str, job_dir: str, device_id: str) -> dict[str, Any]:
    """Prepare a *single* future ASR task; not an executable authorization."""
    if re.fullmatch(r"[a-fA-F0-9]{64}", source_sha256) is None:
        raise ValueError("source_sha256 must be a 64-character hex digest")
    if not isinstance(source_duration_s, (int, float)) or not math.isfinite(source_duration_s) or source_duration_s <= 0:
        raise ValueError("source_duration_s must be finite and positive")
    if not all(isinstance(x, str) and x.strip() for x in (source_movie, job_dir, device_id)):
        raise ValueError("nonempty source_movie, job_dir, device_id are required")
    return {
        "schema_version": "whole-film-asr-scope.v1",
        "quality_mode": "STORY_FIRST",
        "task_ids": [_TASK],
        "batch_split_policy": "NO_BATCH_SPLIT",
        "device_id": device_id,
        "job_dir": job_dir,
        "source_movie": source_movie,
        "source_sha256": source_sha256.lower(),
        "source_duration_s": float(source_duration_s),
        "auto_install": False,
        "auto_download": False,
        "cpu_fallback_requires_separate_approval": True,
        "approved": False,
        "asr_operations": [{
            "task_id": _TASK,
            "time_window_s": [0.0, float(source_duration_s)],
            "input_audio": "assets/g02_audio/g02_full_source_pcm16kmono.wav",
            "transcript_output": "analysis/transcript_original.jsonl",
            "raw_output": "analysis/g02_asr_full_raw.jsonl",
            "quarantine_output": "analysis/g02_asr_full_quarantine.jsonl",
            "flags_output": "analysis/asr_flags.json",
            "one_model_transcribe_call": True,
            "gpu_first": True,
            "requires_explicit_package_approval": True,
            "qc_policy": "Q02_TEXT_PASS",
            "clean_transcript_output": "analysis/transcript_cleaned.v1.jsonl",
        }],
        "prohibited": ["G02.M02.Bxxx", "ten_minute_windows", "unapproved_CPU_fallback", "unapproved_install"],
    }


def qc_full_film(*, source_duration_s: float, decoded_audio_duration_s: float,
                 input_sha256_verified: bool, whole_file_audio: bool,
                 one_transcribe_call: bool, raw_count: int,
                 provisional_count: int, quarantined_count: int,
                 segments: list[dict[str, Any]], material_blockers: list[str],
                 max_audio_timing_delta_s: float = 0.5) -> dict[str, Any]:
    """Check structure and provenance; absence of speech is not missing audio.

    The caller must verify the *actual bytes* of the original whole-film audio
    and ASR output. Speech segment gaps by themselves are not coverage failures.
    The helper does not assert human hearing or verified film facts.
    """
    durations = (source_duration_s, decoded_audio_duration_s)
    if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0 for x in durations):
        raise ValueError("durations must be finite positive numbers")
    if any(not isinstance(x, int) or x < 0 for x in (raw_count, provisional_count, quarantined_count)):
        raise ValueError("segment counts must be nonnegative integers")
    if not isinstance(segments, list) or not isinstance(material_blockers, list):
        raise TypeError("segments and material_blockers must be lists")
    seen: set[str] = set()
    valid_timecodes = True
    for row in segments:
        if not isinstance(row, dict):
            valid_timecodes = False
            break
        sid = row.get("segment_id")
        st, et = row.get("start"), row.get("end")
        if (not isinstance(sid, str) or not sid or sid in seen or
            not isinstance(st, (int, float)) or not isinstance(et, (int, float)) or
            not math.isfinite(st) or not math.isfinite(et) or
            not (0 <= st < et <= source_duration_s + max_audio_timing_delta_s)):
            valid_timecodes = False
            break
        seen.add(sid)
    consistent_count = raw_count == provisional_count + quarantined_count and len(segments) == provisional_count
    duration_ok = abs(source_duration_s - decoded_audio_duration_s) <= max_audio_timing_delta_s
    technical_ok = all((input_sha256_verified is True, whole_file_audio is True,
                        one_transcribe_call is True, duration_ok, valid_timecodes,
                        consistent_count))
    # v1.3.16: ASR speech/plot uncertainty is documented here, not a Q02 gate.
    # Q02 is a text-output gate; film meaning is validated in G04/G05/G08.
    asr_content_warnings = list(material_blockers)
    blockers = []
    if not technical_ok:
        blockers.append("FULL_MOVIE_AUDIO_OR_ASR_STRUCTURAL_COVERAGE_INCOMPLETE")
    gate = "PASS" if technical_ok else "BLOCKED"
    return {
        "task_id": _TASK,
        "batch_split_policy": "NO_BATCH_SPLIT",
        "technical_qc": "PASS" if technical_ok else "BLOCKED",
        "QC_STATUS": "PASS_WITH_WARNINGS" if technical_ok and not blockers and quarantined_count else "PASS" if technical_ok and not blockers else "BLOCKED" if not technical_ok else "NOT_VERIFIED",
        "Q02_GATE_STATUS": gate,
        "raw_count": raw_count,
        "provisional_count": provisional_count,
        "quarantined_count": quarantined_count,
        "whole_audio_duration_s": decoded_audio_duration_s,
        "duration_matches_source": duration_ok,
        "silence_is_not_missing_audio": True,
        "spoken_words_verified": False,
        "material_blockers": blockers,
        "asr_content_warnings": asr_content_warnings,
        "QC_POLICY": "Q02_TEXT_PASS",
    }
