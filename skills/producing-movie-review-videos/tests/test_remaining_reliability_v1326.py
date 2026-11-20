"""Audio contracts, cache invalidation, delta recovery and path containment."""
import copy
import json
import os
from pathlib import Path
import subprocess
import pytest
from test_project_flow_v1325 import module,plan,state,complete


def render(f,p,*,audio):
    path=Path(p['JOB_DIR'])/p['stage_outputs']['G15'][0]
    path.parent.mkdir(parents=True,exist_ok=True)
    args=['ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i','color=blue:s=160x90:r=12']
    if audio:args+=['-f','lavfi','-i','sine=frequency=440:sample_rate=48000']
    subprocess.run(args+['-t','0.5','-c:v','mpeg4','-c:a','aac',str(path)],check=True,capture_output=True)
    return {'status':'DONE','outputs':[{'relative_path':p['stage_outputs']['G15'][0],'sha256':f.file_sha(path)}]}


@pytest.mark.parametrize('required,present,expected',[(True,True,'FINAL_REVIEW'),(True,False,'FAILED'),(False,False,'FINAL_REVIEW')])
def test_audio_contract(tmp_path,required,present,expected):
    f=module();p=plan(tmp_path,stages=('G15',));p['requires_audio']=required
    result=render(f,p,audio=present)
    out=f.run_until_hinge(p,state(f,p),lambda *a:result,session_owner='session-A')
    assert out['status']==expected
    if expected=='FAILED':assert 'G15' not in out['stage_completions']


def test_audio_required_by_default_and_per_file_override(tmp_path):
    f=module();p=plan(tmp_path,stages=('G15',));p.pop('requires_audio')
    result=render(f,p,audio=False)
    with pytest.raises(ValueError,match='audio'):f.validate_media(p,result['outputs'])
    p['media_contracts']={result['outputs'][0]['relative_path']:{'requires_audio':False,'expected_duration':0.5}}
    assert f.validate_media(p,result['outputs'])
    p['media_contracts'][result['outputs'][0]['relative_path']]['expected_duration']=10
    with pytest.raises(ValueError,match='duration'):f.validate_media(p,result['outputs'])


def test_one_decode_through_completion_final_review_and_acceptance(tmp_path):
    f=module();cache=f._sibling('verification_cache_v1326');cache.clear()
    p=plan(tmp_path,stages=('G15',));p['requires_audio']=True
    result=render(f,p,audio=True)
    out=f.run_until_hinge(p,state(f,p),lambda *a:result,session_owner='session-A',persist=True)
    assert out['status']=='FINAL_REVIEW'
    assert cache.stats['decode_runs']==cache.stats['probe_runs']==1
    accepted=f.user_review(p,out,action='ACCEPTED',user_ref='test-user',notes='test acceptance',persist=True)
    assert accepted['status']=='ACCEPTED' and cache.stats['decode_runs']==1
    record=out['stage_completions']['G15'];cache.clear()
    f.validate_media(p,record['outputs'],prior_evidence=record['media_evidence'])
    assert cache.stats['decode_runs']==0 and cache.stats['media_hits']==1
    bad=copy.deepcopy(record['media_evidence']);bad[0]['duration']=99
    f.validate_media(p,record['outputs'],prior_evidence=bad)
    assert cache.stats['decode_runs']==1


def test_cache_rechecks_contract_and_tool_identity(tmp_path,monkeypatch):
    f=module();cache=f._sibling('verification_cache_v1326');cache.clear()
    p=plan(tmp_path,stages=('G15',));result=render(f,p,audio=False)
    f.validate_media(p,result['outputs']);assert cache.stats['decode_runs']==1
    p['requires_audio']=True
    with pytest.raises(ValueError,match='audio'):f.validate_media(p,result['outputs'])
    p['requires_audio']=False
    identity=cache.tool_identity
    monkeypatch.setattr(cache,'tool_identity',lambda b:{**identity(b),'version':'changed-tool-version'})
    f.validate_media(p,result['outputs']);assert cache.stats['decode_runs']==2


