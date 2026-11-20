"""REVIEW_PHIM v1.3.12 — offline, stdlib-only work-package contract oracle.

It DOES NOT acquire user permission, talk to a remote machine, execute a task,
start a job, inspect source files, or schedule background work. Calling agents
must independently verify authenticated approvals and canonical Windows paths.
The module tests protocol invariants and offers an optional exclusive-file lock
in an already-approved JOB_DIR.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Consent, scope, state, or evidence contract violated."""


MAX_BATCH_INSTANCES = 400
REQUIRED_HUMAN_GATES = {
    "G05": "G05_SCRIPT",
    "G07": "G07_VOICE",
    "G10": "G10_PILOT",
}
TERMINAL = {"PACKAGE_PASS", "CANCELLED"}
PAUSED = {"PARTIAL", "WAITING_FOR_JOB", "WAITING_FOR_AUDIO_UPLOAD",
          "WAITING_FOR_HUMAN_APPROVAL", "NOT_VERIFIED", "BLOCKED", "NEEDS_FIX"}


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise ContractError(message)


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def expand_tasks(plan: dict[str, Any]) -> list[str]:
    """Expand only finite, named microtask IDs and finite batch instance ranges."""
    tasks = plan.get("task_ids", [])
    ranges = plan.get("bounded_batches", [])
    _require(isinstance(tasks, list) and isinstance(ranges, list), "task lists must be arrays")
    _require(all(isinstance(x, str) and x.startswith(("G", "P00")) and x.strip() == x and "*" not in x and "?" not in x for x in tasks), "task IDs must be explicitly bounded")
    out = list(tasks)
    for bound in ranges:
        _require(isinstance(bound, dict), "batch range must be a record")
        stem, start, end = bound.get("stem"), bound.get("start"), bound.get("end")
        _require(isinstance(stem, str) and stem.startswith(("G", "P00")) and ".B" not in stem and "*" not in stem, "invalid batch stem")
        _require(type(start) is int and type(end) is int and 1 <= start <= end <= MAX_BATCH_INSTANCES, "batch indices must be finite within cap")
        out.extend(f"{stem}.B{i:03d}" for i in range(start, end + 1))
    _require(len(out) > 0 and len(out) <= MAX_BATCH_INSTANCES, "empty or oversized work package")
    _require(len(set(out)) == len(out), "duplicate task instance")
    stages = plan.get("allowed_stages", [])
    _require(isinstance(stages, list) and len(stages) > 0, "allowed_stages missing")
    _require(all(any(task.startswith(stage + ".") for stage in stages) for task in out), "task not covered by allowed_stages")
    return out


def plan_hash(plan: dict[str, Any]) -> str:
    """SHA256 on deterministic UTF-8 JSON; no NaN, unknown installs or wildcards."""
    _require(isinstance(plan, dict), "plan must be an object")
    _require("plan_hash" not in plan, "self-referential plan hash")
    for k in ("WORK_PACKAGE_ID", "schema_version", "deviceId", "JOB_DIR", "SOURCE_MOVIE", "source_hash", "allowed_stages", "allowed_read_roots", "allowed_write_roots", "repair_budget", "human_gates", "install_budget", "allowed_executables_and_models", "expected_outputs", "acceptance_criteria", "stop_conditions"):
        _require(k in plan, f"plan missing {k}")
    _require(plan["schema_version"] == "work-package.v2", "unsupported plan schema")
    for k in ("WORK_PACKAGE_ID", "deviceId", "JOB_DIR", "SOURCE_MOVIE"):
        _require(isinstance(plan[k], str) and plan[k].strip(), f"empty {k}")
    _require(_is_digest(plan["source_hash"]) or (plan["source_hash"] == "UNKNOWN" and all(s.startswith("P00") for s in plan["allowed_stages"])), "source hash unknown beyond read-only P00")
    for k in ("allowed_read_roots", "allowed_write_roots", "human_gates", "install_budget", "allowed_executables_and_models", "expected_outputs", "acceptance_criteria", "stop_conditions"):
        _require(isinstance(plan[k], list), f"invalid {k}")
    _require(bool(plan["allowed_read_roots"]) and bool(plan["allowed_write_roots"]), "empty approved roots")
    repair = plan["repair_budget"]
    _require(isinstance(repair, dict), "repair budget not a record")
    _require(all(type(repair.get(k)) is int and 0 <= repair[k] <= (2 if k == "per_issue" else 4) for k in ("per_issue", "total")), "invalid repair cap")
    _require(repair["per_issue"] <= repair["total"], "per_issue exceeds total")
    _require(isinstance(repair.get("allowed_kinds", []), list), "repair kinds not an array")
    for installation in plan["install_budget"]:
        _require(isinstance(installation, dict) and isinstance(installation.get("id"), str), "invalid install item")
        for field in ("source", "version", "sha256", "size_bytes", "target", "license"):
            _require(field in installation and installation[field] not in ("UNKNOWN", "*", None, ""), f"unbounded install field {field}")
        _require(_is_digest(installation.get("sha256")), "installation SHA-256 missing or invalid")
        _require(type(installation.get("size_bytes")) is int and installation["size_bytes"] >= 0, "installation bytes must be a non-negative integer")
    expand_tasks(plan)
    try:
        payload = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"non-canonical plan value: {exc}") from exc
    return hashlib.sha256(payload).hexdigest()


