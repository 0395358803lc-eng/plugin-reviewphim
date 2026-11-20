"""Real local codec integration and recovery regressions; no remote/model claims."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import pytest

from test_project_flow_v1325 import module,plan,state,complete


def run(f,p,s,executor=None,**kw):
    return f.run_until_hinge(p,s,executor or (lambda t,st:complete(f,p,st)),session_owner='session-A',**kw)


@pytest.mark.parametrize('bad_kind',['text','audio_only','truncated','damaged_packets'])
def test_reject_unusable_mp4_even_with_true_executor_flag(tmp_path,bad_kind):
    f=module();p=plan(tmp_path,stages=('G15',));s=state(f,p)
    result=complete(f,p,'G15');path=tmp_path/p['stage_outputs']['G15'][0]
    if bad_kind=='text':path.write_bytes(b'This is not a video')
    elif bad_kind=='audio_only':
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','sine=frequency=440',
                        '-t','0.5','-c:a','aac',str(path)],check=True,capture_output=True)
    elif bad_kind=='truncated':path.write_bytes(path.read_bytes()[:40])
    else:
        data=bytearray(path.read_bytes());pos=data.index(b'mdat')+4
        data[pos:pos+80]=b'\xff'*80;path.write_bytes(data)
    result['outputs'][0]['sha256']=f.file_sha(path)
    out=run(f,p,s,lambda t,st:result)
    assert out['status']=='FAILED' and 'G15' not in out['stage_completions']


def test_real_video_probe_and_decode_and_required_sidecars(tmp_path):
    f=module();p=plan(tmp_path,stages=('G15',));p['stage_outputs']['G15'].append('publish/metadata.json');s=state(f,p)
    result=complete(f,p,'G15')
    assert run(f,p,s,lambda t,st:result)['status']=='FAILED'
    side=tmp_path/'publish/metadata.json';side.parent.mkdir();side.write_text('{"title":"test"}')
    result['outputs'].append({'relative_path':'publish/metadata.json','sha256':f.file_sha(side)})
    result['technical_ready']=False  # local decode is authoritative
    out=run(f,p,s,lambda t,st:result)
    assert out['status']=='FINAL_REVIEW'
    assert out['stage_completions']['G15']['media_evidence'][0]['decode_exit']==0


def test_retry_preserves_done_and_honors_budget(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01','G15'));p['repair_budget']['allowed_kinds']=['transient']
    s=state(f,p);seen=[]
    def executor(t,st):
        seen.append(st)
        if st=='G15' and seen.count(st)==1:return {'status':'FAILED','reason':'temporary renderer error','failure_kind':'transient'}
        return complete(f,p,st)
    out=run(f,p,s,executor,persist=True)
    assert out['status']=='FINAL_REVIEW' and seen==['G01','G15','G15']
    assert out['retry_counts']=={'G15':1} and out['retry_history'][0]['result']=='DONE'
    assert f.read_checkpoint(tmp_path)==out


def test_no_infinite_retry_or_permission_escalation(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01',));p['repair_budget']['allowed_kinds']=['transient','permission']
    s=state(f,p);seen=[]
    out=run(f,p,s,lambda t,st:seen.append(st) or {'status':'FAILED','reason':'down','failure_kind':'transient'})
    assert out['status']=='FAILED' and len(seen)==3 and out['retry_counts']['G01']==2
    out=run(f,p,s,lambda t,st:{'status':'FAILED','reason':'needs install','failure_kind':'permission'})
    assert out['status']=='FAILED' and not out.get('retry_counts')
    with pytest.raises(ValueError):f.retry_failed(p,out,session_owner='session-A')


@pytest.mark.parametrize('field',['missing','owner','deviceId','plan_hash','package_id','WORK_PACKAGE_ID'])
def test_real_lock_checked_on_execution_and_resume(tmp_path,field):
    f=module();p=plan(tmp_path,stages=('G01',));s=state(f,p)
    lock=tmp_path/'logs/work_package.lock'
    if field=='missing':lock.unlink()
    else:
        content=json.loads(lock.read_text());content[field]='wrong';lock.write_text(json.dumps(content))
    seen=[];out=run(f,p,s,lambda t,st:seen.append(st))
    assert not seen and 'lock' in out['last_blocker']
    s.update(status='WAITING_USER',wait_reason='EXTERNAL_INPUT')
    with pytest.raises(ValueError):f.resume_after_user(p,s,action='EXTERNAL_INPUT',user_ref='u')


def test_actual_source_change_blocks(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01',));s=state(f,p)
    Path(p['SOURCE_MOVIE']).write_bytes(b'tampered')
    seen=[];out=run(f,p,s,lambda t,st:seen.append(st))
    assert not seen and 'source file SHA256 mismatch' in out['last_blocker']


@pytest.mark.parametrize('stage',['G05','G10','G11A','G11B'])
def test_proposal_exists_before_creative_gate_and_never_regenerated(tmp_path,stage):
    f=module();p=plan(tmp_path,stages=(stage,));s=state(f,p);seen=[]
    def executor(t,st):seen.append(st);return complete(f,p,st)
    waiting=run(f,p,s,executor)
    assert waiting['status']=='WAITING_USER' and stage in waiting['stage_completions']
    resumed=f.resume_after_user(p,waiting,action=f.CREATIVE_GATES[stage],user_ref='actual-user')
    assert run(f,p,resumed,executor)['status']=='PACKAGE_DONE' and seen==[stage]


def test_runner_records_reusable_without_manual_schema_patch(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01','G02'));s=state(f,p)
    old=run(f,p,s,max_steps=1)
    new=copy.deepcopy(p);new['WORK_PACKAGE_ID']='SECOND'
    fresh=state(f,new)
    records=copy.deepcopy(old['stage_completions'])
    reused=f.merge_verified_completions(new,fresh,records,expected_inputs={k:v['inputs'] for k,v in records.items()})
    seen=[]
    out=run(f,new,reused,lambda t,st:seen.append(st) or complete(f,new,st))
    assert seen==['G02'] and out['status']=='PACKAGE_DONE'
    assert records==old['stage_completions']
    assert out['stage_completions']['G01']['provenance']['WORK_PACKAGE_ID']==p['WORK_PACKAGE_ID']


def test_ledger_recovers_done_after_snapshot_crash(tmp_path,monkeypatch):
    f=module();p=plan(tmp_path,stages=('G01',));s=state(f,p)
    f.checkpoint(tmp_path,s,event='INITIALIZED')
    def crash(root,state):raise KeyboardInterrupt('power loss after durable event')
    monkeypatch.setattr(f,'_write_checkpoint',crash)
    s['status']='WAITING_USER';s['wait_reason']='EXTERNAL_INPUT'
    with pytest.raises(KeyboardInterrupt):f.checkpoint(tmp_path,s,event='WAITING_USER')
    loaded=f.read_checkpoint(tmp_path)
    assert loaded['status']=='WAITING_USER' and loaded['ledger_seq']==2


def test_lost_connection_reconciles_then_retries_only_interrupted_task(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01','G02'));p['repair_budget']['allowed_kinds']=['connection'];s=state(f,p)
    def worker(t,st):
        if st=='G02':raise KeyboardInterrupt('host disconnected')
        return complete(f,p,st)
    with pytest.raises(KeyboardInterrupt):run(f,p,s,worker,persist=True)
    loaded=f.read_checkpoint(tmp_path)
    assert loaded['inflight']['stage']=='G02'
    seen=[]
    assert run(f,p,loaded,lambda t,st:seen.append(st))['inflight'] and not seen
    failed=f.recover_interrupted(p,loaded,session_owner='session-A',recovery_ref='host-inspection-1',verify_inactive=lambda x:True,persist=True)
    resumed=f.retry_failed(p,failed,session_owner='session-A',persist=True)
    out=run(f,p,resumed,lambda t,st:seen.append(st) or complete(f,p,st),persist=True)
    assert out['status']=='PACKAGE_DONE' and seen==['G02']


def test_manual_copy_resumes_g12_without_rerunning_thumbnail(tmp_path):
    f=module();p=plan(tmp_path,stages=('G11B','G12'),delegations=('G11B_THUMBNAIL',));s=state(f,p);seen=[]
    def generate(t,st):
        seen.append(st)
        return {'status':'WAITING_USER','reason':'USER_IMAGE_PLACEMENT','generation_ref':'chat-image-1'}
    waiting=run(f,p,s,generate,persist=True)
    placed=complete(f,p,'G11B')['thumbnail_evidence']
    resumed=f.resume_after_user(p,waiting,action='USER_IMAGE_PLACEMENT',user_ref='copied',evidence=placed,persist=True)
    out=run(f,p,resumed,lambda t,st:seen.append(st) or complete(f,p,st),persist=True)
    assert seen==['G11B','G12'] and out['status']=='PACKAGE_DONE'


def test_full_real_video_flow_review_and_targeted_revision(tmp_path,monkeypatch):
    import sys
    f=module();p=plan(tmp_path,stages=f.STAGE_SEQUENCE,delegations=tuple(f.CREATIVE_GATES.values()))
    for st in ('G11','G12','G13','G14'):p['stage_outputs'][st]=['output/'+st+'.mp4']
    p['repair_budget']['allowed_kinds']=['transient']
    core=f._sibling('work_package_state');monkeypatch.setitem(sys.modules,'work_package_state',core)
    dispatcher=f._sibling('one_approval_dispatch_v1321')
    (tmp_path/'logs').mkdir(exist_ok=True)
    def approve(approved_plan,ref):
        proposed={'status':'PROPOSED','plan_hash':f.hash_plan(approved_plan),'source_hash':approved_plan['source_hash'],
            'deviceId':approved_plan['deviceId'],'JOB_DIR':approved_plan['JOB_DIR']}
        consent={'source':'user_message','approval_ref':ref,'action':'APPROVE_PACKAGE',
            'WORK_PACKAGE_ID':approved_plan['WORK_PACKAGE_ID'],'deviceId':approved_plan['deviceId'],
            'JOB_DIR':approved_plan['JOB_DIR'],'plan_hash':f.hash_plan(approved_plan)}
        return dispatcher.approve_and_start(proposed,approved_plan,consent,owner='session-A',
            lock_path=tmp_path/'logs/work_package.lock',observed_device_id=approved_plan['deviceId'],
            observed_source_hash=approved_plan['source_hash'])['state']
    s=approve(p,'one-package-approval');seen=[]
    def execute(t,st):
        seen.append(st)
        if st=='G11' and seen.count(st)==1:return {'status':'FAILED','reason':'transient render failure','failure_kind':'transient'}
        if st=='G11B':return {'status':'WAITING_USER','reason':'USER_IMAGE_PLACEMENT','generation_ref':'test-host-image'}
        return complete(f,p,st)
    waiting=run(f,p,s,execute,persist=True)
    assert waiting['status']=='WAITING_USER' and seen[-1]=='G11B'
    evidence=complete(f,p,'G11B')['thumbnail_evidence']
    resumed=f.resume_after_user(p,waiting,action='USER_IMAGE_PLACEMENT',user_ref='user-copied',evidence=evidence,persist=True)
    out=run(f,p,resumed,execute,persist=True)
    seen_unique=list(dict.fromkeys(seen))
    assert out['status']=='FINAL_REVIEW' and seen_unique==list(f.STAGE_SEQUENCE)
    assert seen.count('G11B')==1 and seen.count('G11')==2
    original=copy.deepcopy(out['delivery']);old_bytes=(tmp_path/original['outputs'][0]['relative_path']).read_bytes()
    requested=f.user_review(p,out,action='REVISION_REQUESTED',user_ref='user-fix',notes='Adjust final segment only',targets=['G14'],persist=True)
    new=f.propose_revision(p,requested)
    assert new['revision_request']['affected_stages']==['G14','G15']
    # Host has released its previous lock and authenticated the concrete new plan.
    core.release_lock(tmp_path/'logs/work_package.lock',owner='session-A')
    fresh=approve(new,'revision-scope-approval');fresh['ledger_seq']=requested['ledger_seq']
    resumed=f.begin_revision(p,new,requested,fresh,session_owner='session-A',persist=True)
    revised_seen=[]
    revised=run(f,new,resumed,lambda t,st:revised_seen.append(st) or complete(f,new,st),persist=True)
    assert revised_seen==['G14','G15'] and revised['status']=='FINAL_REVIEW'
    assert (tmp_path/original['outputs'][0]['relative_path']).read_bytes()==old_bytes
    assert revised['delivery']['outputs'][0]['sha256']!=original['outputs'][0]['sha256']
    accepted=f.user_review(new,revised,action='ACCEPTED',user_ref='user-accept',notes='Accepted version 2',persist=True)
    assert accepted['acceptance']['delivery']['version']==2
    events=[json.loads(x) for x in (tmp_path/'logs/project_flow_v1325.jsonl').read_text(encoding='utf-8').splitlines()]
    assert {'REVISION_REQUESTED','ACCEPTED','REVISION_STARTED'}<={x['event'] for x in events}
    assert f.read_checkpoint(tmp_path)['status']=='ACCEPTED'
    # Optional persistent, shareable evidence for the release report.
    if os.environ.get('REVIEW_EVIDENCE_DIR'):
        target=Path(os.environ['REVIEW_EVIDENCE_DIR']);target.mkdir(parents=True,exist_ok=True)
        shutil.copy2(tmp_path/original['outputs'][0]['relative_path'],target/'integration-v1.mp4')
        shutil.copy2(tmp_path/revised['delivery']['outputs'][0]['relative_path'],target/'integration-v2.mp4')
        shutil.copy2(tmp_path/'logs/project_flow_v1325.jsonl',target/'integration-ledger.jsonl')
        (target/'integration-summary.json').write_text(json.dumps({'stages':seen,'revision_stages':revised_seen,
            'final_status':accepted['status'],'quality_qc_invocations':accepted['quality_qc_invocations'],
            'media_evidence':revised['stage_completions']['G15']['media_evidence'],
            'limits':'Local host fixture artifacts; real decodable MP4. No remote ASR/TTS/ImageGen or film-quality acceptance claimed.'},indent=2),encoding='utf-8')


def test_legacy_core_routes_production_dispatch_and_blocks_qc_transition(tmp_path):
    f=module();core=f._sibling('work_package_state');p=plan(tmp_path,stages=('G05',));s=state(f,p);s['execution_mode']=f.MODE
    assert core.can_dispatch(s,p['task_ids'][0],session_owner='session-A',plan=p)
    with pytest.raises(ValueError):core.transition(s,'PACKAGE_PASS',event='qc_complete')


def test_missing_decoder_permission_never_installs(tmp_path):
    f=module();p=plan(tmp_path,stages=('G15',));p['allowed_executables_and_models']=[]
    out=run(f,p,state(f,p))
    assert out['status']=='FAILED' and out['failure']['kind']=='permission'


def test_voice_sample_approval_precedes_bulk_voice_in_same_stage(tmp_path):
    import wave
    f=module();p=plan(tmp_path,stages=('G07',));s=state(f,p);seen=[]
    assert f.decide_next(p,s,session_owner='session-A')['phase']=='proposal'
    def sample(t,st):
        seen.append('sample')
        path=tmp_path/p['stage_proposals']['G07'][0];path.parent.mkdir()
        with wave.open(str(path),'wb') as stream:
            stream.setparams((1,2,16000,1600,'NONE','not compressed'));stream.writeframes(b'\0\0'*1600)
        return {'status':'PROPOSAL_READY','outputs':[{'relative_path':p['stage_proposals']['G07'][0],'sha256':f.file_sha(path)}]}
    waiting=run(f,p,s,sample,persist=True)
    assert waiting['status']=='WAITING_USER' and 'G07' not in waiting['stage_completions']
    resumed=f.resume_after_user(p,waiting,action='G07_VOICE',user_ref='voice-approved',persist=True)
    assert f.decide_next(p,resumed,session_owner='session-A')['phase']=='execute'
    out=run(f,p,resumed,lambda t,st:seen.append('bulk') or complete(f,p,st),persist=True)
    assert out['status']=='PACKAGE_DONE' and seen==['sample','bulk']


def test_configuration_changes_and_incomplete_provenance_block_reuse(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01',));old=run(f,p,state(f,p))
    new=copy.deepcopy(p);new['WORK_PACKAGE_ID']='NEW';new['production_config']={'voice':'different'}
    fresh=state(f,new)
    with pytest.raises(ValueError):f.merge_verified_completions(new,fresh,old['stage_completions'],expected_inputs={'G01':old['stage_completions']['G01']['inputs']})
    new.pop('production_config');fresh=state(f,new)
    record=copy.deepcopy(old['stage_completions']);record['G01'].pop('approval_ref')
    with pytest.raises(ValueError):f.merge_verified_completions(new,fresh,record,expected_inputs={'G01':record['G01']['inputs']})
    record=copy.deepcopy(old['stage_completions']);record['G01']['plan_hash']='f'*64
    with pytest.raises(ValueError):f.merge_verified_completions(new,fresh,record,expected_inputs={'G01':record['G01']['inputs']})


def test_lock_recovery_never_steals_existing_lock(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01',));state(f,p);core=f._sibling('work_package_state')
    path=tmp_path/'logs/work_package.lock';before=path.read_bytes()
    with pytest.raises(ValueError):core.recover_missing_lock(path,owner='different',package_id=p['WORK_PACKAGE_ID'],
        plan_hash=f.hash_plan(p),device_id=p['deviceId'],recovery_ref='host-ref',verify_inactive=lambda *a:True)
    assert path.read_bytes()==before


def test_cli_claim_failure_retry_and_binding(tmp_path):
    from test_project_flow_cli_v1325 import call
    f=module();p=plan(tmp_path,stages=('G01',));p['repair_budget']['allowed_kinds']=['transient'];s=state(f,p)
    plan_path=tmp_path/'plan.json';plan_path.write_text(json.dumps(p));f.checkpoint(tmp_path,s)
    assert call('start','--plan',plan_path)['task_id']==p['task_ids'][0]
    result={'status':'FAILED','reason':'render unavailable','failure_kind':'transient','task_id':p['task_ids'][0],'plan_hash':f.hash_plan(p)}
    result_path=tmp_path/'result.json';result_path.write_text(json.dumps(result))
    assert call('record','--plan',plan_path,'--result',result_path)['status']=='FAILED'
    assert call('retry','--plan',plan_path)['retry_counts']=={'G01':1}
    result={**complete(f,p,'G01'),'task_id':p['task_ids'][0],'plan_hash':f.hash_plan(p)}
    result_path.write_text(json.dumps(result))
    assert call('record','--plan',plan_path,'--result',result_path)['status']=='PACKAGE_DONE'


def test_ledger_corruption_fails_closed_and_stale_writer_rejected(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01',));s=state(f,p);f.checkpoint(tmp_path,s)
    old=copy.deepcopy(s);f.checkpoint(tmp_path,s)
    with pytest.raises(ValueError):f.checkpoint(tmp_path,old)
    ledger=tmp_path/'logs/project_flow_v1325.jsonl'
    with ledger.open('a') as stream:stream.write('{partial')
    with pytest.raises(ValueError):f.read_checkpoint(tmp_path)


def test_manifest_prompts_all_route_production_and_app_identity_unchanged():
    root=Path(__file__).resolve().parents[3]
    portable=json.loads((root/'plugin.json').read_text(encoding='utf-8'))
    overlay=json.loads((root/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    interface=portable['extensions']['com.openai']['interface']
    assert len(interface['defaultPrompt'])==9
    assert all('PRODUCTION_FIRST_V1325' in p and 'PRODUCTION_RELIABILITY_V1326' in p for p in interface['defaultPrompt'])
    assert overlay['interface']==interface and portable['name']==overlay['name']=='review-phim'
    assert portable['extensions']['com.openai']['apps']==overlay['apps']=='./.app.json'
