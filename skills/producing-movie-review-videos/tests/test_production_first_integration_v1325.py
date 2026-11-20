"""Mode-specific integration: Production First bypasses aesthetic Qxx, never security."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import hashlib
from test_project_flow_v1325 import plan,state,complete,module as flow_mod
ROOT=Path(__file__).resolve().parents[1]

def guard_mod():
    path=ROOT/'tools'/'workflow_integrity_v1323.py'
    spec=importlib.util.spec_from_file_location('workflow_integrity_v1323',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def test_production_first_plan_is_not_rejected_by_old_guard(tmp_path):
    g=guard_mod();p=plan(tmp_path,stages=('G01','G02'))
    assert g.validate_new_package(p)==p['task_ids']

def test_production_first_dispatch_without_q01_or_q02(tmp_path):
    f=flow_mod();g=guard_mod();p=plan(tmp_path,stages=('G01','G02'));s=state(f,p)
    assert g.decide_dispatch(p,s,p['task_ids'][0],session_owner='session-A').allowed
    assert not g.decide_dispatch(p,s,p['task_ids'][1],session_owner='session-A').allowed
    s=f.run_until_hinge(p,s,lambda t,st:complete(f,p,st),session_owner='session-A',max_steps=1)
    assert g.decide_dispatch(p,s,p['task_ids'][1],session_owner='session-A').allowed
    assert not s['qc_gates_passed']

def test_production_first_package_completes_without_quality_qc(tmp_path):
    f=flow_mod();g=guard_mod();p=plan(tmp_path,stages=('G01','G02'));s=state(f,p)
    finished=f.run_until_hinge(p,s,lambda t,st:complete(f,p,st),session_owner='session-A')
    assert finished['status']=='PACKAGE_DONE'
    assert g.validate_package_completion(p,finished).allowed

def test_mode_not_enabled_legacy_qc_still_blocks(tmp_path):
    f=flow_mod();g=guard_mod();p=plan(tmp_path,stages=('G01','G02'));p.pop('execution_mode');p.pop('creative_delegations');p.pop('stage_outputs');s=state(g,p)
    s.update(allowed_tasks=p['task_ids'],qc_gates_passed=[],stage_evidence={},task_qc={})
    assert not g.decide_dispatch(p,s,p['task_ids'][1],session_owner='session-A').allowed

def test_out_of_scope_approval_never_jumps_stage(tmp_path):
    f=flow_mod();g=guard_mod();p=plan(tmp_path,stages=('G01','G02'));s=state(f,p)
    assert not g.decide_dispatch(p,s,'G03.TRANSLATE.FULL',session_owner='session-A').allowed

def test_no_quality_gate_but_manual_image_still_blocks(tmp_path):
    f=flow_mod();g=guard_mod();p=plan(tmp_path,stages=('G11B','G12'),delegations=('G11B_THUMBNAIL',));s=state(f,p)
    assert g.decide_dispatch(p,s,p['task_ids'][0],session_owner='session-A').allowed
    assert not g.decide_dispatch(p,s,p['task_ids'][1],session_owner='session-A').allowed


def test_one_click_approval_to_real_stage_executor_same_turn(tmp_path, monkeypatch):
    import sys
    from test_one_approval_dispatch_v1321 import core_fixture
    core=core_fixture();monkeypatch.setitem(sys.modules,'work_package_state',core)
    mpath=ROOT/'tools'/'one_approval_dispatch_v1321.py'
    spec=importlib.util.spec_from_file_location('one_approval_dispatch_v1321_for_flow',mpath)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    f=flow_mod();job=tmp_path/'job';(job/'logs').mkdir(parents=True)
    p=plan(job,stages=('G01','G02'))
    digest=f.hash_plan(p)
    state0={'status':'PROPOSED','plan_hash':digest,'deviceId':p['deviceId'],
            'JOB_DIR':p['JOB_DIR'],'source_hash':p['source_hash']}
    approval={'source':'user_message','approval_ref':'real-approve-turn','action':'APPROVE_PACKAGE',
              'WORK_PACKAGE_ID':p['WORK_PACKAGE_ID'],'deviceId':p['deviceId'],
              'JOB_DIR':p['JOB_DIR'],'plan_hash':digest}
    opened=m.approve_and_start(state0,p,approval,owner='session-A',lock_path=job/'logs'/'work_package.lock',
              observed_device_id=p['deviceId'],observed_source_hash=p['source_hash'])
    assert opened['outcome']=='STARTED' and opened['dispatch_now']
    seen=[]
    def real_executor(task,stage):
        seen.append(task)
        return complete(f,p,stage)
    out=f.run_until_hinge(p,opened['state'],real_executor,session_owner='session-A',persist=True)
    assert out['status']=='PACKAGE_DONE' and seen==p['task_ids']
    assert (job/'logs'/'project_flow_v1325.json').exists()
    assert len((job/'logs'/'project_flow_v1325.jsonl').read_text().splitlines())>=3
