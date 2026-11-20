"""Offline policy helpers for whole-stage G01/G03/G05; does NOT execute film tasks.

No local translation, external network, machine access, file writes or ASR execution.
Only run these helpers if a work package has approved that tool execution.
"""
from __future__ import annotations

import re
from typing import Any

TASKS = {"G01": "G01.SOURCE.FULL", "G03": "G03.TRANSLATE.FULL", "G05": "G05.REVIEW.FULL"}


def make_stage_scope(stage: str, *, source_sha256: str, device_id: str,
                     job_dir: str, source_duration_s: float | None = None) -> dict[str, Any]:
    """Produce bounded *scope only*, not user approval or executable permission."""
    if stage not in TASKS:
        raise ValueError("Only G01/G03/G05 are atomic stages in v1.3.15")
    if not isinstance(source_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", source_sha256):
        raise ValueError("source_sha256 is required, 64 hexadecimal characters")
    if not isinstance(device_id, str) or not device_id.strip():
        raise ValueError("device_id is required")
    if not isinstance(job_dir, str) or not job_dir.strip():
        raise ValueError("job_dir is required")
    if source_duration_s is not None and (not isinstance(source_duration_s, (int, float)) or
                                          not 0 < source_duration_s < float("inf")):
        raise ValueError("source_duration_s must be positive and finite")
    required = {
        "G01": ["SOURCE_MOVIE", "FILM_DIR", "JOB_DIR"],
        "G03": ["Q02_PASS", "analysis/transcript_original.jsonl", "JOB_DIR"],
        "G05": ["FILM_UNDERSTANDING_READY", "analysis/story_map.json", "JOB_DIR"],
    }
    return {
        "schema_version": "whole-stage-scope.v1", "quality_mode": "STORY_FIRST",
        "stage": stage, "task_ids": [TASKS[stage]], "work_split_policy": "NO_STAGE_SPLIT",
        "stage_qc": "Q" + stage[1:], "source_sha256": source_sha256.lower(),
        "device_id": device_id, "job_dir": job_dir, "source_duration_s": source_duration_s,
        "prerequisites": required[stage], "internal_paging_is_task": False,
        "one_stage_one_qc": True, "auto_install": False, "auto_approval": False,
        "G05_SCRIPT_human_gate": stage == "G05", "needs_work_package_approval": True,
    }


def qc_translation(*, total_source: int, total_translated: int,
                   all_ids_match: bool, all_times_match: bool) -> dict[str, Any]:
    """Q03 cannot pass if one source segment is missing, duplicated or timestamp shifted."""
    if not all(isinstance(n, int) and n >= 0 for n in (total_source, total_translated)):
        raise ValueError("segment counts must be nonnegative integers")
    if not all_ids_match or not all_times_match or total_translated > total_source:
        status = "BLOCKED"
    elif total_translated < total_source or total_source == 0:
        status = "PARTIAL"
    else:
        status = "PASS"
    return {"task_id": TASKS["G03"], "Q03_GATE_STATUS": status,
            "status": status, "total_source": total_source, "total_translated": total_translated,
            "human_read_all_segments_claimed": False,
            "note": "Structural verification only; actual ChatGPT translation must be evidenced separately"}


def qc_review(*, six_steps_complete: bool, story_facts_verified: bool,
              visual_evidence_ready: bool, human_script_approved: bool) -> dict[str, Any]:
    """One Q05; content verification precedes human G05_SCRIPT approval."""
    if not six_steps_complete or not story_facts_verified or not visual_evidence_ready:
        status = "NOT_VERIFIED"
    elif not human_script_approved:
        status = "WAITING_FOR_HUMAN_APPROVAL"
    else:
        status = "PASS"
    return {"task_id": TASKS["G05"], "Q05_GATE_STATUS": status, "status": status,
            "G05_SCRIPT_approved": bool(human_script_approved), "auto_start_G06": False}
