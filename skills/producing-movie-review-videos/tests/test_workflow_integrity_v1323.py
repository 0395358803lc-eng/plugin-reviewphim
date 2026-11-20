"""End-to-end offline contract for the single v1.3.23 stage gate; no remote I/O."""
import importlib.util
import hashlib
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('integrity',ROOT/'tools'/'workflow_integrity_v1323.py')
assert spec and spec.loader
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

STAGES=['G01','G02','G03','G04','G05','G06','G07','G08','G09','G10','G11','G11A','G11B','G12','G13','G14','G15']
TASKS={'G01':'G01.SOURCE.FULL','G02':'G02.ASR.FULL','G03':'G03.TRANSLATE.FULL',
       'G04':'G04.FILM.UNDERSTANDING.FULL','G05':'G05.REVIEW.FULL',
       'G11A':'G11A.YOUTUBE_METADATA.FULL','G11B':'G11B.THUMBNAIL.FULL'}

def task(stage):
    return TASKS.get(stage, stage+'.M01')

def plan(stage):
    return {'WORK_PACKAGE_ID':'WP', 'schema_version':'work-package.v2',
            'deviceId':'device-1','JOB_DIR':'D:\\Job','SOURCE_MOVIE':'D:\\Film\\movie.mp4',
            'source_hash':'a'*64,'allowed_stages':[stage], 'task_ids':[task(stage)],
            'bounded_batches':[],'allowed_read_roots':['D:\\Film'],
            'allowed_write_roots':['D:\\Job'],'repair_budget':{'per_issue':0,'total':0,'allowed_kinds':[]},
            'install_budget':[], 'human_gates':[], 'allowed_executables_and_models':[],
            'expected_outputs':[], 'acceptance_criteria':[], 'stop_conditions':[]}

def state(p):
    return {'status':'RUNNING','plan_hash':v.hash_plan(p),'approved_plan_hash':v.hash_plan(p),
            'approval_ref':'user-msg','WORK_PACKAGE_ID':p['WORK_PACKAGE_ID'],
            'deviceId':p['deviceId'],'JOB_DIR':p['JOB_DIR'], 'source_hash':p['source_hash'],
            'lock_owner':'session-1','lock_verified':True,
            'allowed_tasks':p['task_ids'], 'task_qc':{},'qc_gates_passed':[],
            'approved_human_gates':[], 'stage_evidence':{},'unresolved_blockers':[],
            'final_qc':False}

def allowed(p,s):
    return v.decide_dispatch(p,s,task(p['allowed_stages'][0]),session_owner='session-1')


def test_requires_plan_and_explicit_task_scope():
    p=plan('G08');v.validate_new_package(p)
    with pytest.raises(ValueError):v.validate_new_package({**p,'bounded_batches':[{'stem':'G04.M02','start':1,'end':1}]})
    with pytest.raises(ValueError):v.validate_new_package({**plan('G04'),'task_ids':['G04.M01']})
    with pytest.raises(ValueError):v.validate_new_package({**plan('G05'),'task_ids':['G05.M01']})
    with pytest.raises(ValueError):v.validate_new_package({**plan('G01'),'task_ids':['G01.M01']})
    with pytest.raises(ValueError):v.validate_new_package({**plan('G03'),'task_ids':['G03.M02.B001']})
    with pytest.raises(ValueError):v.validate_new_package({**plan('G11B'),'task_ids':['G11B.M01']})

@pytest.mark.parametrize('stage,dependency', [('G02','Q01'),('G03','Q02'),('G04','Q03'),('G05','Q04'),
  ('G06','Q05'),('G07','Q06'),('G08','Q07'),('G09','Q08'),('G10','Q09'),('G11','Q10'),
  ('G11A','Q11'),('G11B','Q11A'),('G12','Q11B'),('G13','Q12'),('G14','Q13'),('G15','Q14')])
