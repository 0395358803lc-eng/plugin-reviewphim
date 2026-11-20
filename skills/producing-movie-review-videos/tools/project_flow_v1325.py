"""REVIEW_PHIM v1.3.25 project-level Production First orchestrator.

Runs finite authorized task callbacks in order, persists real artifact-completion
records and waits for final user acceptance. The host/ChatGPT must implement the
executor callback with approved Remote_Desktop_Commander tools or run this code
on an authorized machine; this module cannot itself invoke ChatGPT, connected
Remote Desktop tools, image generation, FFmpeg or make background chat turns.

This module does NOT bypass approved filesystem/installation/publishing scope.
It never treats aesthetic/narrative QC as a prerequisite for task advancement.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Callable, Any

MODE='PRODUCTION_FIRST_V1325'
STAGE_SEQUENCE=('P00','G01','G02','G03','G04','G05','G06','G07','G08','G09',
                'G10','G11','G11A','G11B','G12','G13','G14','G15')
CREATIVE_GATES={
    'G05':'G05_SCRIPT', 'G07':'G07_VOICE', 'G10':'G10_PILOT',
    'G11A':'G11A_METADATA', 'G11B':'G11B_THUMBNAIL',
}
ATOMIC={
    'G01':'G01.SOURCE.FULL','G02':'G02.ASR.FULL','G03':'G03.TRANSLATE.FULL',
    'G04':'G04.FILM.UNDERSTANDING.FULL','G05':'G05.REVIEW.FULL',
    'G11A':'G11A.YOUTUBE_METADATA.FULL','G11B':'G11B.THUMBNAIL.FULL',
}
STATUS={'PENDING','RUNNING','DONE','WARNING','FAILED','WAITING_USER',
        'FINAL_REVIEW','PACKAGE_DONE','ACCEPTED','REVISION_REQUESTED'}


def hash_plan(plan:dict[str,Any])->str:
    if not isinstance(plan,dict) or 'plan_hash' in plan:
        raise ValueError('invalid or self-referential plan')
    raw=json.dumps(plan,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def stage_of(task:str)->str:
    return task.split('.',1)[0] if isinstance(task,str) else ''


def validate_plan(plan:dict[str,Any])->list[str]:
    fields=('WORK_PACKAGE_ID','schema_version','deviceId','JOB_DIR','SOURCE_MOVIE','source_hash',
            'allowed_stages','task_ids','allowed_read_roots','allowed_write_roots',
            'repair_budget','install_budget','human_gates','creative_delegations','stage_outputs')
    if not isinstance(plan,dict) or any(k not in plan for k in fields):
        raise ValueError('missing approved work-package fields')
    if plan.get('execution_mode')!=MODE or plan['schema_version']!='work-package.v2':
        raise ValueError('not an explicitly selected Production First package')
    if not all(isinstance(plan[k],str) and plan[k] for k in ('WORK_PACKAGE_ID','deviceId','JOB_DIR','SOURCE_MOVIE')):
        raise ValueError('invalid package/device/directory/source')
    source_hash=plan['source_hash']
    if not (isinstance(source_hash,str) and
            (len(source_hash)==64 and all(c in '0123456789abcdef' for c in source_hash) or
             source_hash=='UNKNOWN' and plan['allowed_stages']==['P00'])):
        raise ValueError('invalid source SHA or unbounded P00 UNKNOWN')
    tasks=plan['task_ids'];stages=plan['allowed_stages']
    if not isinstance(tasks,list) or not isinstance(stages,list) or not tasks or len(tasks)>100:
        raise ValueError('empty or unbounded task list')
    if not all(isinstance(t,str) and '.' in t and len(t)<160 and '*' not in t and '?' not in t for t in tasks):
        raise ValueError('invalid task identifiers')
    if not all(s in STAGE_SEQUENCE for s in stages) or stages!=sorted(set(stages),key=STAGE_SEQUENCE.index):
        raise ValueError('stages must be unique and ordered')
    if len(tasks)!=len(stages) or [stage_of(t) for t in tasks]!=stages:
        raise ValueError('one task per stage in Production First')
    if plan.get('bounded_batches'):
        raise ValueError('no approval micro-batches in Production First')
    if any(s in ATOMIC and t!=ATOMIC[s] for s,t in zip(stages,tasks)):
        raise ValueError('atomic stage task mismatch')
    outs=plan['stage_outputs']
    if not isinstance(outs,dict) or set(outs)!=set(stages):
        raise ValueError('output contract required for every scoped stage')
    if not all(isinstance(v,list) and len(v)>0 and all(isinstance(f,str) and f and _safe_relative(f) for f in v) for v in outs.values()):
        raise ValueError('invalid required stage output paths')
    creative=plan['creative_delegations']
    if not isinstance(creative,list) or len(creative)!=len(set(creative)) or not set(creative)<=set(CREATIVE_GATES.values()):
        raise ValueError('unsupported or blanket creative delegation')
    for field in ('allowed_read_roots','allowed_write_roots','human_gates','install_budget'):
        if not isinstance(plan[field],list):raise ValueError('bad '+field)
    # A single approval cannot silently write in a different JOB_DIR or read
    # another source. Strict path containment works for native Windows paths
    # when this module runs on the selected remote Windows device.
    job=Path(plan['JOB_DIR']).resolve(strict=False)
    source=Path(plan['SOURCE_MOVIE']).resolve(strict=False)
    def in_roots(candidate, roots):
        return any(candidate==r or r in candidate.parents for r in
                   (Path(p).resolve(strict=False) for p in roots if isinstance(p,str) and p))
    if not in_roots(job,plan['allowed_write_roots']):
        raise ValueError('JOB_DIR is outside approved write roots')
    if not in_roots(source,plan['allowed_read_roots']):
        raise ValueError('source movie is outside approved read roots')
    if not isinstance(plan['repair_budget'],dict):raise ValueError('bad repair budget')
    for t in tasks:
        if t.startswith('G15.M05') and (not plan.get('delete_paths') or 'G15_DELETE' not in plan['human_gates']):
            raise ValueError('delete requires explicit path list and separate gate')
    if 'G15_DELETE' in creative:raise ValueError('deletion cannot be predelegated')
    if 'G15' in stages and not any(p.lower().endswith('.mp4') for p in outs['G15']):
        raise ValueError('G15 must deliver a named final MP4 file')
    hash_plan(plan)
    return tasks


def _safe_relative(s:str)->bool:
    p=PurePosixPath(s)
    return s==str(p) and not s.startswith('/') and '\\' not in s and ':' not in s and '..' not in p.parts and '.' not in p.parts


def validate_artifacts(job_dir:str|Path, outputs:list[dict[str,Any]], required:list[str])->dict[str,Any]:
    """Only completion checks: actual file, bounded path, non-empty bytes and SHA.

    No subjective plot/audio/visual quality scoring and no Qxx stage gates.
    """
    try:
        if not isinstance(outputs,list) or not isinstance(required,list):return {'ok':False,'reason':'invalid output record'}
        root=Path(job_dir).resolve(strict=True)
        names={}
        for item in outputs:
            rel=item.get('relative_path');digest=item.get('sha256')
            if not isinstance(rel,str) or not _safe_relative(rel):return {'ok':False,'reason':'unsafe output path'}
            if rel in names:return {'ok':False,'reason':'duplicate output record'}
            names[rel]=digest
            dest=root.joinpath(*PurePosixPath(rel).parts)
            if dest.is_symlink() or not dest.is_file():return {'ok':False,'reason':'missing/symlink output '+rel}
            real=dest.resolve(strict=True)
            if root not in real.parents:return {'ok':False,'reason':'output escapes job root'}
            if real.stat().st_size==0:return {'ok':False,'reason':'empty output '+rel}
            if not isinstance(digest,str) or len(digest)!=64:return {'ok':False,'reason':'missing output SHA256'}
            h=hashlib.sha256()
            with real.open('rb') as f:
                for buf in iter(lambda:f.read(1048576),b''):h.update(buf)
            if h.hexdigest()!=digest:return {'ok':False,'reason':'output SHA256 mismatch '+rel}
        if not set(required)<=set(names):return {'ok':False,'reason':'required output missing'}
        return {'ok':True,'reason':'required artifacts exist, readable as bytes and SHA256 matched'}
    except (ValueError,OSError,TypeError,AttributeError) as e:return {'ok':False,'reason':str(e)}


def decide_next(plan:dict[str,Any],state:dict[str,Any],*,session_owner:str)->dict[str,Any]:
    """Select the next scoped task based on DONE artifacts, not QC gates."""
    try:
        tasks=validate_plan(plan)
        if not isinstance(state,dict) or state.get('status')!='RUNNING':return {'allowed':False,'reason':'not running'}
        digest=hash_plan(plan)
        if not state.get('approval_ref') or state.get('plan_hash')!=digest or state.get('approved_plan_hash')!=digest:
            return {'allowed':False,'reason':'approval/plan hash mismatch'}
        for key in ('deviceId','JOB_DIR','source_hash'):
            if state.get(key)!=plan.get(key):return {'allowed':False,'reason':key+' mismatch'}
        if state.get('allowed_tasks')!=tasks:return {'allowed':False,'reason':'approved task list mismatch'}
        if not session_owner or state.get('lock_owner')!=session_owner or state.get('lock_verified') is not True:
            return {'allowed':False,'reason':'lock not authenticated'}
        if state.get('unresolved_blockers'):return {'allowed':False,'reason':'unresolved permission/technical blocker'}
        done=state.get('stage_completions',{})
        if not isinstance(done,dict):return {'allowed':False,'reason':'invalid completions'}
        for stage,tid in zip(plan['allowed_stages'],tasks):
            record=done.get(stage)
            if record is not None:
                if record.get('task_id')!=tid or record.get('source_hash')!=plan['source_hash']:
                    return {'allowed':False,'reason':'stored stage lineage mismatch'}
                checked=validate_artifacts(plan['JOB_DIR'],record.get('outputs',[]),plan['stage_outputs'][stage])
                if not checked['ok']:return {'allowed':False,'reason':'completed stage '+stage+' corrupted: '+checked['reason']}
                continue
            if tid.startswith('G15.M05') and ('G15_DELETE' not in state.get('approved_human_gates',[]) or not plan.get('delete_paths')):
                return {'allowed':False,'reason':'G15_DELETE explicit approval missing'}
            gate=CREATIVE_GATES.get(stage)
            if gate and gate not in plan['creative_delegations'] and gate not in state.get('approved_human_gates',[]):
                return {'allowed':True,'next_stage':stage,'next_task':tid,'needs_user':True,'reason':gate}
            return {'allowed':True,'next_stage':stage,'next_task':tid,'needs_user':False,'reason':'ready'}
        return {'allowed':True,'next_stage':None,'next_task':None,'needs_user':False,'reason':'all scoped tasks completed'}
    except (ValueError,TypeError,AttributeError,KeyError) as e:
        return {'allowed':False,'reason':str(e)}


def _append_log(root:Path,event:dict[str,Any])->None:
    ledger=root/'logs'/'project_flow_v1325.jsonl'
    ledger.parent.mkdir(parents=True,exist_ok=True)
    with ledger.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(event,ensure_ascii=False,sort_keys=True)+'\n')
        stream.flush();os.fsync(stream.fileno())


def checkpoint(root:Path,state:dict[str,Any])->None:
    target=root/'logs'/'project_flow_v1325.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix('.json.tmp')
    with temp.open('w',encoding='utf-8') as stream:
        json.dump(state,stream,ensure_ascii=False,sort_keys=True,indent=2)
        stream.flush();os.fsync(stream.fileno())
    os.replace(temp,target)


def read_checkpoint(job_dir:str|Path)->dict[str,Any]:
    return json.loads((Path(job_dir)/'logs'/'project_flow_v1325.json').read_text(encoding='utf-8'))


def run_until_hinge(plan:dict[str,Any],state:dict[str,Any],
                    executor:Callable[[str,str],dict[str,Any]],*,session_owner:str,
                    persist:bool=False,max_steps:int|None=None)->dict[str,Any]:
    """Synchronous finite loop: callback MUST execute authorized real tools.

    Host supplies a real executor (usually ChatGPT via Remote Desktop Commander).
    No implicit async/background operation. max_steps can bound a chat turn.
    """
    validate_plan(plan)
    if not callable(executor):raise ValueError('real authorized executor callback required')
    root=Path(plan['JOB_DIR'])
    s={**state,'stage_completions':dict(state.get('stage_completions') or {})}
    s.setdefault('quality_qc_invocations',0)
    steps=0
    while max_steps is None or steps<max_steps:
        choice=decide_next(plan,s,session_owner=session_owner)
        if not choice['allowed']:
            # Never overwrite a terminal review or move ahead after tampering.
            s['last_blocker']=choice['reason']
            return s
        stage=choice['next_stage']
        if stage is None:
            s['status']='FINAL_REVIEW' if 'G15' in plan['allowed_stages'] else 'PACKAGE_DONE'
            s['next_stage']=None
            if persist:checkpoint(root,s);_append_log(root,{'event':s['status'],'plan_hash':hash_plan(plan)})
            return s
        if choice['needs_user']:
            s.update(status='WAITING_USER',next_stage=stage,wait_reason=choice['reason'])
            if persist:checkpoint(root,s);_append_log(root,{'event':'WAITING_USER','stage':stage,'reason':choice['reason']})
            return s
        task=choice['next_task']
        try:
            result=executor(task,stage)
        except Exception as exc:
            s.update(status='FAILED',next_stage=stage,last_blocker='executor raised: '+str(exc))
            if persist:checkpoint(root,s);_append_log(root,{'event':'FAILED','stage':stage,'reason':s['last_blocker']})
            return s
        if not isinstance(result,dict) or result.get('status') not in {'DONE','WARNING','WAITING_USER','FAILED'}:
            s.update(status='FAILED',next_stage=stage,last_blocker='executor did not return completion evidence')
            if persist:checkpoint(root,s);_append_log(root,{'event':'FAILED','stage':stage,'reason':s['last_blocker']})
            return s
        if result['status']=='WAITING_USER':
            s.update(status='WAITING_USER',next_stage=stage,wait_reason=result.get('reason') or 'EXTERNAL_ACTION')
            if persist:checkpoint(root,s);_append_log(root,{'event':'WAITING_USER','stage':stage,'reason':s['wait_reason']})
            return s
        if result['status']=='FAILED':
            s.update(status='FAILED',next_stage=stage,last_blocker=result.get('reason') or 'task failed')
            if persist:checkpoint(root,s);_append_log(root,{'event':'FAILED','stage':stage,'reason':s['last_blocker']})
            return s
        checked=validate_artifacts(root,result.get('outputs',[]),plan['stage_outputs'][stage])
        if not checked['ok']:
            s.update(status='FAILED',next_stage=stage,last_blocker=checked['reason'])
            if persist:checkpoint(root,s);_append_log(root,{'event':'FAILED','stage':stage,'reason':checked['reason']})
            return s
        if stage=='G11B' and result.get('user_image_placement_verified') is not True:
            s.update(status='FAILED',next_stage=stage,last_blocker='manual thumbnail file/title/approval evidence missing')
            if persist:checkpoint(root,s);_append_log(root,{'event':'FAILED','stage':stage,'reason':s['last_blocker']})
            return s
        if stage in {'G11','G14','G15'} and result.get('technical_ready') is not True:
            s.update(status='FAILED',next_stage=stage,last_blocker='render/MP4 technical readiness missing')
            if persist:checkpoint(root,s);_append_log(root,{'event':'FAILED','stage':stage,'reason':s['last_blocker']})
            return s
        record={'task_id':task,'source_hash':plan['source_hash'],'plan_hash':hash_plan(plan),
                'outputs':result['outputs'],'completion_status':'DONE',
                'warnings':list(result.get('warnings',[]))}
        s['stage_completions'][stage]=record
        s['status']='RUNNING'
        s.pop('wait_reason',None);s.pop('last_blocker',None)
        if persist:checkpoint(root,s);_append_log(root,{'event':'STAGE_DONE','stage':stage,'task_id':task,'outputs':record['outputs']})
        steps+=1
    next_item=decide_next(plan,s,session_owner=session_owner)
    if next_item.get('allowed') and next_item.get('next_task') is None:
        s['status']='FINAL_REVIEW' if 'G15' in plan['allowed_stages'] else 'PACKAGE_DONE'
        s['next_stage']=None
        if persist:_append_log(root,{'event':s['status'],'plan_hash':hash_plan(plan)})
    else:
        s['status']='RUNNING';s['next_stage']=next_item.get('next_stage')
    if persist:checkpoint(root,s)
    return s


def user_review(plan:dict[str,Any],state:dict[str,Any],*,action:str,user_ref:str,
                notes:str,targets:list[str]|None=None)->dict[str,Any]:
    """No self-approval. Record final verdict, preserve original stage outputs."""
    validate_plan(plan)
    if ('G15' not in plan['allowed_stages'] or state.get('status')!='FINAL_REVIEW'
            or not isinstance(user_ref,str) or not user_ref.strip()):
        raise ValueError('final review and authentic user message required')
    if state.get('plan_hash')!=hash_plan(plan):raise ValueError('review plan mismatch')
    if action not in {'ACCEPTED','REVISION_REQUESTED'}:raise ValueError('unknown review decision')
    updated={**state,'stage_completions':dict(state['stage_completions'])}
    if action=='ACCEPTED':
        updated['status']='ACCEPTED';updated['acceptance']={'user_ref':user_ref,'notes':notes}
    else:
        if not isinstance(targets,list) or not targets or not all(t in plan['allowed_stages'] for t in targets):
            raise ValueError('revision requires specific previously authorized stages')
        updated['status']='REVISION_REQUESTED'
        updated['revision_requests']=list(state.get('revision_requests',[]))+[{
            'user_ref':user_ref,'notes':notes,'targets':targets,
            'requires_new_revision_scope':True}]
    return updated


def resume_after_user(plan:dict[str,Any],state:dict[str,Any],*,
                      action:str,user_ref:str,evidence:dict[str,Any]|None=None)->dict[str,Any]:
    """Resume the SAME bounded package after an actual user action.

    For thumbnail handoff FILE_ACCEPTED must have been obtained by a real
    remote bytes inspection; the subsequent executor must still recheck the
    actual file before marking the G11B stage DONE.
    """
    validate_plan(plan)
    if state.get('status')!='WAITING_USER' or state.get('plan_hash')!=hash_plan(plan):
        raise ValueError('no matching user wait for this plan')
    if not isinstance(user_ref,str) or not user_ref.strip():
        raise ValueError('real user message reference required')
    reason=state.get('wait_reason')
    if action!=reason:raise ValueError('user action does not resolve the waiting reason')
    if reason=='USER_IMAGE_PLACEMENT':
        if not isinstance(evidence,dict) or evidence.get('status')!='FILE_ACCEPTED':
            raise ValueError('thumbnail bytes must be inspected before resume')
    elif reason not in CREATIVE_GATES.values() and reason!='EXTERNAL_INPUT':
        raise ValueError('unexpected or unsupported user wait')
    out={**state,'status':'RUNNING','external_resolved_by':user_ref}
    out.pop('wait_reason',None)
    if reason in CREATIVE_GATES.values():
        gates=list(out.get('approved_human_gates') or [])
        if reason not in gates:gates.append(reason)
        out['approved_human_gates']=gates
    # Do not record DONE/approval of another stage from a resume message.
    return out


def merge_verified_completions(plan:dict[str,Any],state:dict[str,Any],
                               previous:dict[str,dict[str,Any]],*,
                               expected_inputs:dict[str,dict[str,str]])->dict[str,Any]:
    """Import immutable DONE evidence from a previous approved package.

    Requires exact stage/task, source hash, input hashes, old approval provenance
    and current physical file bytes. Never treats an old QC PASS as proof.
    """
    validate_plan(plan)
    if (state.get('status')!='RUNNING' or state.get('plan_hash')!=hash_plan(plan)
            or state.get('approved_plan_hash')!=hash_plan(plan)
            or not state.get('approval_ref') or state.get('lock_verified') is not True):
        raise ValueError('current package is not authorized for evidence import')
    if not isinstance(previous,dict) or not isinstance(expected_inputs,dict):
        raise ValueError('invalid previous records')
    stages=dict(zip(plan['allowed_stages'],plan['task_ids']))
    out={**state,'stage_completions':dict(state.get('stage_completions') or {})}
    for stage,record in previous.items():
        if stage not in stages or stage in out['stage_completions']:
            raise ValueError('cannot import outside scope or overwrite existing stage')
        if (not isinstance(record,dict) or record.get('task_id')!=stages[stage] or
                record.get('source_hash')!=plan['source_hash'] or
                record.get('completion_status')!='DONE' or not record.get('approval_ref') or
                not record.get('WORK_PACKAGE_ID') or
                not isinstance(record.get('plan_hash'),str) or len(record['plan_hash'])!=64):
            raise ValueError('unverifiable previous work package provenance')
        if (stage not in expected_inputs or not expected_inputs[stage] or
                record.get('inputs')!=expected_inputs[stage]):
            raise ValueError('cannot reuse output with changed or unknown input hashes')
        verified=validate_artifacts(plan['JOB_DIR'],record.get('outputs',[]),plan['stage_outputs'][stage])
        if not verified['ok']:raise ValueError('previous stage bytes failed: '+verified['reason'])
        out['stage_completions'][stage]={
            'task_id':stages[stage],'source_hash':plan['source_hash'],
            'plan_hash':hash_plan(plan),'inputs':record['inputs'],
            'completion_status':'DONE','outputs':record['outputs'],
            'imported_from_package':record['WORK_PACKAGE_ID'],
            'imported_approval_ref':record['approval_ref'],
        }
    return out
