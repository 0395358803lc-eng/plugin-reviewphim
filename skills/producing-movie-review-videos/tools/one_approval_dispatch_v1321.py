"""One REVIEW_PHIM package approval activates its existing work-package state.

This is an offline contract helper, NOT an autonomous worker. Real ChatGPT/remote
orchestrators must authenticate approval provenance, verify filesystem/remote
state and run only approved commands AFTER the function returns STARTED.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from work_package_state import (
    ContractError, acquire_lock, plan_hash, release_lock, transition, validate_approval,
)


def approve_and_start(
    state: dict[str, Any],
    plan: dict[str, Any],
    approval: dict[str, Any],
    *,
    owner: str,
    lock_path: Path,
    observed_device_id: str,
    observed_source_hash: str,
) -> dict[str, Any]:
    """One authenticated APPROVE_PACKAGE → APPROVED → RUNNING, no second UI gate.

    Caller must independently confirm the actual user message, canonical remote
    paths, approved executable set, permissions and source checksum. The approved
    JOB_DIR/logs must already exist; this does not create job directories.
    """
    if not owner or not isinstance(owner, str):
        raise ContractError("owner run id required")
    # v1.3.23: validate unified atomic stage scope before an approval can enter
    # RUNNING. This is a source policy check; it does not run remote tasks.
    from importlib.util import module_from_spec, spec_from_file_location
    gate_path = Path(__file__).with_name('workflow_integrity_v1323.py')
    spec = spec_from_file_location('workflow_integrity_v1323', gate_path)
    if spec is None or spec.loader is None:
        raise ContractError('v1.3.23 workflow integrity validator unavailable')
    gate_module = module_from_spec(spec)
    spec.loader.exec_module(gate_module)
    try:
        gate_module.validate_new_package(plan)
        # v1.3.25 Production First: the above delegates to finite stage and
        # creative-delegation validation without creating aesthetic QC gates.
    except ValueError as exc:
        raise ContractError(f'v1.3.23 package scope rejected: {exc}') from exc
    actual_hash = plan_hash(plan)
    if observed_device_id != plan["deviceId"] or observed_source_hash != plan["source_hash"]:
        raise ContractError("device/source preflight mismatch")
    if state.get("plan_hash") != actual_hash:
        raise ContractError("state and plan hash mismatch")
    if state.get("source_hash") not in (None, observed_source_hash):
        raise ContractError("state source mismatch")
    if state.get("deviceId") not in (None, observed_device_id):
        raise ContractError("state device mismatch")
    if state.get("JOB_DIR") not in (None, plan["JOB_DIR"]):
        raise ContractError("state job directory mismatch")
    # Do not accept a repeated or made-up click as authority to execute again.
    if state.get("status") == "RUNNING":
        if state.get("approved_plan_hash") != actual_hash or not state.get("approval_ref"):
            raise ContractError("running job does not match approved package")
        return {"outcome": "ALREADY_RUNNING", "state": dict(state), "dispatch_now": False}
    if state.get("status") not in ("PROPOSED", "APPROVED"):
        raise ContractError("package is not eligible for initial start; use guarded resume")
    validate_approval(plan, approval)
    lock_path = Path(lock_path)
    job_dir = Path(plan["JOB_DIR"])
    if (lock_path.name != "work_package.lock" or lock_path.parent.name != "logs"
            or lock_path.parent.parent.resolve(strict=True) != job_dir.resolve(strict=True)
            or lock_path.parent.is_symlink()):
        raise ContractError("lock must be in approved JOB_DIR/logs")
    if state["status"] == "PROPOSED":
        approved = transition(state, "APPROVED", event="user_approved", plan=plan, approval=approval)
    else:
        if state.get("approval_ref") != approval["approval_ref"] or state.get("approved_plan_hash") != actual_hash:
            raise ContractError("previous APPROVED state is not the same approval")
        approved = dict(state)
    # Acquire before RUNNING, and never steal another process's lock.
    acquire_lock(lock_path, owner=owner, package_id=plan["WORK_PACKAGE_ID"],
                 plan_hash=actual_hash, device_id=plan["deviceId"])
    try:
        # Do not mark a lock verified just because our acquire function returned.
        # Read the actual metadata and bind it to this approval and device.
        import json
        lock_record = json.loads(lock_path.read_text(encoding="utf-8"))
        if not all((lock_record.get("owner") == owner,
                    lock_record.get("package_id") == plan["WORK_PACKAGE_ID"],
                    lock_record.get("deviceId") == plan["deviceId"],
                    lock_record.get("plan_hash") == actual_hash)):
            raise ContractError("newly created work-package lock metadata mismatch")
        running = transition({**approved, "lock_owner": owner}, "RUNNING", event="start")
        running = {**running, "lock_verified": True}
    except Exception:
        release_lock(lock_path, owner=owner)
        raise
    return {"outcome": "STARTED", "state": running, "dispatch_now": True}