def validate_approval(plan: dict[str, Any], approval: dict[str, Any]) -> bool:
    """Validate approval metadata; caller must verify user-message provenance."""
    _require(isinstance(approval, dict), "approval missing")
    _require(approval.get("source") == "user_message" and bool(approval.get("approval_ref")), "not an authenticated user approval record")
    _require(approval.get("action") == "APPROVE_PACKAGE", "action was not approve package")
    for k in ("WORK_PACKAGE_ID", "deviceId", "JOB_DIR"):
        _require(approval.get(k) == plan[k], f"approval mismatch: {k}")
    _require(approval.get("plan_hash") == plan_hash(plan), "approval plan hash differs")
    return True


def can_dispatch(state: dict[str, Any], task_id: str, *, session_owner: str, expected_source_hash: str | None = None) -> bool:
    """Internal checks; no user authorization is inferred by a PASS or a file."""
    if state.get("status") != "RUNNING":
        return False
    if not state.get("approval_ref") or state.get("plan_hash") != state.get("approved_plan_hash"):
        return False
    if session_owner != state.get("lock_owner"):
        return False
    if expected_source_hash is not None and state.get("source_hash") != expected_source_hash:
        return False
    if task_id not in state.get("allowed_tasks", []):
        return False
    if state.get("task_qc", {}).get(task_id) == "PASS":
        return False
    if state.get("unresolved_blockers"):
        return False
    gates = set(state.get("approved_human_gates", []))
    passed_qc = set(state.get("qc_gates_passed", []))
    if task_id.startswith("G05.") and "Q04" not in passed_qc:
        return False
    if task_id.startswith("G15.") and "Q14" not in passed_qc:
        return False
    if task_id.startswith("G15.M05") and "G15_DELETE" not in gates:
        return False
    if task_id.startswith(("G06.", "G07.", "G08.", "G09.", "G10.", "G11.", "G12.", "G13.", "G14.")) and "G05_SCRIPT" not in gates:
        return False
    if task_id.startswith("G07.M03") and "G07_VOICE" not in gates:
        return False
    if task_id.startswith(("G09.", "G10.", "G11.", "G12.", "G13.", "G14.")) and "Q08" not in passed_qc:
        return False
    if task_id.startswith(("G09.M04", "G09.M05", "G10.", "G11.", "G12.", "G13.", "G14.")) and "G07_VOICE" not in gates:
        return False
    if task_id.startswith(("G11.", "G12.", "G13.", "G14.")) and "G10_PILOT" not in gates:
        return False
    return True


def transition(state: dict[str, Any], next_status: str, *, event: str,
               same_context: bool = False, external_resolved: bool = False,
               plan: dict[str, Any] | None = None,
               approval: dict[str, Any] | None = None) -> dict[str, Any]:
    """Guard transitions; never executes work or changes approval scope."""
    old = state.get("status")
    _require(old not in TERMINAL, "terminal state immutable; new package required")
    if old == "PROPOSED" and next_status == "APPROVED":
        _require(event == "user_approved" and plan is not None and approval is not None,
                 "package proposal needs an authenticated user approval")
        validate_approval(plan, approval)
        _require(state.get("plan_hash") == plan_hash(plan), "proposal hash differs from approved plan")
        return {**state, "status": "APPROVED", "approval_ref": approval["approval_ref"],
                "approved_plan_hash": plan_hash(plan), "allowed_tasks": expand_tasks(plan)}
    _require(state.get("approval_ref") and state.get("plan_hash") == state.get("approved_plan_hash"), "no valid package approval")
    _require(next_status != old, "duplicate transition is not a new event")
    allowed = {
        "APPROVED": {"RUNNING"},
        "RUNNING": PAUSED | {"PACKAGE_PASS"},
        **{p: {"RUNNING", "CANCELLED"} for p in PAUSED},
    }
    _require(next_status in allowed.get(old, set()), f"illegal transition: {old} -> {next_status}")
    if next_status == "PACKAGE_PASS":
        _require(event == "qc_complete", "package pass requires QC event")
        _require(state.get("final_qc") is True, "independent package QC not completed")
        _require(not state.get("unresolved_blockers"), "unresolved blockers")
        allowed_tasks=state.get("allowed_tasks", [])
        _require(bool(allowed_tasks) and all(state.get("task_qc", {}).get(task) == "PASS" for task in allowed_tasks), "some internal tasks lack QC PASS")
        inferred = set(state.get("required_human_gates", []))
        for task in allowed_tasks:
            gate = REQUIRED_HUMAN_GATES.get(task[:3])
            if gate:
                inferred.add(gate)
        _require(inferred.issubset(set(state.get("approved_human_gates", []))), "human content approval missing")
    if next_status == "RUNNING" and old in PAUSED:
        _require(event == "resume" and same_context, "resume requires exact approved scope and source")
        if old in {"WAITING_FOR_HUMAN_APPROVAL", "WAITING_FOR_AUDIO_UPLOAD", "WAITING_FOR_JOB", "BLOCKED", "NOT_VERIFIED"}:
            _require(external_resolved, "external dependency not verified")
    if next_status == "RUNNING" and old == "APPROVED":
        _require(event == "start", "start requires explicit user-approved package")
    if next_status in {"WAITING_FOR_HUMAN_APPROVAL", "WAITING_FOR_AUDIO_UPLOAD"}:
        _require(event == "wait_for_external", "external wait event required")
    if next_status == "PARTIAL":
        _require(event == "checkpoint", "partial requires a durable checkpoint")
    return {**state, "status": next_status}


