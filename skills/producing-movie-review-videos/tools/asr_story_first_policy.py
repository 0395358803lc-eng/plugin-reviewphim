"""Pure-stdlib offline ASR issue triage for REVIEW_PHIM STORY_FIRST (v1.3.13).

This does NOT transcribe audio, hear clips, change original transcripts, modify QC
checkpoints or approve the workflow. Run only in an approved task/scope. It emits
an advisory JSON report for review by the main workflow.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any


MINOR_NONBLOCKING = "MINOR_NONBLOCKING"
MATERIAL_REVIEW = "MATERIAL_REVIEW"
MATERIAL_BLOCKER = "MATERIAL_BLOCKER"


def classify(candidate: dict[str, Any]) -> dict[str, Any]:
    """Classify the *story consequence* of an ASR issue, not its word count.

    Input story_role and event links must be independently supplied from review
    context; this module never invents a label or claims it heard the clip.
    """
    if not isinstance(candidate, dict):
        raise TypeError("candidate must be a dict")
    sid = candidate.get("segment_id")
    if not isinstance(sid, str) or not sid.strip():
        raise ValueError("candidate requires segment_id")

    role = candidate.get("story_role", "unknown")
    if role not in {"core", "peripheral", "unknown"}:
        raise ValueError("story_role must be core/peripheral/unknown")

    flags = list(candidate.get("flags") or [])
    if not all(isinstance(f, str) for f in flags):
        raise ValueError("flags must be list of strings")

    used = bool(candidate.get("used_in_review", False))
    linked = bool(candidate.get("linked_key_event", False))
    unverified = bool(candidate.get("unverified", True))
    raw_preserved = candidate.get("raw_preserved") is True
    missing_source = candidate.get("source_missing") is True
    material_gap = candidate.get("material_audio_gap") is True
    high_impact = candidate.get("plot_contradiction") is True

    if not raw_preserved or missing_source or material_gap or high_impact:
        impact = MATERIAL_BLOCKER
        reason = "Missing/unpreserved source, material story gap or plot contradiction"
    elif unverified and (role == "core" or used or linked):
        impact = MATERIAL_BLOCKER
        reason = "Unverified content could affect a material review claim"
    elif role == "unknown":
        impact = MATERIAL_REVIEW
        reason = "Narrative relevance must be assessed in grouped context"
    elif unverified and role == "peripheral" and not used and not linked:
        impact = MINOR_NONBLOCKING
        reason = "Ancillary unverified candidate; exclude from review, preserve as warning"
    else:
        impact = "NO_RELEVANT_ISSUE"
        reason = "No unresolved material issue indicated by supplied metadata"

    return {
        "segment_id": sid,
        "impact_classification": impact,
        "reason": reason,
        "warning_codes": flags,
        "may_quote_in_review": (not unverified) and impact == "NO_RELEVANT_ISSUE",
        "must_preserve_original": True,
        "heard_verified": False,  # No automatic inference or listening here.
        "original_text": candidate.get("text_original", ""),
    }


def summarize(
    candidates: list[dict[str, Any]], *,
    total_raw_candidates: int,
    full_film_coverage: bool,
    source_hash_ok: bool,
    missing_batch: bool = False,
    critical_story_events_verified: bool = False,
) -> dict[str, Any]:
    if total_raw_candidates < 0:
        raise ValueError("total_raw_candidates must be >= 0")
    if not isinstance(candidates, list):
        raise TypeError("candidates must be list")
    outcomes = [classify(s) for s in candidates]
    ids = [x["segment_id"] for x in outcomes]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate IDs must be unique")
    minor = [x["segment_id"] for x in outcomes if x["impact_classification"] == MINOR_NONBLOCKING]
    material = [x["segment_id"] for x in outcomes if x["impact_classification"] == MATERIAL_REVIEW]
    blockers = [x["segment_id"] for x in outcomes if x["impact_classification"] == MATERIAL_BLOCKER]
    # The minimum of two is an efficiency cap for short window batches, not
    # permission to omit two plot-changing claims.
    tolerance = max(2, math.ceil(0.02 * total_raw_candidates))
    if not source_hash_ok or missing_batch:
        batch_status = MATERIAL_BLOCKER
        blockers.append("SOURCE_HASH_OR_BATCH_MISSING")
    elif blockers:
        batch_status = MATERIAL_BLOCKER
    elif material or len(minor) > tolerance:
        batch_status = MATERIAL_REVIEW
    elif minor:
        batch_status = "PASS_WITH_WARNINGS"
    else:
        batch_status = "PASS"

    # No claim that a single 10-min batch is enough for the full movie.
    q02 = ("PASS" if batch_status in {"PASS", "PASS_WITH_WARNINGS"}
           and full_film_coverage and critical_story_events_verified
           and source_hash_ok and not missing_batch else "NOT_VERIFIED")

    return {
        "schema_version": "story-first-asr-triage.v1",
        "quality_mode": "STORY_FIRST",
        "batch_status": batch_status,
        "Q02_GATE_STATUS": q02,
        "TECHNICAL_QC": "PASS" if source_hash_ok and not missing_batch else "BLOCKED",
        "STORY_QC": "PROVISIONAL" if q02 != "PASS" else "PASS_WITH_WARNINGS" if minor else "PASS",
        "total_raw_candidates": total_raw_candidates,
        "triaged_count": len(outcomes),
        "minor_tolerance_count": tolerance,
        "minor_count": len(minor),
        "ignored_in_review_segment_ids": minor,
        "material_review_ids": material,
        "blocking_issue_ids": blockers,
        "requires_user_audio_upload_for_minor": False,
        "requires_explicit_next_work_package_approval": True,
        "heard_verified": False,
        "candidate_outcomes": outcomes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", help="approved local JSON: {candidates, total_raw_candidates, ...}")
    args = parser.parse_args(argv)
    with open(args.input_json, encoding="utf-8") as f:
        request = json.load(f)
    data = summarize(
        request["candidates"],
        total_raw_candidates=request["total_raw_candidates"],
        full_film_coverage=request.get("full_film_coverage", False),
        source_hash_ok=request.get("source_hash_ok", False),
        missing_batch=request.get("missing_batch", False),
        critical_story_events_verified=request.get("critical_story_events_verified", False),
    )
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
