"""REVIEW_PHIM 1.3.22: offline plan/QC contract helper; no task execution.

Metadata predicates do not prove ChatGPT viewed/heard media or searched the web.
The caller must verify actual file contents, media inspection, approvals and hashes.
"""
from __future__ import annotations

from typing import Any

ATOMIC_TASKS = {
    "G04": "G04.FILM.UNDERSTANDING.FULL",
    "G05": "G05.REVIEW.FULL",
}


def _task_stage(task_id: str) -> str:
    if not isinstance(task_id, str):
        raise ValueError("task id must be a string")
    return task_id.split(".", 1)[0]


def validate_stage_tasks(task_ids: list[str], bounded_batches: list[dict[str, Any]],
                         allowed_stages: list[str]) -> dict[str, str]:
    """Reject new G04/G05 microtask or batch approvals; other stages untouched.

    Call alongside the existing work-package v2 plan/hash checks BEFORE presenting
    a new approval or dispatching a newly approved package. Not for legacy imports.
    """
    if not isinstance(task_ids, list) or not isinstance(bounded_batches, list) or not isinstance(allowed_stages, list):
        raise ValueError("task_ids, bounded_batches and allowed_stages must be lists")
    for batch in bounded_batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("stem"), str):
            raise ValueError("malformed bounded batch")
        if _task_stage(batch["stem"]) in ATOMIC_TASKS:
            raise ValueError("G04/G05 internal batches must not become work-package tasks")
    result: dict[str, str] = {}
    for task in task_ids:
        stage = _task_stage(task)
        if stage not in ATOMIC_TASKS:
            continue
        if task != ATOMIC_TASKS[stage] or stage in result:
            raise ValueError(f"{stage} must have exactly one atomic task: {ATOMIC_TASKS[stage]}")
        result[stage] = task
    for stage in ATOMIC_TASKS:
        if stage in allowed_stages and stage not in result:
            raise ValueError(f"{stage} requires {ATOMIC_TASKS[stage]}")
    return result


def g04_readiness(report: dict[str, Any]) -> str:
    """Conservative QC metadata validation for one Q04, not visual perception."""
    if not isinstance(report, dict) or report.get("film_evidence_exists") is not True:
        return "BLOCKED"
    if report.get("scene_index_start_end") is not True:
        return "NOT_VERIFIED"
    events = report.get("core_events")
    if not isinstance(events, list) or not events:
        return "NOT_VERIFIED"
    core = [e for e in events if isinstance(e, dict) and e.get("importance") == "CORE"]
    if not core:
        return "NOT_VERIFIED"
    if report.get("unresolved_core_claims"):
        return "NEEDS_REVIEW"
    for event in core:
        if (not event.get("event_id") or event.get("media_inspected") is not True
                or event.get("status") not in {"VERIFIED_VISUAL", "VERIFIED_MULTIMODAL"}):
            return "NOT_VERIFIED"
    return "PASS"


def g05_readiness(report: dict[str, Any]) -> str:
    """Confirm a single Q05 and preserve the independent G05_SCRIPT human gate."""
    if not isinstance(report, dict) or report.get("g04_status") != "PASS":
        return "BLOCKED"
    if report.get("web_crosscheck") not in {"PASS", "PASS_WITH_WARNINGS"}:
        return "NOT_VERIFIED"
    if (report.get("review_complete") is not True or report.get("narrative_only") != "PASS"
            or report.get("story_evidence") != "PASS" or report.get("q05_count") != 1):
        return "NEEDS_FIX"
    return "PASS" if report.get("human_approval_g05_script") is True else "WAITING_FOR_HUMAN_APPROVAL"