def test_every_stage_dependency_blocks_until_pass(stage,dependency):
    p=plan(stage);s=state(p)
    assert not allowed(p,s).allowed,stage
    s['qc_gates_passed']=[dependency]
    # Complete all other stage-specific requirements before expecting success.
    if stage in ('G06','G07','G08','G09','G10','G11','G11A','G11B','G12','G13','G14','G15'):
        s['approved_human_gates'].append('G05_SCRIPT')
    if stage in ('G07','G08','G09','G10','G11','G11A','G11B','G12','G13','G14','G15'):
        s['approved_human_gates'].append('G07_VOICE')
    if stage in ('G11','G11A','G11B','G12','G13','G14','G15'):
        s['approved_human_gates'].append('G10_PILOT')
    if stage in ('G11B','G12','G13','G14','G15'):
        s['approved_human_gates'].append('G11A_METADATA')
    if stage in ('G12','G13','G14','G15'):
        s['approved_human_gates'].append('G11B_THUMBNAIL')
    if stage in ('G05','G09'):
        s['stage_evidence'][dependency]={'visual_inspected':True,'source_hash':'a'*64}
    if stage=='G12':
        s['stage_evidence']['Q11B']={'thumbnail_file_verified':True,'thumbnail_approval_hash_matches':True}
    if stage=='G15':
        s['g14_axes']={'TECHNICAL_STATUS':'PASS','STORY_STATUS':'PASS','VISUAL_EDITING_STATUS':'PASS'}
        s['stage_evidence']['Q14']={'actual_video_inspected':True,'audio_inspected':True}
    assert allowed(p,s).allowed, (stage,allowed(p,s))


def test_voice_sample_without_gate_but_tts_requires_gate():
    p=plan('G07');p['task_ids']=['G07.M01','G07.M03'];s=state(p)
    s['allowed_tasks']=p['task_ids'];s['qc_gates_passed']=['Q06']
    s['approved_human_gates']=['G05_SCRIPT']
    assert v.decide_dispatch(p,s,'G07.M01',session_owner='session-1').allowed
    assert not v.decide_dispatch(p,s,'G07.M03',session_owner='session-1').allowed
    s['approved_human_gates'].append('G07_VOICE')
    assert v.decide_dispatch(p,s,'G07.M03',session_owner='session-1').allowed


def test_no_bypass_from_second_qc_field_or_missing_lock():
    p=plan('G12');s=state(p)
    s['passed_qc']=['Q11B'];s['qc_gates_passed']=[]
    assert not allowed(p,s).allowed
    s['qc_gates_passed']=['Q11B'];s['lock_verified']=False
    assert not allowed(p,s).allowed


def test_cross_package_thumbnail_gate_works_when_approved_in_earlier_package():
    p=plan('G12');s=state(p)
    s['qc_gates_passed']=['Q11B'];s['approved_human_gates']=['G05_SCRIPT','G07_VOICE','G10_PILOT','G11A_METADATA','G11B_THUMBNAIL']
    s['stage_evidence']['Q11B']={'thumbnail_file_verified':True,'thumbnail_approval_hash_matches':True}
    assert allowed(p,s).allowed # G11A/B NOT in current plan: completed previous work packages.


def test_completion_blocks_missing_human_gates_and_qc_and_real_media():
    for stage,gate in [('G05','G05_SCRIPT'),('G07','G07_VOICE'),('G10','G10_PILOT'),('G11A','G11A_METADATA'),('G11B','G11B_THUMBNAIL')]:
        p=plan(stage);s=state(p);s['task_qc'][task(stage)]='PASS';s['final_qc']=True;s['qc_gates_passed']=['Q'+stage[1:]]
        assert not v.validate_package_completion(p,s).allowed
        s['approved_human_gates']=[gate]
        if stage=='G11B':
            # v1.3.24: human approval is necessary but file presence/hash is separate.
            assert not v.validate_package_completion(p,s).allowed
            s['stage_evidence']['Q11B']={'thumbnail_file_verified':True,
                                          'thumbnail_approval_hash_matches':True}
        assert v.validate_package_completion(p,s).allowed
    p=plan('G14');s=state(p);s['task_qc'][task('G14')]='PASS';s['final_qc']=True;s['qc_gates_passed']=['Q14']
    assert not v.validate_package_completion(p,s).allowed
    s['g14_axes']={'TECHNICAL_STATUS':'PASS','STORY_STATUS':'PASS','VISUAL_EDITING_STATUS':'PASS'}
    s['stage_evidence']['Q14']={'actual_video_inspected':True,'audio_inspected':True}
    assert v.validate_package_completion(p,s).allowed