def repair_allowed(policy: dict[str, Any], counts: dict[str, int], issue_id: str, kind: str) -> bool:
    """Allows only named reversible kinds within both per-issue and total budgets."""
    if not policy or kind not in policy.get("allowed_kinds", []):
        return False
    per_issue=policy.get("per_issue", 0)
    total=policy.get("total", 0)
    if type(per_issue) is not int or type(total) is not int or per_issue < 0 or total < 0:
        return False
    if any(type(v) is not int or v < 0 for v in counts.values()):
        return False
    return counts.get(issue_id, 0) < per_issue and sum(counts.values()) < total


def event_id(package_id: str, approved_plan_hash: str, task_id: str,
             input_hashes: dict[str, str], attempt: int) -> str:
    """Deterministic deduplication key for one attempt; not an approval token."""
    _require(bool(package_id) and bool(task_id) and _is_digest(approved_plan_hash), "invalid event identity")
    _require(type(attempt) is int and attempt >= 1, "attempt must be >=1")
    _require(isinstance(input_hashes, dict) and all(isinstance(k,str) and _is_digest(v) for k,v in input_hashes.items()), "invalid input hash set")
    data={"WORK_PACKAGE_ID":package_id,"plan_hash":approved_plan_hash,
          "task_id":task_id,"input_hashes":input_hashes,"attempt":attempt}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",", ":"),ensure_ascii=False).encode("utf-8")).hexdigest()


def import_legacy_evidence(tasks: list[dict[str, Any]], *, expected_source_hash: str) -> dict[str, Any]:
    """Non-destructively classify old task evidence; never authorizes a new scope."""
    verified, not_verified = [], []
    for task in tasks:
        id_=task.get("task_id", "UNKNOWN")
        if (task.get("QC_STATUS") == "PASS" and task.get("source_hash") == expected_source_hash
                and task.get("evidence_exists") is True and task.get("evidence_hash_valid") is True and bool(task.get("approval_ref"))):
            verified.append(id_)
        else:
            not_verified.append(id_)
    return {"verified_evidence": verified, "not_verified": not_verified, "authorizes_new_package": False}


def acquire_lock(path: Path, *, owner: str, package_id: str, plan_hash: str, device_id: str = "UNKNOWN") -> None:
    """Atomic exclusive creation; caller must put path inside an approved JOB_DIR.

    An existing lock is always a blocker, even if apparently stale; inspect it
    and the originating job before an explicitly authorized recovery.
    """
    _require(bool(owner) and bool(package_id) and bool(device_id) and _is_digest(plan_hash), "lock metadata invalid")
    path=Path(path)
    _require(path.parent.is_dir() and not path.parent.is_symlink() and not path.is_symlink(),
             "lock path must not be a symlink or outside canonical JOB_DIR")
    fd=None
    try:
        fd=os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        data=json.dumps({"owner_run_id":owner,"owner":owner,"package_id":package_id,"deviceId":device_id,"plan_hash":plan_hash},sort_keys=True).encode("utf-8")
        os.write(fd,data)
        os.fsync(fd)
    except FileExistsError as exc:
        raise ContractError("another session owns work-package lock; do not auto-steal") from exc
    except Exception:
        if fd is not None:
            try:os.unlink(path)
            except OSError:pass
        raise
    finally:
        if fd is not None:
            os.close(fd)


def release_lock(path: Path, *, owner: str) -> None:
    """Release only own lock; no stale lock takeovers and no process killing."""
    path=Path(path)
    _require(not path.is_symlink() and not path.parent.is_symlink(), "lock path is a symlink")
    try:
        current=json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContractError("lock cannot be verified") from exc
    _require(current.get("owner") == owner, "lock belongs to another session")
    path.unlink()
