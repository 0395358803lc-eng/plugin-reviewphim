"""Behavioral simulation for REVIEW_PHIM's consent-bound work package protocol."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from work_package_state import (
    ContractError,
    plan_hash,
    validate_approval,
    expand_tasks,
    can_dispatch,
    transition,
    repair_allowed,
    acquire_lock,
    release_lock,
    import_legacy_evidence,
    event_id,
)


def plan():
    return {
        "WORK_PACKAGE_ID": "G03.PKG01",
        "schema_version": "work-package.v2",
        "deviceId": "device-1",
        "JOB_DIR": "D:\\Film\\REVIEW_PHIM_WORKSPACE\\film-1",
        "SOURCE_MOVIE": "D:\\Film\\movie.mkv",
        "source_hash": "a" * 64,
        "allowed_stages": ["G03"],
        "task_ids": ["G03.M01", "G03.M04"],
        "bounded_batches": [{"stem": "G03.M02", "start": 1, "end": 3},
                            {"stem": "G03.M03", "start": 1, "end": 3}],
        "allowed_read_roots": ["D:\\Film"],
        "allowed_write_roots": ["D:\\Film\\REVIEW_PHIM_WORKSPACE\\film-1"],
        "install_budget": [],
        "allowed_executables_and_models": [],
        "expected_outputs": ["analysis/transcript_vi.jsonl"],
        "acceptance_criteria": ["all segment hashes verified"],
        "stop_conditions": ["scope mismatch", "human gate missing"],
        "repair_budget": {"per_issue": 2, "total": 4, "allowed_kinds": ["json_format", "batch_merge"]},
        "human_gates": [],
    }


def state(*, stage="G03", tasks=None, status="RUNNING", human=None):
    p = plan()
    p["allowed_stages"] = [stage]
    p["task_ids"] = tasks or [f"{stage}.M01"]
    p["bounded_batches"] = []
    return {
        "status": status,
        "WORK_PACKAGE_ID": p["WORK_PACKAGE_ID"],
        "plan_hash": plan_hash(p),
        "approved_plan_hash": plan_hash(p),
        "approval_ref": "user-message-123",
        "deviceId": p["deviceId"],
        "JOB_DIR": p["JOB_DIR"],
        "source_hash": p["source_hash"],
        "allowed_tasks": expand_tasks(p),
        "task_qc": {},
        "required_human_gates": human if human is not None else [],
        "approved_human_gates": [],
        "unresolved_blockers": [],
        "final_qc": False,
        "lock_owner": "session-1",
    }


class PlanContractTests(unittest.TestCase):
    def test_digest_stable_regardless_of_dict_insertion_order(self):
        p=plan();q=json.loads(json.dumps(p,ensure_ascii=False));q=dict(reversed(list(q.items())))
        self.assertEqual(plan_hash(p), plan_hash(q))
        self.assertEqual(len(plan_hash(p)), 64)

    def test_reject_unknown_or_open_ended_batch_and_invalid_budget(self):
        for bad in ({"stem":"G03.M02","start":1,"end":"*"},
                    {"stem":"G03.M02","start":1,"end":5000}):
            p=plan();p["bounded_batches"]=[bad]
            with self.assertRaises(ContractError):expand_tasks(p)
        p=plan();p["install_budget"]=[{"id":"A04","source":"UNKNOWN"}]
        with self.assertRaises(ContractError):plan_hash(p)

    def test_install_budget_needs_bounded_hash_bytes_license_and_source(self):
        p=plan()
        p["install_budget"]=[{"id":"A04","source":"https://example.org/pkg.whl","version":"1.2.1","sha256":"a"*64,"size_bytes":-1,"target":"tools/pkg","license":"MIT"}]
        with self.assertRaises(ContractError):plan_hash(p)
        p["install_budget"][0]["size_bytes"]=100
        self.assertEqual(len(plan_hash(p)),64)
        p["repair_budget"]={"per_issue":3,"total":10,"allowed_kinds":["format"]}
        with self.assertRaises(ContractError):plan_hash(p)

    def test_approval_requires_exact_user_record_and_scope_hash(self):
        p=plan();digest=plan_hash(p)
        a={"action":"APPROVE_PACKAGE","source":"user_message","approval_ref":"msg-1", "WORK_PACKAGE_ID":"G03.PKG01","plan_hash":digest,"deviceId":"device-1","JOB_DIR":p["JOB_DIR"]}
        self.assertTrue(validate_approval(p,a))
        for key,bad in [("plan_hash","0"*64),("deviceId","wrong-device"),("source","assistant")]:
            altered={**a,key:bad}
            with self.assertRaises(ContractError):validate_approval(p,altered)

    def test_approved_scope_allows_only_finite_batch_instances(self):
        ids=expand_tasks(plan())
        self.assertIn("G03.M02.B003",ids)
        self.assertNotIn("G03.M02.B004",ids)
        self.assertEqual(len(ids),8)


class ExecutionContractTests(unittest.TestCase):
    def test_authorization_from_proposed_to_approved_requires_user_provenance(self):
        p=plan();digest=plan_hash(p)
        s=state(status="PROPOSED")
        s.pop("approval_ref",None)
        s.pop("approved_plan_hash",None)
        s["plan_hash"]=digest
        with self.assertRaises(ContractError):transition(s,"APPROVED",event="user_approved")
        a={"action":"APPROVE_PACKAGE","source":"user_message","approval_ref":"user-msg-234", "WORK_PACKAGE_ID":p["WORK_PACKAGE_ID"],"plan_hash":digest,"deviceId":p["deviceId"],"JOB_DIR":p["JOB_DIR"]}
        z=transition(s,"APPROVED",event="user_approved",plan=p,approval=a)
        self.assertEqual(z["approval_ref"],"user-msg-234")
        self.assertEqual(transition(z,"RUNNING",event="start")["status"],"RUNNING")

    def test_g05_requires_film_understanding_ready(self):
        s=state(stage="G05",tasks=["G05.M01"])
        self.assertFalse(can_dispatch(s,"G05.M01",session_owner="session-1"))
        s["qc_gates_passed"]=["Q04"]
        self.assertTrue(can_dispatch(s,"G05.M01",session_owner="session-1"))

    def test_g15_requires_g14_qc_and_delete_needs_independent_approval(self):
        s=state(stage="G15",tasks=["G15.M03","G15.M05"])
        self.assertFalse(can_dispatch(s,"G15.M03",session_owner="session-1"))
        s["qc_gates_passed"]=["Q14"]
        self.assertTrue(can_dispatch(s,"G15.M03",session_owner="session-1"))
        self.assertFalse(can_dispatch(s,"G15.M05",session_owner="session-1"))
        s["approved_human_gates"]=["G15_DELETE"]
        self.assertTrue(can_dispatch(s,"G15.M05",session_owner="session-1"))

    def test_dispatch_uses_qc_and_no_implicit_extra_tasks(self):
        s=state(tasks=["G03.M01","G03.M04"])
        self.assertTrue(can_dispatch(s,"G03.M01",session_owner="session-1"))
        s["task_qc"]["G03.M01"]="PASS"
        self.assertFalse(can_dispatch(s,"G03.M01",session_owner="session-1"))
        self.assertFalse(can_dispatch(s,"G03.M99",session_owner="session-1"))
        self.assertFalse(can_dispatch(s,"G03.M04",session_owner="session-2"))
        s["source_hash"]="0"*64
        self.assertFalse(can_dispatch(s,"G03.M04",session_owner="session-1",expected_source_hash="a"*64))

    def test_no_package_pass_if_any_qc_or_human_gate_missing(self):
        s=state(stage="G05",tasks=["G05.M01"],human=["G05_SCRIPT"])
        s["task_qc"]={"G05.M01":"PASS"};s["final_qc"]=True
        with self.assertRaises(ContractError):transition(s,"PACKAGE_PASS",event="qc_complete")
        s["approved_human_gates"]=["G05_SCRIPT"]
        x=transition(s,"PACKAGE_PASS",event="qc_complete")
        self.assertEqual(x["status"],"PACKAGE_PASS")
        with self.assertRaises(ContractError):transition(x,"RUNNING",event="resume")

    def test_g07_g10_both_require_explicit_user_approval(self):
        for g,gate in [("G07","G07_VOICE"),("G10","G10_PILOT")]:
            s=state(stage=g,tasks=[g+".M01"])
            s["task_qc"]={g+".M01":"PASS"};s["final_qc"]=True
            with self.assertRaises(ContractError):transition(s,"PACKAGE_PASS",event="qc_complete")
            s["approved_human_gates"]=[gate]
            self.assertEqual(transition(s,"PACKAGE_PASS",event="qc_complete")["status"],"PACKAGE_PASS")

    def test_pause_and_resume_same_approval_without_escalation(self):
        s=state(tasks=["G03.M01","G03.M04"])
        paused=transition(s,"PARTIAL",event="checkpoint")
        resumed=transition(paused,"RUNNING",event="resume", same_context=True)
        self.assertEqual(resumed["approval_ref"],s["approval_ref"])
        self.assertEqual(resumed["allowed_tasks"],s["allowed_tasks"])
        with self.assertRaises(ContractError):transition(paused,"RUNNING",event="resume",same_context=False)

    def test_waiting_for_human_and_audio_does_not_auto_approve(self):
        for wait in ("WAITING_FOR_HUMAN_APPROVAL","WAITING_FOR_AUDIO_UPLOAD"):
            s=state();paused=transition(s,wait,event="wait_for_external")
            with self.assertRaises(ContractError):transition(paused,"RUNNING",event="resume",same_context=True,external_resolved=False)
            self.assertEqual(transition(paused,"RUNNING",event="resume",same_context=True,external_resolved=True)["status"],"RUNNING")

    def test_dispatch_requires_human_and_stage_qc_gates(self):
        s=state(stage="G06",tasks=["G06.M01"])
        self.assertFalse(can_dispatch(s,"G06.M01",session_owner="session-1"))
        s["approved_human_gates"]=["G05_SCRIPT"]
        self.assertTrue(can_dispatch(s,"G06.M01",session_owner="session-1"))
        s=state(stage="G09",tasks=["G09.M01"])
        s["approved_human_gates"]=["G05_SCRIPT","G07_VOICE"]
        self.assertFalse(can_dispatch(s,"G09.M01",session_owner="session-1"))
        s["qc_gates_passed"]=["Q08"]
        self.assertTrue(can_dispatch(s,"G09.M01",session_owner="session-1"))

    def test_no_delete_implied_by_delivery_pass(self):
        s=state(stage="G15",tasks=["G15.M03"])
        s["task_qc"]={"G15.M03":"PASS"};s["final_qc"]=True
        self.assertEqual(transition(s,"PACKAGE_PASS",event="qc_complete")["status"],"PACKAGE_PASS")
        self.assertFalse(can_dispatch(s,"G15.M05",session_owner="session-1"))


class RepairAndResumeTests(unittest.TestCase):
    def test_repair_budget_is_both_per_issue_and_total_limited(self):
        policy=plan()["repair_budget"]
        self.assertTrue(repair_allowed(policy,{"ISSUE-1":1,"ISSUE-2":1},"ISSUE-1","json_format"))
        self.assertFalse(repair_allowed(policy,{"ISSUE-1":2},"ISSUE-1","json_format"))
        self.assertFalse(repair_allowed(policy,{"ISSUE-1":1,"ISSUE-2":3},"ISSUE-3","json_format"))
        self.assertFalse(repair_allowed(policy,{},"ISSUE-1","download_model"))

    def test_event_id_deduplicates_same_task_attempt_without_conflating_retry(self):
        input_hashes={"audio":"a"*64,"scene":"b"*64}
        v=event_id("G03.PKG01","a"*64,"G03.M02.B001",input_hashes,1)
        self.assertEqual(v,event_id("G03.PKG01","a"*64,"G03.M02.B001",dict(reversed(list(input_hashes.items()))),1))
        self.assertNotEqual(v,event_id("G03.PKG01","a"*64,"G03.M02.B001",input_hashes,2))
        self.assertEqual(len(v),64)

    def test_legacy_import_never_authenticates_or_auto_approves(self):
        s_hash="a"*64
        legacy=[{"task_id":"G03.M01","QC_STATUS":"PASS","source_hash":s_hash,"evidence_exists":True,"evidence_hash_valid":True,"approval_ref":"old-msg"},
                {"task_id":"G03.M02.B001","QC_STATUS":"PASS","source_hash":s_hash,"evidence_exists":False,"evidence_hash_valid":False,"approval_ref":"old-msg"},
                {"task_id":"G03.M04","QC_STATUS":"NEEDS_FIX","source_hash":s_hash,"evidence_exists":True,"evidence_hash_valid":True,"approval_ref":"old-msg"}]
        result=import_legacy_evidence(legacy,expected_source_hash=s_hash)
        self.assertEqual(result["verified_evidence"],["G03.M01"])
        self.assertEqual(len(result["not_verified"]),2)
        self.assertFalse(result["authorizes_new_package"])

    def test_exclusive_lock_denies_duplicate_and_requires_owner_to_release(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"work_package.lock"
            acquire_lock(path, owner="session-1", package_id="G03.PKG01",plan_hash="a"*64,device_id="device-1")
            self.assertEqual(json.loads(path.read_text())["deviceId"],"device-1")
            with self.assertRaises(ContractError):acquire_lock(path, owner="session-2",package_id="G03.PKG01",plan_hash="a"*64)
            with self.assertRaises(ContractError):release_lock(path, owner="session-2")
            self.assertTrue(path.exists())
            release_lock(path,owner="session-1")
            self.assertFalse(path.exists())


if __name__=="__main__":unittest.main(verbosity=2)