def test_hash_detects_same_size_restored_mtime_and_replacement(tmp_path):
    f=module();cache=f._sibling('verification_cache_v1326');cache.clear()
    path=tmp_path/'data';path.write_bytes(b'abc');stamp=path.stat()
    original=f.file_sha(path);assert f.file_sha(path)==original
    assert cache.stats['hash_reads']==1
    path.write_bytes(b'xyz');os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    assert f.file_sha(path)!=original and cache.stats['hash_reads']==2
    replacement=tmp_path/'new';replacement.write_bytes(b'abc');os.utime(replacement,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    os.replace(replacement,path)
    assert f.file_sha(path)==original and cache.stats['hash_reads']==3
    f.file_sha(path,force=True);assert cache.stats['hash_reads']==4


def test_media_change_never_reuses_old_decode(tmp_path):
    f=module();p=plan(tmp_path,stages=('G15',));result=render(f,p,audio=True)
    evidence=f.validate_media(p,result['outputs']);path=tmp_path/result['outputs'][0]['relative_path']
    stamp=path.stat();data=bytearray(path.read_bytes());pos=data.index(b'mdat')+4
    data[pos:pos+128]=b'\xff'*128;path.write_bytes(data);os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    with pytest.raises(ValueError,match='SHA256'):f.validate_media(p,result['outputs'],prior_evidence=evidence)
    result['outputs'][0]['sha256']=f.file_sha(path)
    with pytest.raises(ValueError,match='decode'):f.validate_media(p,result['outputs'],prior_evidence=evidence)


def test_corrupt_audio_packets_fail_full_decode(tmp_path):
    f=module();p=plan(tmp_path,stages=('G15',));p['requires_audio']=True
    result=render(f,p,audio=True);path=tmp_path/result['outputs'][0]['relative_path']
    probe=subprocess.run(['ffprobe','-v','error','-select_streams','a','-show_packets','-of','json',str(path)],check=True,capture_output=True,text=True)
    packets=json.loads(probe.stdout)['packets'];data=bytearray(path.read_bytes())
    for packet in packets:
        offset=int(packet['pos']);length=int(packet['size']);data[offset:offset+length]=b'\xff'*length
    path.write_bytes(data);result['outputs'][0]['sha256']=f.file_sha(path)
    with pytest.raises(ValueError,match='decode'):f.validate_media(p,result['outputs'])


def test_source_hash_reused_between_decisions_but_forced_on_run_boundary(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01',));s=state(f,p)
    cache=f._sibling('verification_cache_v1326');cache.clear()
    assert f.decide_next(p,s,session_owner='session-A')['allowed']
    assert f.decide_next(p,s,session_owner='session-A')['allowed']
    assert cache.stats['hash_reads']==1
    f.authenticate_context(p,s,'session-A',force_source=True)
    assert cache.stats['hash_reads']==2


def test_cached_file_still_requires_read_access(tmp_path,monkeypatch):
    f=module();path=tmp_path/'file';path.write_bytes(b'readable');f.file_sha(path)
    original=Path.open
    def denied(self,*args,**kwargs):
        if self==path:raise PermissionError('access revoked')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',denied)
    with pytest.raises(PermissionError):f.file_sha(path)


def test_delta_recovery_hot_reads_and_prefix_tampering(tmp_path):
    f=module();journal=f._sibling('project_journal_v1326');journal.clear()
    s={'status':'RUNNING','done':{}}
    for i in range(70):
        s['done'][str(i)]={'payload':'x'*400};f.checkpoint(tmp_path,s)
        assert f.read_checkpoint(tmp_path)==s
    assert journal.stats['ledger_reads']==0
    assert journal.stats['snapshots']==3
    events=f._events(tmp_path);assert 'delta' in events[1] and 'state' in events[31]
    journal.clear();assert f.read_checkpoint(tmp_path)==s
    assert journal.stats['ledger_reads']==1
    ledger=tmp_path/'logs/project_flow_v1325.jsonl';original=ledger.read_bytes();stamp=ledger.stat()
    ledger.write_bytes(original.replace(b'"RUNNING"',b'"CORRUPT"',1));os.utime(ledger,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    with pytest.raises(ValueError,match='hash'):f.read_checkpoint(tmp_path)
    assert ledger.read_bytes()!=original  # no automatic rewrite or truncate


def test_torn_tail_blocks_without_destroying_committed_prefix(tmp_path):
    f=module();s={'status':'RUNNING'};f.checkpoint(tmp_path,s)
    ledger=tmp_path/'logs/project_flow_v1325.jsonl';original=ledger.read_bytes()
    with ledger.open('ab') as stream:stream.write(b'{"schema":')
    with pytest.raises(ValueError,match='incomplete'):f.read_checkpoint(tmp_path)
    assert ledger.read_bytes()==original+b'{"schema":'


def test_v2_ledger_is_read_and_appended_without_migration(tmp_path):
    f=module();logs=tmp_path/'logs';logs.mkdir();ledger=logs/'project_flow_v1325.jsonl'
    s={'status':'RUNNING','ledger_seq':1,'state_schema':'project-flow.v2'}
    entry={'schema':'project-flow-event.v2','seq':1,'previous_hash':None,'timestamp':'2026-01-01','event':'CHECKPOINT','details':{},'state':s}
    entry['event_hash']=f.hash_plan(entry);original=(json.dumps(entry)+'\n').encode();ledger.write_bytes(original)
    assert f.read_checkpoint(tmp_path)==s and ledger.read_bytes()==original
    s['status']='WAITING_USER';f.checkpoint(tmp_path,s)
    assert ledger.read_bytes().startswith(original)
    assert all(e['schema']=='project-flow-event.v2' for e in f._events(tmp_path))


def test_stale_state_cannot_append(tmp_path):
    f=module();s={'status':'RUNNING'};f.checkpoint(tmp_path,s);stale=copy.deepcopy(s)
    f.checkpoint(tmp_path,s)
    with pytest.raises(ValueError,match='stale'):f.checkpoint(tmp_path,stale)


@pytest.mark.skipif(os.name!='nt',reason='Windows junction semantics')
def test_junction_cannot_escape_artifact_or_checkpoint_root(tmp_path):
    f=module();outside=tmp_path/'outside';outside.mkdir();(outside/'keep').write_bytes(b'unchanged')
    job=tmp_path/'job';job.mkdir()
    subprocess.run(['powershell','-NoProfile','-Command',"$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:REVIEW_TEST_LINK -Target $env:REVIEW_TEST_TARGET | Out-Null"],
        env={**os.environ,'REVIEW_TEST_LINK':str(job/'redirect'),'REVIEW_TEST_TARGET':str(outside)},check=True,capture_output=True)
    try:
        report=f.validate_artifacts(job,[{'relative_path':'redirect/keep','sha256':f.file_sha(outside/'keep')}],['redirect/keep'])
        assert not report['ok']
        with pytest.raises(ValueError,match='redirect'):f.checkpoint(job/'redirect',{'status':'RUNNING'})
        assert (outside/'keep').read_bytes()==b'unchanged' and not (outside/'logs').exists()
    finally:(job/'redirect').rmdir()