def test_no_delete_without_specific_approved_scope():
    p=plan('G15');p['task_ids']=['G15.M05'];s=state(p);s['allowed_tasks']=p['task_ids'];s['qc_gates_passed']=['Q14']
    s['g14_axes']={'TECHNICAL_STATUS':'PASS','STORY_STATUS':'PASS','VISUAL_EDITING_STATUS':'PASS'}
    s['stage_evidence']['Q14']={'actual_video_inspected':True,'audio_inspected':True}
    s['approved_human_gates']=['G05_SCRIPT','G07_VOICE','G10_PILOT','G11A_METADATA','G11B_THUMBNAIL','G15_DELETE']
    assert not v.decide_dispatch(p,s,'G15.M05',session_owner='session-1').allowed
    p['delete_paths']=['temp/old.mp4'];s['plan_hash']=v.hash_plan(p);s['approved_plan_hash']=s['plan_hash']
    assert v.decide_dispatch(p,s,'G15.M05',session_owner='session-1').allowed


def test_duplicate_pass_does_not_run_again():
    p=plan('G01');s=state(p);s['task_qc'][task('G01')]='PASS'
    assert not allowed(p,s).allowed


def test_wrong_hash_device_owner_or_scope_blocks():
    p=plan('G01');s=state(p)
    assert allowed(p,s).allowed
    for key,value in [('deviceId','device-2'),('source_hash','b'*64),('approved_plan_hash','a'*64),('lock_owner','different-owner')]:
        bad={**s,key:value}
        assert not allowed(p,bad).allowed
    assert not v.decide_dispatch(p,s,'G01.M42',session_owner='session-1').allowed


def test_reuse_only_with_verified_bytes_and_same_input(tmp_path):
    job=tmp_path/'job';job.mkdir();out=job/'audio.wav';out.write_bytes(b'synthetic-audio')
    h=hashlib.sha256(out.read_bytes()).hexdigest()
    rec={'task_id':'G07.M03','qc_status':'PASS','source_hash':'a'*64,
         'inputs':{'script':'b'*64}, 'outputs':[{'relative_path':'audio.wav','sha256':h}]}
    assert v.reuse_evidence(job,rec,source_hash='a'*64,inputs={'script':'b'*64}).allowed
    assert not v.reuse_evidence(job,rec,source_hash='a'*64,inputs={'script':'c'*64}).allowed
    out.write_bytes(b'corrupted')
    assert not v.reuse_evidence(job,rec,source_hash='a'*64,inputs={'script':'b'*64}).allowed


def test_g03_uses_validated_cleaned_transcript_or_blocks():
    assert v.select_g03_transcript({'cleaned_verified':True,'cleaned_path':'analysis/transcript_cleaned.v1.jsonl',
      'original_path':'analysis/transcript_original.jsonl'})=='analysis/transcript_cleaned.v1.jsonl'
    with pytest.raises(ValueError):v.select_g03_transcript({'cleaned_declared':True,'cleaned_verified':False,
      'original_path':'analysis/transcript_original.jsonl'})
    assert v.select_g03_transcript({'original_verified':True,'original_path':'analysis/transcript_original.jsonl'})=='analysis/transcript_original.jsonl'


def test_new_plugin_policy_boundaries_exist():
    doc=(ROOT/'references'/'FULL_WORKFLOW_INTEGRITY_V1323.md').read_text('utf-8')
    skill=(ROOT/'SKILL.md').read_text('utf-8')
    assert 'workflow_integrity_v1323.py' in skill
    for x in ('G07_VOICE','G10_PILOT','G11A_METADATA','G11B_THUMBNAIL','G15_DELETE','G14','single-pass','NO_STAGE_SPLIT','G03'):
        assert x in doc


def test_legacy_no_thumbnail_package_keeps_original_q11_g12_route():
    p=plan('G12');s=state(p)
    s['qc_gates_passed']=['Q11']
    s['approved_human_gates']=['G05_SCRIPT','G07_VOICE','G10_PILOT']
    s['legacy_package_verified']=True
    s['legacy_without_thumbnail_verified']=True
    assert v.decide_dispatch(p,s,task('G12'),session_owner='session-1',legacy=True).allowed
    # Without explicit legacy verification, this must NOT be interpreted as permission.
    s['legacy_package_verified']=False
    assert not v.decide_dispatch(p,s,task('G12'),session_owner='session-1',legacy=True).allowed


def test_completion_requires_active_owner_and_exact_source_hash():
    p=plan('G01');s=state(p);s['qc_gates_passed']=['Q01'];s['task_qc'][task('G01')]='PASS';s['final_qc']=True
    assert v.validate_package_completion(p,s).allowed
    for key,bad in [('status','BLOCKED'),('source_hash','b'*64),('approved_plan_hash','0'*64),('lock_verified',False)]:
        ss={**s,key:bad}
        assert not v.validate_package_completion(p,ss).allowed
