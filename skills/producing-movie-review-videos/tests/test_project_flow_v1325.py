"""Production-first real project state machine tests; synthetic artifacts only."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import shutil
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'tools'/'project_flow_v1325.py'

def module():
    spec=importlib.util.spec_from_file_location('project_flow_v1325',MODULE)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def plan(root, *,stages=('G01','G02','G03'), delegations=()):
    task={'G01':'G01.SOURCE.FULL','G02':'G02.ASR.FULL','G03':'G03.TRANSLATE.FULL',
          'G04':'G04.FILM.UNDERSTANDING.FULL','G05':'G05.REVIEW.FULL','G07':'G07.M03','G10':'G10.M01',
          'G11A':'G11A.YOUTUBE_METADATA.FULL','G11B':'G11B.THUMBNAIL.FULL',
          'G12':'G12.M01','G14':'G14.M01','G15':'G15.M03'}
    source=root.parent/'source.mkv'
    source.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists():source.write_bytes(b'test-source-bytes')
    return {'schema_version':'work-package.v2','execution_mode':'PRODUCTION_FIRST_V1325',
      'WORK_PACKAGE_ID':'FULL-2026-11-20','deviceId':'device-A','JOB_DIR':str(root),
      'SOURCE_MOVIE':str(root.parent/'source.mkv'),'source_hash':hashlib.sha256(source.read_bytes()).hexdigest(),
      'allowed_stages':list(stages),'task_ids':[task.get(x,x+'.M01') for x in stages],
      'bounded_batches':[],'allowed_read_roots':[str(root.parent)],
      'allowed_write_roots':[str(root)],'repair_budget':{'per_issue':2,'total':4,'allowed_kinds':['format']},
      'stage_proposals':{'G07':['proposals/voice-sample.wav']} if 'G07' in stages and 'G07_VOICE' not in delegations else {},
      'install_budget':[],'human_gates':[],'creative_delegations':list(delegations),
      'expected_outputs':[],'acceptance_criteria':[],'stop_conditions':[],
      'stage_outputs':{s:['assets/youtube_thumbnail.png' if s=='G11B' else f'output/{s}.mp4' if s=='G15' else f'output/{s}.dat'] for s in stages},
      'requires_audio':False,  # These codec fixtures deliberately contain silent video.
      'allowed_executables_and_models':['ffprobe','ffmpeg']}


def state(m,p):
    logs=Path(p['JOB_DIR'])/'logs';logs.mkdir(parents=True,exist_ok=True)
    (logs/'work_package.lock').write_text(json.dumps({'owner':'session-A','package_id':p['WORK_PACKAGE_ID'], 'WORK_PACKAGE_ID':p['WORK_PACKAGE_ID'],'deviceId':p['deviceId'],'plan_hash':m.hash_plan(p)}))
    return {'status':'RUNNING','plan_hash':m.hash_plan(p),'approved_plan_hash':m.hash_plan(p),
      'approval_ref':'user-approved-exact-plan','deviceId':p['deviceId'],
      'JOB_DIR':p['JOB_DIR'],'source_hash':p['source_hash'],
      'allowed_tasks':p['task_ids'],'lock_owner':'session-A','lock_verified':True,
      'stage_completions':{},'approved_human_gates':[], 'task_qc':{},'qc_gates_passed':[]}


def complete(m,p,stage):
    f=Path(p['JOB_DIR'])/p['stage_outputs'][stage][0]
    f.parent.mkdir(parents=True,exist_ok=True)
    evidence=None
    if f.suffix=='.mp4':
        color='red' if p.get('revision_number',1)>1 else 'blue'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i',f'color=c={color}:s=160x90:r=12',
            '-t','0.5','-c:v','mpeg4',str(f)],check=True,capture_output=True)
    elif stage=='G11B':
        from test_manual_thumbnail_handoff_v1324 import make_png,inputs
        make_png(f)
        _,title,approval,_=inputs(Path(p['JOB_DIR']))
        evidence={'title':title,'approval':approval,'image_name':f.name,'relative_path':p['stage_outputs'][stage][0],
                  'image_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
    else:f.write_bytes((stage+'-real-output').encode())
    return {'status':'DONE','outputs':[{'relative_path':p['stage_outputs'][stage][0],
          'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}], 'technical_ready':True,'thumbnail_evidence':evidence}


def test_missing_module_red():
    m=module();assert m.STAGE_SEQUENCE[0]=='P00'


def test_no_qc_intermediate_and_auto_advance(tmp_path):
    m=module();p=plan(tmp_path);s=state(m,p)
    executed=[]
    def execute(task,stage):
        executed.append(stage)
        return complete(m,p,stage)
    result=m.run_until_hinge(p,s,execute,session_owner='session-A')
    assert result['status']=='PACKAGE_DONE'
    assert executed==['G01','G02','G03']
    assert sorted(result['stage_completions'])==['G01','G02','G03']
    assert result['quality_qc_invocations']==0
    assert not result.get('qc_gates_passed')


def test_missing_output_is_failed_not_done(tmp_path):
    m=module();p=plan(tmp_path,stages=('G01',));s=state(m,p)
    result=m.run_until_hinge(p,s,lambda t,x:{'status':'DONE','outputs':[]},session_owner='session-A')
    assert result['status']=='FAILED' and not result['stage_completions']


def test_empty_and_wrong_hash_output_rejected(tmp_path):
    m=module();p=plan(tmp_path,stages=('G01',));s=state(m,p)
    file=tmp_path/'output/G01.dat';file.parent.mkdir(exist_ok=True);file.touch()
    ev={'status':'DONE','outputs':[{'relative_path':'output/G01.dat','sha256':'b'*64}]}
    result=m.run_until_hinge(p,s,lambda t,x:ev,session_owner='session-A')
    assert result['status']=='FAILED'
    file.write_bytes(b'data')
    result=m.run_until_hinge(p,state(m,p),lambda t,x:ev,session_owner='session-A')
    assert result['status']=='FAILED'


def test_reject_unauthorized_or_wrong_owner(tmp_path):
    m=module();p=plan(tmp_path);s=state(m,p)
    assert not m.decide_next(p,s,session_owner='different')['allowed']
    assert not m.decide_next(p,{**s,'source_hash':'b'*64},session_owner='session-A')['allowed']
    assert not m.decide_next(p,{**s,'plan_hash':'0'*64},session_owner='session-A')['allowed']
    assert m.decide_next(p,{**s,'lock_verified':False},session_owner='session-A')['allowed']  # real lock is authoritative
    assert not m.decide_next(p,{**s,'status':'PROPOSED'},session_owner='session-A')['allowed']


def test_delegation_stops_for_script_without_scope(tmp_path):
    m=module();p=plan(tmp_path,stages=('G05','G07'));s=state(m,p)
    result=m.run_until_hinge(p,s,lambda t,x:complete(m,p,x),session_owner='session-A')
    assert result['status']=='WAITING_USER' and result['next_stage']=='G05'
    assert result['wait_reason']=='G05_SCRIPT'


def test_specific_delegation_skips_script_quality_gate(tmp_path):
    m=module();p=plan(tmp_path,stages=('G05','G07'),delegations=('G05_SCRIPT','G07_VOICE'))
    result=m.run_until_hinge(p,state(m,p),lambda t,x:complete(m,p,x),session_owner='session-A')
    assert result['status']=='PACKAGE_DONE'


def test_manual_thumbnail_stops_even_with_creative_delegation(tmp_path):
    m=module();p=plan(tmp_path,stages=('G11B','G12'),delegations=('G11B_THUMBNAIL',))
    s=state(m,p)
    result=m.run_until_hinge(p,s,lambda t,x:{'status':'WAITING_USER','reason':'USER_IMAGE_PLACEMENT'},session_owner='session-A')
    assert result['status']=='WAITING_USER' and result['wait_reason']=='USER_IMAGE_PLACEMENT'
    assert 'G12' not in result['stage_completions']


def test_manual_thumbnail_cannot_mark_done_without_file_verified(tmp_path):
    m=module();p=plan(tmp_path,stages=('G11B',),delegations=('G11B_THUMBNAIL',))
    result=m.run_until_hinge(p,state(m,p),lambda t,x:{**complete(m,p,x),'thumbnail_evidence':None},session_owner='session-A')
    assert result['status']=='FAILED'


def test_file_validated_thumbnail_can_continue(tmp_path):
    m=module();p=plan(tmp_path,stages=('G11B','G12'),delegations=('G11B_THUMBNAIL',))
    def execute(t,st):
        r=complete(m,p,st)
        if st=='G11B':r['user_image_placement_verified']=True
        return r
    result=m.run_until_hinge(p,state(m,p),execute,session_owner='session-A')
    assert result['status']=='PACKAGE_DONE'


def test_checkpoint_resume_skips_done_stage_and_detects_tamper(tmp_path):
    m=module();p=plan(tmp_path);s=state(m,p);ran=[]
    def execute(t,st):
        ran.append(st)
        if st=='G02':return {'status':'WAITING_USER','reason':'EXTERNAL_INPUT'}
        return complete(m,p,st)
    r=m.run_until_hinge(p,s,execute,session_owner='session-A',persist=True)
    assert r['status']=='WAITING_USER' and ran==['G01','G02']
    loaded=m.read_checkpoint(tmp_path)
    assert 'G01' in loaded['stage_completions']
    def execute2(t,st):
        ran.append(st);return complete(m,p,st)
    loaded['status']='RUNNING'
    r=m.run_until_hinge(p,loaded,execute2,session_owner='session-A',persist=True)
    assert r['status']=='PACKAGE_DONE' and ran==['G01','G02','G02','G03']
    (tmp_path/'output/G01.dat').write_bytes(b'tampered')
    loaded=m.read_checkpoint(tmp_path);loaded['status']='RUNNING'
    assert not m.decide_next(p,loaded,session_owner='session-A')['allowed']


def test_review_and_targeted_revision_preserve_original(tmp_path):
    m=module();p=plan(tmp_path,stages=('G14','G15'))
    result=m.run_until_hinge(p,state(m,p),lambda t,x:complete(m,p,x),session_owner='session-A')
    assert result['status']=='FINAL_REVIEW'
    requested=m.user_review(p,result,action='REVISION_REQUESTED',user_ref='real-user-msg',notes='Chỉnh đoạn cao trào',targets=['G14'])
    assert requested['status']=='REVISION_REQUESTED' and requested['revision_requests'][-1]['targets']==['G14']
    assert requested['stage_completions']['G14']==result['stage_completions']['G14']
    accepted=m.user_review(p,result,action='ACCEPTED',user_ref='real-user-msg',notes='Đạt')
    assert accepted['status']=='ACCEPTED'


def test_deletion_is_not_creative_delegation(tmp_path):
    m=module();p=plan(tmp_path,stages=('G15',));p['task_ids']=['G15.M05'];p['delete_paths']=['output/old.mp4'];s=state(m,p)
    with pytest.raises(ValueError):m.validate_plan({**p,'creative_delegations':['G15_DELETE']})
    assert not m.decide_next(p,s,session_owner='session-A')['allowed']


def test_executor_cannot_run_out_of_scope(tmp_path):
    m=module();p=plan(tmp_path,stages=('G01',));s=state(m,p)
    assert not m.validate_artifacts(tmp_path,[{'relative_path':'../escape.txt','sha256':'a'*64}],['output/G01.dat'])['ok']
    with pytest.raises(ValueError):m.validate_plan({**p,'allowed_stages':['G01','G02']})


def test_no_background_promises_or_fake_remote_executor():
    m=module()
    assert hasattr(m,'run_until_hinge')
    assert 'Remote_Desktop_Commander' in m.__doc__


def test_manual_resume_needs_real_user_and_verified_placement(tmp_path):
    m=module();p=plan(tmp_path,stages=('G11B',),delegations=('G11B_THUMBNAIL',))
    s=state(m,p);s['status']='WAITING_USER';s['next_stage']='G11B';s['wait_reason']='USER_IMAGE_PLACEMENT'
    with pytest.raises(ValueError):m.resume_after_user(p,s,action='USER_IMAGE_PLACEMENT',user_ref='',evidence={'status':'FILE_ACCEPTED'})
    with pytest.raises(ValueError):m.resume_after_user(p,s,action='USER_IMAGE_PLACEMENT',user_ref='real-msg',evidence={'status':'UNVERIFIED'})
    resumed=m.resume_after_user(p,s,action='USER_IMAGE_PLACEMENT',user_ref='real-msg',evidence=complete(m,p,'G11B')['thumbnail_evidence'])
    assert resumed['status']=='RUNNING' and resumed['external_resolved_by']=='real-msg'


def test_creative_resume_needs_exact_requested_gate(tmp_path):
    m=module();p=plan(tmp_path,stages=('G05',));s=state(m,p)
    r=m.run_until_hinge(p,s,lambda t,x:complete(m,p,x),session_owner='session-A')
    assert r['wait_reason']=='G05_SCRIPT'
    with pytest.raises(ValueError):m.resume_after_user(p,r,action='G07_VOICE',user_ref='real-msg')
    resumed=m.resume_after_user(p,r,action='G05_SCRIPT',user_ref='real-msg')
    assert resumed['status']=='RUNNING' and resumed['approved_human_gates']==['G05_SCRIPT']
    done=m.run_until_hinge(p,resumed,lambda t,x:complete(m,p,x),session_owner='session-A')
    assert done['status']=='PACKAGE_DONE'


def test_only_full_video_can_be_accepted(tmp_path):
    m=module();p=plan(tmp_path,stages=('G01',));s=state(m,p)
    r=m.run_until_hinge(p,s,lambda t,x:complete(m,p,x),session_owner='session-A')
    assert r['status']=='PACKAGE_DONE'
    with pytest.raises(ValueError):m.user_review(p,r,action='ACCEPTED',user_ref='u1',notes='ok')


def test_end_to_end_18_stages_with_creative_delegation(tmp_path):
    m=module();stages=m.STAGE_SEQUENCE
    delegates=tuple(m.CREATIVE_GATES.values())
    p=plan(tmp_path,stages=stages,delegations=delegates)
    seen=[]
    def execute(t,st):
        seen.append(st)
        r=complete(m,p,st)
        if st=='G11B':r['user_image_placement_verified']=True
        return r
    result=m.run_until_hinge(p,state(m,p),execute,session_owner='session-A')
    assert result['status']=='FINAL_REVIEW' and len(seen)==18
    assert seen==list(stages)
    assert result['quality_qc_invocations']==0
    assert m.user_review(p,result,action='ACCEPTED',user_ref='real-owner',notes='Video đạt')['status']=='ACCEPTED'


def test_scope_cannot_write_to_unapproved_job_or_read_other_source(tmp_path):
    m=module();p=plan(tmp_path/'job',stages=('G01',));(tmp_path/'job').mkdir()
    with pytest.raises(ValueError):m.validate_plan({**p,'allowed_write_roots':[str(tmp_path/'other')]})
    with pytest.raises(ValueError):m.validate_plan({**p,'allowed_read_roots':[str(tmp_path/'other')]})


def test_reuse_stage_outputs_from_prior_approved_package_only_after_bytes_check(tmp_path):
    m=module();p=plan(tmp_path,stages=('G01','G02'))
    r=complete(m,p,'G01')
    old={'schema':'stage-completion.v2','JOB_DIR':p['JOB_DIR'],'deviceId':p['deviceId'],'task_id':'G01.SOURCE.FULL','source_hash':p['source_hash'],
         'approval_ref':'old-real-user-approval','WORK_PACKAGE_ID':'PREV-PACKAGE',
         'outputs':r['outputs'],'completion_status':'DONE', 'plan_hash':'f'*64,
         'inputs':m.expected_inputs(p,{},'G01')}
    old['record_sha256']=m.completion_hash(old)
    s=state(m,p)
    adopted=m.merge_verified_completions(p,s,{'G01':old},expected_inputs={'G01':m.expected_inputs(p,{},'G01')})
    assert adopted['stage_completions']['G01']['imported_from_package']=='PREV-PACKAGE'
    assert m.decide_next(p,adopted,session_owner='session-A')['next_stage']=='G02'
    bad={**old,'source_hash':'b'*64}
    with pytest.raises(ValueError):m.merge_verified_completions(p,s,{'G01':bad},expected_inputs={'G01':m.expected_inputs(p,{},'G01')})
    (tmp_path/'output/G01.dat').write_bytes(b'changed')
    with pytest.raises(ValueError):m.merge_verified_completions(p,s,{'G01':old},expected_inputs={'G01':m.expected_inputs(p,{},'G01')})
