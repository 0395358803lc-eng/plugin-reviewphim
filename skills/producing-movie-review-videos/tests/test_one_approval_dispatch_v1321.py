"""One-click activation contract tests, independent of remote device I/O.

The shim mirrors the established work_package_state.py API while the installed
plugin supplies the actual core module. No test performs remote operations.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class ContractError(ValueError):
    pass


def canonical_plan_hash(plan):
    if "plan_hash" in plan:
        raise ContractError("self-reference")
    return hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def core_fixture():
    core = types.ModuleType("work_package_state")
    core.ContractError = ContractError
    core.plan_hash = canonical_plan_hash

    def validate_approval(plan, approval):
        if not isinstance(approval, dict) or approval.get("source") != "user_message" or not approval.get("approval_ref") or approval.get("action") != "APPROVE_PACKAGE":
            raise ContractError("not an authenticated approval")
        for key in ("WORK_PACKAGE_ID", "deviceId", "JOB_DIR"):
            if approval.get(key) != plan.get(key):
                raise ContractError("approval mismatch")
        if approval.get("plan_hash") != canonical_plan_hash(plan):
            raise ContractError("hash mismatch")
        return True

    def transition(state, next_status, *, event, plan=None, approval=None, **kwargs):
        if state.get("status") == "PROPOSED" and next_status == "APPROVED":
            if event != "user_approved" or plan is None or approval is None:
                raise ContractError("approval required")
            validate_approval(plan, approval)
            return {**state, "status": "APPROVED", "approval_ref": approval["approval_ref"],
                    "approved_plan_hash": canonical_plan_hash(plan), "allowed_tasks": plan["task_ids"]}
        if state.get("status") == "APPROVED" and next_status == "RUNNING":
            if event != "start" or not state.get("approval_ref") or state.get("plan_hash") != state.get("approved_plan_hash"):
                raise ContractError("start without approval")
            return {**state, "status": "RUNNING"}
        raise ContractError("illegal transition")

    def acquire_lock(path, *, owner, package_id, plan_hash, device_id):
        try:
            with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
                json.dump({"owner": owner, "package_id": package_id, "plan_hash": plan_hash, "deviceId": device_id}, f)
        except FileExistsError as exc:
            raise ContractError("lock owned by another session") from exc

    def release_lock(path, *, owner):
        data = json.loads(Path(path).read_text())
        if data["owner"] != owner:
            raise ContractError("wrong lock owner")
        Path(path).unlink()

    core.validate_approval = validate_approval
    core.transition = transition
    core.acquire_lock = acquire_lock
    core.release_lock = release_lock
    return core


@pytest.fixture
def env(tmp_path, monkeypatch):
    core = core_fixture()
    monkeypatch.setitem(sys.modules, "work_package_state", core)
    module_path = ROOT / "tools" / "one_approval_dispatch_v1321.py"
    spec = importlib.util.spec_from_file_location("one_approval_dispatch_v1321", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    job = tmp_path / "JOB_DIR"
    (job / "logs").mkdir(parents=True)
    plan = {
        "schema_version": "work-package.v2", "WORK_PACKAGE_ID": "WP-1321-TEST",
        "deviceId": "device-verified", "JOB_DIR": str(job),
        "SOURCE_MOVIE": str(tmp_path / "movie.mp4"), "source_hash": "a" * 64,
        "allowed_stages": ["G01"], "task_ids": ["G01.SOURCE.FULL"],
        "bounded_batches": [], "allowed_read_roots": [str(tmp_path)],
        "allowed_write_roots": [str(job)], "allowed_executables_and_models": [],
        "install_budget": [], "repair_budget": {"per_issue": 0, "total": 0, "allowed_kinds": []},
        "expected_outputs": [], "acceptance_criteria": [], "stop_conditions": [], "human_gates": [],
    }
    digest = canonical_plan_hash(plan)
    state = {"status": "PROPOSED", "plan_hash": digest, "source_hash": plan["source_hash"],
             "deviceId": plan["deviceId"], "JOB_DIR": plan["JOB_DIR"], "approved_human_gates": []}
    approval = {"source": "user_message", "approval_ref": "actual-user-turn",
                "action": "APPROVE_PACKAGE", "WORK_PACKAGE_ID": plan["WORK_PACKAGE_ID"],
                "deviceId": plan["deviceId"], "JOB_DIR": str(job), "plan_hash": digest}
    lock = job / "logs" / "work_package.lock"
    kwargs = dict(owner="session-1", lock_path=lock,
                  observed_device_id=plan["deviceId"], observed_source_hash=plan["source_hash"])
    return module, plan, state, approval, kwargs


def test_single_approval_enters_running_directly(env):
    module, plan, state, approval, kwargs = env
    out = module.approve_and_start(state, plan, approval, **kwargs)
    assert out["outcome"] == "STARTED" and out["dispatch_now"] is True
    assert out["state"]["status"] == "RUNNING"
    assert out["state"]["lock_verified"] is True
    assert out["state"]["approved_plan_hash"] == state["plan_hash"]
    assert out["state"]["approved_human_gates"] == []  # cannot preapprove future human decisions
    assert kwargs["lock_path"].is_file()


def test_second_click_does_not_run_again(env):
    module, plan, state, approval, kwargs = env
    out = module.approve_and_start(state, plan, approval, **kwargs)
    repeated = module.approve_and_start(out["state"], plan, approval, **kwargs)
    assert repeated["outcome"] == "ALREADY_RUNNING"
    assert repeated["dispatch_now"] is False


def test_wrong_plan_hash_is_blocked(env):
    module, plan, state, approval, kwargs = env
    approval["plan_hash"] = "f" * 64
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)
    assert not kwargs["lock_path"].exists()


def test_device_preflight_mismatch_is_blocked(env):
    module, plan, state, approval, kwargs = env
    kwargs["observed_device_id"] = "different-machine"
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)
    assert not kwargs["lock_path"].exists()


def test_source_hash_mismatch_is_blocked(env):
    module, plan, state, approval, kwargs = env
    kwargs["observed_source_hash"] = "b" * 64
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)


def test_wrong_job_root_is_blocked(env, tmp_path):
    module, plan, state, approval, kwargs = env
    outside = tmp_path / "outside" / "logs"
    outside.mkdir(parents=True)
    kwargs["lock_path"] = outside / "work_package.lock"
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)
    assert not kwargs["lock_path"].exists()


def test_existing_lock_is_not_stolen(env):
    module, plan, state, approval, kwargs = env
    kwargs["lock_path"].write_text('other-session')
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)
    assert kwargs["lock_path"].read_text() == 'other-session'


def test_missing_human_message_rejected(env):
    module, plan, state, approval, kwargs = env
    approval["source"] = "tool_output"
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)


def test_non_running_terminal_state_not_restarted(env):
    module, plan, state, approval, kwargs = env
    state["status"] = "PACKAGE_PASS"
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)


def test_previous_approved_package_enters_running_without_new_gate(env):
    module, plan, state, approval, kwargs = env
    old = module.transition(state, "APPROVED", event="user_approved", plan=plan, approval=approval)
    result = module.approve_and_start(old, plan, approval, **kwargs)
    assert result["outcome"] == "STARTED"
    assert result["state"]["status"] == "RUNNING"


def test_wrong_approval_for_previous_approved_state_blocked(env):
    module, plan, state, approval, kwargs = env
    old = module.transition(state, "APPROVED", event="user_approved", plan=plan, approval=approval)
    approval["approval_ref"] = "different-turn"
    with pytest.raises(ContractError):module.approve_and_start(old, plan, approval, **kwargs)


def test_existing_running_other_plan_is_blocked(env):
    module, plan, state, approval, kwargs = env
    state["status"] = "RUNNING"
    state["approved_plan_hash"] = "0" * 64
    state["approval_ref"] = "turn-old"
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)


def test_missing_owner_blocked(env):
    module, plan, state, approval, kwargs = env
    kwargs["owner"] = ""
    with pytest.raises(ContractError):module.approve_and_start(state, plan, approval, **kwargs)


def test_v1323_validator_blocks_microtask_before_work_package_lock(env):
    module, plan, state, approval, kwargs = env
    plan['allowed_stages']=['G04']
    plan['task_ids']=['G04.M01']
    digest=canonical_plan_hash(plan)
    state['plan_hash']=digest
    approval['plan_hash']=digest
    with pytest.raises(ContractError, match='v1.3.23 package scope rejected'):
        module.approve_and_start(state,plan,approval,**kwargs)
    assert not kwargs['lock_path'].exists()
