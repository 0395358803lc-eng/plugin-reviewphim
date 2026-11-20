"""REVIEW_PHIM v1.3.26 project-level Production First orchestrator.

Runs finite authorized task callbacks in order, persists real artifact-completion
records and waits for final user acceptance. The host/ChatGPT must implement the
executor callback with approved Remote_Desktop_Commander tools or run this code
on an authorized machine; this module cannot itself invoke ChatGPT, connected
Remote Desktop tools, image generation or make background chat turns. Approved
local FFprobe/FFmpeg are invoked only for technical media validation.

This module does NOT bypass approved filesystem/installation/publishing scope.
It never treats aesthetic/narrative QC as a prerequisite for task advancement.
"""
from __future__ import annotations

import hashlib
import json
import os
import copy
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
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


def _sibling(name):
    from importlib.util import module_from_spec, spec_from_file_location
    shared=name in {'verification_cache_v1326','project_journal_v1326'}
    key='_review_phim_'+hashlib.sha256(str(Path(__file__).parent.resolve()).encode()).hexdigest()[:12]+'_'+name
    if shared and key in sys.modules:return sys.modules[key]
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    if shared:sys.modules[key]=module
    return module


def file_sha(path,*,force=False):
    return _sibling('verification_cache_v1326').file_sha(path,force=force)


def authenticate_context(plan,state,owner,*,force_source=False):
    validate_plan(plan)
    digest=hash_plan(plan)
    if not state.get('approval_ref') or any(state.get(k)!=digest for k in ('plan_hash','approved_plan_hash')):
        raise ValueError('approval/plan hash mismatch')
    for key in ('deviceId','JOB_DIR','source_hash'):
        if state.get(key)!=plan[key]:raise ValueError(key+' mismatch')
    if state.get('allowed_tasks')!=plan['task_ids']:raise ValueError('approved task list mismatch')
    if not owner or state.get('lock_owner')!=owner:raise ValueError('lock owner mismatch')
    _sibling('work_package_state').verify_lock(Path(plan['JOB_DIR'])/'logs'/'work_package.lock',
        owner=owner,package_id=plan['WORK_PACKAGE_ID'],plan_hash=digest,device_id=plan['deviceId'])
    if plan['source_hash']!='UNKNOWN' and file_sha(plan['SOURCE_MOVIE'],force=force_source)!=plan['source_hash']:
        raise ValueError('source file SHA256 mismatch')
    if state.get('unresolved_blockers'):raise ValueError('unresolved permission/technical blocker')
    ledger=Path(plan['JOB_DIR'])/'logs'/'project_flow_v1325.jsonl'
    if ledger.exists():
        head=_ledger_head(plan['JOB_DIR'])
        if head['seq'] and state.get('ledger_seq',0)!=head['seq']:
            raise ValueError('state is stale; reload canonical project ledger before execution')


def validate_media(plan,outputs,*,prior_evidence=None):
    """Probe and fully decode MP4 bytes; no aesthetic/content judgement."""
    videos=[x for x in outputs if x['relative_path'].lower().endswith('.mp4')]
    if not videos:return []
    approved=plan.get('allowed_executables_and_models',[])
    binaries={}
    for name in ('ffprobe','ffmpeg'):
        candidates=[x for x in approved if isinstance(x,str) and Path(x).stem.lower()==name]
        if not candidates:raise PermissionError(name+' is not in approved executable scope')
        binary=shutil.which(candidates[0])
        if not binary:raise FileNotFoundError('approved '+name+' is unavailable; installation is not authorized')
        binaries[name]=binary
    cache=_sibling('verification_cache_v1326')
    tool_identity={name:cache.tool_identity(binary) for name,binary in binaries.items()}
    evidence=[]
    for item in videos:
        path=Path(plan['JOB_DIR'])/item['relative_path']
        signature=cache.fingerprint(path)
        if file_sha(path)!=item['sha256']:raise ValueError('MP4 SHA256 mismatch before verification')
        contract=plan.get('media_contracts',{}).get(item['relative_path'],{})
        requires_audio=contract.get('requires_audio',plan.get('requires_audio',True))
        key=cache.digest({'file':signature,'sha256':item['sha256'],'tools':tool_identity})
        cached=cache.media_get(key) if signature['reliable'] else None
        if cached is None and signature['reliable']:
            # Only caller-verified completion/ledger evidence is eligible here.
            # Executor-supplied media flags are never passed as prior_evidence.
            cached=next((e for e in (prior_evidence or []) if isinstance(e,dict) and cache.sealed_evidence(e)
                and e.get('fingerprint')==signature and e.get('sha256')==item['sha256'] and e.get('tools')==tool_identity),None)
        if cached:
            _check_media_contract(cached,contract,requires_audio)
            cache.stats['media_hits']+=1;evidence.append(copy.deepcopy(cached));continue
        cache.stats['probe_runs']+=1
        probe=subprocess.run([binaries['ffprobe'],'-v','error','-protocol_whitelist','file,pipe',
            '-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,timeout=120)
        if probe.returncode:raise ValueError('invalid MP4 container: '+probe.stderr[-1000:])
        info=json.loads(probe.stdout);fmt=info.get('format',{})
        duration=float(fmt.get('duration',0))
        streams=[s for s in info.get('streams',[]) if s.get('codec_type')=='video' and not s.get('disposition',{}).get('attached_pic')]
        audio=[s for s in info.get('streams',[]) if s.get('codec_type')=='audio']
        if ('mp4' not in fmt.get('format_name','').split(',') or not math.isfinite(duration) or duration<=0
                or not streams or any(not s.get('codec_name') or s.get('width',0)<=0 or s.get('height',0)<=0 for s in streams)):
            raise ValueError('MP4 requires container, positive duration and decodable video stream metadata')
        report={'relative_path':item['relative_path'],'sha256':item['sha256'],
            'duration':duration,'video_streams':streams,'audio_streams':audio,'format_name':fmt['format_name'],
            'probe_exit':probe.returncode,'decode_exit':0,'decoder':binaries['ffmpeg'],
            'fingerprint':signature,'tools':tool_identity,'verification_schema':'media-verification.v2'}
        _check_media_contract(report,contract,requires_audio)
        cache.stats['decode_runs']+=1
        decode=subprocess.run([binaries['ffmpeg'],'-nostdin','-v','error','-xerror',
            '-err_detect','explode','-protocol_whitelist','file,pipe','-i',str(path),
            '-map','0:v','-map','0:a' if requires_audio else '0:a?','-f','null','-'],capture_output=True,text=True,timeout=3600)
        if decode.returncode or decode.stderr.strip():raise ValueError('MP4 decode failed: '+decode.stderr[-1000:])
        if cache.fingerprint(path)!=signature or file_sha(path)!=item['sha256']:raise ValueError('MP4 changed during verification')
        report['verification_sha256']=cache.digest(report)
        cache.media_put(key,report);evidence.append(report)
    return evidence


def _check_media_contract(evidence,contract,requires_audio):
    if evidence.get('decode_exit')!=0 or evidence.get('probe_exit')!=0:raise ValueError('MP4 evidence invalid')
    audio=evidence.get('audio_streams',[])
    if requires_audio and (not audio or any(not s.get('codec_name') or int(s.get('sample_rate',0))<=0
                                          or int(s.get('channels',0))<=0 for s in audio)):
        raise ValueError('MP4 requires a valid audio stream')
    expected=contract.get('expected_duration')
    if expected is not None and abs(evidence['duration']-expected)>contract.get('duration_tolerance',0.25):
        raise ValueError('MP4 duration differs from approved output contract')


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
    if any(not isinstance(p,str) or not Path(p).is_absolute() for p in
           [plan['JOB_DIR'],plan['SOURCE_MOVIE'],*plan['allowed_read_roots'],*plan['allowed_write_roots']]):
        raise ValueError('approved source, JOB_DIR and roots must be absolute native paths')
    def in_roots(candidate, roots):
        return any(candidate==r or r in candidate.parents for r in
                   (Path(p).resolve(strict=False) for p in roots if isinstance(p,str) and p))
    if not in_roots(job,plan['allowed_write_roots']):
        raise ValueError('JOB_DIR is outside approved write roots')
    if not in_roots(source,plan['allowed_read_roots']):
        raise ValueError('source movie is outside approved read roots')
    if not isinstance(plan['repair_budget'],dict):raise ValueError('bad repair budget')
    repair=plan['repair_budget']
    if (any(type(repair.get(k)) is not int or not 0<=repair[k]<=cap for k,cap in (('per_issue',2),('total',4)))
            or repair['per_issue']>repair['total'] or not isinstance(repair.get('allowed_kinds',[]),list)):
        raise ValueError('invalid finite retry budget')
    if not isinstance(plan.get('allowed_executables_and_models'),list):raise ValueError('approved executables required')
    if type(plan.get('requires_audio',True)) is not bool:raise ValueError('requires_audio must be boolean')
    contracts=plan.get('media_contracts',{})
    if not isinstance(contracts,dict):raise ValueError('invalid media contracts')
    all_outputs=[p for paths in outs.values() for p in paths]
    for name,contract in contracts.items():
        if name not in all_outputs or not name.lower().endswith('.mp4') or not isinstance(contract,dict):raise ValueError('unscoped media contract')
        if type(contract.get('requires_audio',plan.get('requires_audio',True))) is not bool:raise ValueError('invalid audio contract')
        for field in ('expected_duration','duration_tolerance'):
            if field in contract and (type(contract[field]) not in (int,float) or not math.isfinite(contract[field]) or contract[field]<0):
                raise ValueError('invalid duration contract')
    if len(all_outputs)!=len(set(all_outputs)):raise ValueError('stages must not overwrite another stage output')
    if any(p.casefold().startswith('logs/') or (job/p).resolve(strict=False)==source for p in all_outputs):
        raise ValueError('stage output would overwrite source or control files')
    dependencies=plan.get('stage_dependencies',{})
    if not isinstance(dependencies,dict) or set(dependencies)-set(stages):raise ValueError('invalid dependency graph')
    for stage,deps in dependencies.items():
        if not isinstance(deps,list) or not set(deps)<=set(stages[:stages.index(stage)]):
            raise ValueError('dependencies must refer to earlier scoped stages')
    proposals=plan.get('stage_proposals',{})
    if not isinstance(proposals,dict) or not set(proposals)<=set(stages)&set(CREATIVE_GATES):
        raise ValueError('invalid stage proposals')
    for paths in proposals.values():
        if not isinstance(paths,list) or not paths or any(not isinstance(p,str) or not _safe_relative(p) or p.casefold().startswith('logs/') or (job/p).resolve(strict=False)==source for p in paths):
            raise ValueError('invalid proposal outputs')
        if set(paths)&set(all_outputs):raise ValueError('proposal and final outputs must be distinct')
    if 'G07' in stages and 'G07_VOICE' not in creative and 'G07' not in proposals:
        raise ValueError('nondelegated G07 requires stage_proposals for the voice sample before bulk TTS')
    for field in ('production_config','stage_config','stage_inputs'):
        if not isinstance(plan.get(field,{}),dict):raise ValueError('invalid '+field)
    for stage,inputs in plan.get('stage_inputs',{}).items():
        if stage not in stages or not isinstance(inputs,dict):raise ValueError('invalid stage inputs')
        for path,digest in inputs.items():
            if (not isinstance(path,str) or not Path(path).is_absolute() or not in_roots(Path(path).resolve(strict=False),plan['allowed_read_roots'])
                    or not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest)):
                raise ValueError('invalid stage input scope/hash')
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
            if any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in (dest,*dest.parents)):
                return {'ok':False,'reason':'output path redirects'}
            if dest.is_symlink() or not dest.is_file():return {'ok':False,'reason':'missing/symlink output '+rel}
            real=dest.resolve(strict=True)
            if root not in real.parents:return {'ok':False,'reason':'output escapes job root'}
            if real.stat().st_size==0:return {'ok':False,'reason':'empty output '+rel}
            if not isinstance(digest,str) or len(digest)!=64:return {'ok':False,'reason':'missing output SHA256'}
            if file_sha(real)!=digest:return {'ok':False,'reason':'output SHA256 mismatch '+rel}
        if not set(required)<=set(names):return {'ok':False,'reason':'required output missing'}
        if set(names)-set(required):return {'ok':False,'reason':'output outside approved stage contract'}
        return {'ok':True,'reason':'required artifacts exist, readable as bytes and SHA256 matched'}
    except (ValueError,OSError,TypeError,AttributeError) as e:return {'ok':False,'reason':str(e)}


def expected_inputs(plan,state,stage):
    inputs={'source':plan['source_hash'],'configuration':hash_plan({
        'production_config':plan.get('production_config',{}),'stage_config':plan.get('stage_config',{}).get(stage,{})})}
    for name,digest in plan.get('stage_inputs',{}).get(stage,{}).items():
        path=Path(name).resolve(strict=True)
        if not any(path==root or root in path.parents for root in (Path(r).resolve(strict=True) for r in plan['allowed_read_roots'])):
            raise ValueError('input outside approved read roots')
        if file_sha(path)!=digest:raise ValueError('stage input hash mismatch')
        inputs[str(path)]=digest
    # Explicit stage dependencies allow a local revision without invalidating
    # unrelated assets. Absent a graph, conservatively bind all earlier outputs.
    dependencies=plan.get('stage_dependencies',{}).get(stage,
        plan['allowed_stages'][:plan['allowed_stages'].index(stage)])
    for prior in dependencies:
        record=state.get('stage_completions',{}).get(prior)
        if record:
            for item in record['outputs']:inputs[item['relative_path']]=item['sha256']
    return inputs


def completion_hash(record):
    return hash_plan({'completion':{k:v for k,v in record.items() if k!='record_sha256'}})


def verify_completion(plan,state,stage,record):
    tid=dict(zip(plan['allowed_stages'],plan['task_ids']))[stage]
    if (not isinstance(record,dict) or record.get('schema')!='stage-completion.v2'
            or record.get('record_sha256')!=completion_hash(record)
            or record.get('JOB_DIR')!=plan['JOB_DIR'] or record.get('deviceId')!=plan['deviceId'] or record.get('task_id')!=tid or
            record.get('source_hash')!=plan['source_hash'] or record.get('completion_status')!='DONE'
            or not record.get('WORK_PACKAGE_ID') or not record.get('approval_ref')
            or not _sibling('work_package_state')._is_digest(record.get('plan_hash'))
            or record.get('inputs')!=expected_inputs(plan,state,stage)):
        raise ValueError('stored stage lineage/inputs mismatch: '+stage)
    checked=validate_artifacts(plan['JOB_DIR'],record.get('outputs',[]),plan['stage_outputs'][stage])
    if not checked['ok']:raise ValueError('completed stage '+stage+' corrupted: '+checked['reason'])
    if stage=='G11B':verify_thumbnail(plan,record.get('thumbnail_evidence'))
    # Hash-bound decoder evidence was created by this runner, never executor flags.
    for item in record['outputs']:
        if item['relative_path'].lower().endswith('.mp4'):
            if not any(e.get('relative_path')==item['relative_path'] and e.get('sha256')==item['sha256']
                       and e.get('decode_exit')==0 and e.get('probe_exit')==0 for e in record.get('media_evidence',[])):
                raise ValueError('verified decoder evidence missing')
    validate_media(plan,record['outputs'],prior_evidence=record.get('media_evidence'))


def decide_next(plan,state,*,session_owner):
    """Select production work; creative approval follows the actual proposal."""
    try:
        authenticate_context(plan,state,session_owner)
        if state.get('status')!='RUNNING':return {'allowed':False,'reason':'not running'}
        if state.get('inflight'):return {'allowed':False,'reason':'interrupted task requires recover; do not execute twice'}
        done=state.get('stage_completions',{})
        if not isinstance(done,dict):raise ValueError('invalid completions')
        for stage,tid in zip(plan['allowed_stages'],plan['task_ids']):
            proposal=state.get('stage_proposals',{}).get(stage)
            if proposal:
                checked=validate_artifacts(plan['JOB_DIR'],proposal.get('outputs',[]),plan.get('stage_proposals',{}).get(stage,[]))
                if not checked['ok'] or proposal.get('inputs')!=expected_inputs(plan,state,stage):
                    raise ValueError('proposal bytes or inputs changed')
                gate=CREATIVE_GATES[stage]
                if gate not in plan['creative_delegations'] and gate not in state.get('approved_human_gates',[]):
                    return {'allowed':True,'next_stage':stage,'next_task':None,'needs_user':True,'reason':gate}
            record=done.get(stage)
            if record is not None:
                verify_completion(plan,state,stage,record)
                gate=CREATIVE_GATES.get(stage)
                if gate and gate not in plan['creative_delegations'] and gate not in state.get('approved_human_gates',[]):
                    return {'allowed':True,'next_stage':stage,'next_task':None,'needs_user':True,'reason':gate}
                continue
            if tid.startswith('G15.M05') and 'G15_DELETE' not in state.get('approved_human_gates',[]):
                raise ValueError('G15_DELETE explicit approval missing')
            phase='proposal' if stage in plan.get('stage_proposals',{}) and not proposal else 'execute'
            return {'allowed':True,'next_stage':stage,'next_task':tid,'needs_user':False,'reason':'ready','phase':phase}
        return {'allowed':True,'next_stage':None,'next_task':None,'needs_user':False,'reason':'all scoped tasks completed'}
    except (ValueError,OSError,TypeError,AttributeError,KeyError) as exc:
        return {'allowed':False,'reason':str(exc)}


def _control_root(root):
    root=Path(root)
    for p in (*root.parents,root,root/'logs',root/'logs'/'project_flow_v1325.json',root/'logs'/'project_flow_v1325.jsonl'):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('control path redirects')
    return root/'logs'


def _write_checkpoint(root,state):
    logs=_control_root(root);logs.mkdir(parents=True,exist_ok=True)
    target=logs/'project_flow_v1325.json'
    import tempfile
    fd,name=tempfile.mkstemp(prefix='project_flow_',suffix='.tmp',dir=logs)
    with os.fdopen(fd,'w',encoding='utf-8') as stream:
        json.dump(state,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        stream.flush();os.fsync(stream.fileno())
    os.replace(name,target)


def _ledger_head(root,*,audit=False):
    ledger=_control_root(root)/'project_flow_v1325.jsonl'
    return _sibling('project_journal_v1326').head(ledger,_sibling('verification_cache_v1326').fingerprint,audit=audit)


def _events(root):
    return copy.deepcopy(_ledger_head(root)['events'])


def checkpoint(root,state,*,event='CHECKPOINT',details=None):
    """New ledgers use v3 deltas; existing v2 histories remain v2."""
    logs=_control_root(root);logs.mkdir(parents=True,exist_ok=True)
    _sibling('project_journal_v1326').append(logs,state,event,details,
        _sibling('verification_cache_v1326').fingerprint,lambda current:_write_checkpoint(root,current))


def read_checkpoint(job_dir):
    head=_ledger_head(job_dir)
    if head['seq']:return copy.deepcopy(head['state'])
    state=json.loads((_control_root(job_dir)/'project_flow_v1325.json').read_text(encoding='utf-8'))
    if state.get('ledger_seq'):raise ValueError('canonical ledger missing')
    return state


def _save(plan,state,event,persist,**details):
    if persist:
        authenticate_context(plan,state,state.get('lock_owner'))
        checkpoint(Path(plan['JOB_DIR']),state,event=event,details=details)


def verify_thumbnail(plan,evidence):
    if not isinstance(evidence,dict) or not all(k in evidence for k in ('title','approval','image_name','image_sha256')):
        raise ValueError('manual thumbnail file/title/approval evidence missing')
    report=_sibling('manual_thumbnail_handoff_v1324').verify_drop(plan['JOB_DIR'],
        title=evidence['title'],approval=evidence['approval'],visual={},
        image_name=evidence['image_name'],image_relative_path=evidence.get('relative_path'),
        expected_source_sha256=evidence['image_sha256'],production_first=True)
    if report['status']!='FILE_ACCEPTED':raise ValueError('thumbnail verification: '+report['status'])
    if report['relative_path'] not in plan['stage_outputs'].get('G11B',[]):
        raise ValueError('thumbnail is outside approved G11B output contract')
    return report


def _failure(plan,s,stage,reason,kind,persist):
    if kind not in {'transient','connection','missing_output','permission','invalid_media','executor'}:kind='executor'
    s.update(status='FAILED',next_stage=stage,last_blocker=reason,
        failure={'stage':stage,'kind':kind,'reason':reason})
    s.pop('inflight',None)
    if s.get('retry_history') and s['retry_history'][-1].get('result')=='RUNNING':
        s['retry_history'][-1].update(result='FAILED',failure=reason)
    _save(plan,s,'FAILED',persist,stage=stage,reason=reason,kind=kind)
    return s


def retry_failed(plan,state,*,session_owner,persist=False):
    authenticate_context(plan,state,session_owner)
    if state.get('status')!='FAILED':raise ValueError('retry requires FAILED')
    failure=state.get('failure',{});stage=failure.get('stage');kind=failure.get('kind')
    counts=state.get('retry_counts',{})
    if stage not in plan['allowed_stages'] or kind=='permission':raise ValueError('explicit permission resolution/new approved scope required')
    if not _sibling('work_package_state').repair_allowed(plan['repair_budget'],counts,stage,kind):
        raise ValueError('retry kind not approved or retry budget exhausted')
    candidate=copy.deepcopy(state);candidate.update(status='RUNNING')
    candidate.pop('inflight',None)
    decision=decide_next(plan,candidate,session_owner=session_owner)
    if not decision.get('allowed') or decision.get('next_stage')!=stage:raise ValueError('retry context invalid: '+decision['reason'])
    candidate.setdefault('retry_counts',{})[stage]=counts.get(stage,0)+1
    candidate.setdefault('retry_history',[]).append({'stage':stage,'kind':kind,'reason':failure['reason'],
        'attempt':candidate['retry_counts'][stage],'result':'RUNNING'})
    candidate.pop('last_blocker',None);candidate.pop('failure',None)
    _save(plan,candidate,'RETRY',persist,stage=stage,kind=kind)
    return candidate


def recover_interrupted(plan,state,*,session_owner,recovery_ref,verify_inactive,persist=False):
    authenticate_context(plan,state,session_owner)
    if not recovery_ref or not callable(verify_inactive) or verify_inactive(state.get('inflight')) is not True:
        raise ValueError('host must verify interrupted executor is no longer active')
    if state.get('status')!='RUNNING' or not state.get('inflight'):raise ValueError('no interrupted execution')
    s=copy.deepcopy(state)
    return _failure(plan,s,s['inflight']['stage'],'execution interrupted; verified inactive: '+recovery_ref,'connection',persist)


def run_until_hinge(plan,state,executor,*,session_owner,persist=False,max_steps=None,auto_retry=True):
    """Finite synchronous host callback loop; never a background ChatGPT worker."""
    validate_plan(plan)
    try:authenticate_context(plan,state,session_owner,force_source=True)
    except (ValueError,OSError) as exc:return {**state,'last_blocker':str(exc)}
    if not callable(executor):raise ValueError('real authorized executor callback required')
    if max_steps is not None and (type(max_steps) is not int or max_steps<1):raise ValueError('positive max_steps required')
    s=copy.deepcopy(state);s.setdefault('stage_completions',{});s.setdefault('quality_qc_invocations',0)
    s['execution_mode']=MODE
    steps=0
    while True:
        if s.get('status')=='FAILED' and not auto_retry:return s
        if s.get('status')=='FAILED' and auto_retry:
            try:s=retry_failed(plan,s,session_owner=session_owner,persist=persist)
            except ValueError:return s
        choice=decide_next(plan,s,session_owner=session_owner)
        if not choice['allowed']:
            s['last_blocker']=choice['reason'];return s
        stage=choice['next_stage']
        if choice['needs_user']:
            s.update(status='WAITING_USER',next_stage=stage,wait_reason=choice['reason'])
            _save(plan,s,'WAITING_USER',persist,stage=stage,reason=choice['reason']);return s
        if stage is None:
            s.update(status='FINAL_REVIEW' if 'G15' in plan['allowed_stages'] else 'PACKAGE_DONE',next_stage=None)
            s['project_status']='PROJECT_FINAL_REVIEW' if s['status']=='FINAL_REVIEW' else 'PACKAGE_DONE'
            if s['status']=='FINAL_REVIEW':
                try:validate_media(plan,s['stage_completions']['G15']['outputs'],prior_evidence=s['stage_completions']['G15'].get('media_evidence'))
                except (OSError,ValueError,subprocess.SubprocessError) as exc:
                    return _failure(plan,s,'G15',str(exc),'invalid_media',persist)
                s['delivery']={'WORK_PACKAGE_ID':plan['WORK_PACKAGE_ID'],'plan_hash':hash_plan(plan),
                    'outputs':copy.deepcopy(s['stage_completions']['G15']['outputs']),
                    'version':plan.get('revision_number',1)}
            _save(plan,s,s['status'],persist);return s
        s['next_stage']=stage
        if max_steps is not None and steps>=max_steps:return s
        task=choice['next_task']
        # Persist intent before host execution. On process loss the host must
        # reconcile the worker/output instead of silently executing again.
        s['inflight']={'task_id':task,'stage':stage,'attempt':s.get('retry_counts',{}).get(stage,0)+1}
        _save(plan,s,'TASK_STARTED',persist,stage=stage)
        completed_this_step=False
        try:
            result=s.get('resumed_result') or executor(task,stage)
            s.pop('resumed_result',None)
            authenticate_context(plan,s,session_owner)
            if not isinstance(result,dict) or result.get('status') not in {'DONE','WARNING','WAITING_USER','FAILED','PROPOSAL_READY'}:
                raise ValueError('executor did not return completion evidence')
            if result['status']=='FAILED':
                _failure(plan,s,stage,result.get('reason','task failed'),result.get('failure_kind','executor'),persist)
                steps+=1;continue
            if result['status']=='WAITING_USER':
                s.pop('inflight',None)
                s.update(status='WAITING_USER',wait_reason=result.get('reason','EXTERNAL_INPUT'),pending_result=copy.deepcopy(result))
                _save(plan,s,'WAITING_USER',persist,stage=stage);return s
            if choice.get('phase')=='proposal':
                if result['status']!='PROPOSAL_READY':raise ValueError('create proposal before using unapproved creative choice')
                checked=validate_artifacts(plan['JOB_DIR'],result.get('outputs',[]),plan['stage_proposals'][stage])
                if not checked['ok']:raise ValueError(checked['reason'])
                media=validate_media(plan,result['outputs'])
                s.setdefault('stage_proposals',{})[stage]={'outputs':copy.deepcopy(result['outputs']),
                    'inputs':expected_inputs(plan,s,stage),'media_evidence':media}
                s.pop('inflight',None)
                completed_this_step=True
                _save(plan,s,'PROPOSAL_READY',persist,stage=stage)
                steps+=1;continue
            if result['status']=='PROPOSAL_READY':raise ValueError('duplicate or unscoped proposal')
            checked=validate_artifacts(plan['JOB_DIR'],result.get('outputs',[]),plan['stage_outputs'][stage])
            if not checked['ok']:
                _failure(plan,s,stage,checked['reason'],'missing_output',persist);steps+=1;continue
            media=validate_media(plan,result['outputs'])
            if stage=='G11B':verify_thumbnail(plan,result.get('thumbnail_evidence'))
            record={'schema':'stage-completion.v2','WORK_PACKAGE_ID':plan['WORK_PACKAGE_ID'],
                'JOB_DIR':plan['JOB_DIR'],'deviceId':plan['deviceId'],
                'approval_ref':s['approval_ref'],'task_id':task,'source_hash':plan['source_hash'],
                'plan_hash':hash_plan(plan),'inputs':expected_inputs(plan,s,stage),
                'outputs':copy.deepcopy(result['outputs']),'completion_status':'DONE',
                'warnings':list(result.get('warnings',[])),'media_evidence':media,
                'thumbnail_evidence':copy.deepcopy(result.get('thumbnail_evidence'))}
            record['record_sha256']=completion_hash(record)
            s['stage_completions'][stage]=record
            s['status']='RUNNING';s.pop('inflight',None);s.pop('wait_reason',None);s.pop('last_blocker',None)
            if s.get('retry_history') and s['retry_history'][-1].get('result')=='RUNNING':
                s['retry_history'][-1]['result']='DONE'
            completed_this_step=True
            _save(plan,s,'STAGE_DONE',persist,stage=stage,record=record)
        except PermissionError as exc:
            if completed_this_step:raise
            _failure(plan,s,stage,str(exc),'permission',persist)
        except (ConnectionError,TimeoutError,subprocess.TimeoutExpired) as exc:
            if completed_this_step:raise
            _failure(plan,s,stage,str(exc),'connection',persist)
        except Exception as exc:
            if completed_this_step:
                # A durable completion may already exist. Let the host reload
                # the ledger; never replace it with a synthetic executor failure.
                raise
            # If context/lock changed, writing a failure would also be unauthorized.
            try:authenticate_context(plan,s,session_owner)
            except (ValueError,OSError) as context_error:
                s['last_blocker']=str(context_error);return s
            _failure(plan,s,stage,str(exc),'invalid_media' if 'MP4' in str(exc) else 'executor',persist)
        steps+=1


def resume_after_user(plan,state,*,action,user_ref,evidence=None,persist=False,session_owner=None):
    authenticate_context(plan,state,session_owner or state.get('lock_owner'),force_source=True)
    if state.get('status')!='WAITING_USER' or not isinstance(user_ref,str) or not user_ref.strip():
        raise ValueError('matching user wait and authentic user reference required')
    if action!=state.get('wait_reason'):raise ValueError('user action does not resolve the waiting reason')
    out=copy.deepcopy(state)
    if action=='USER_IMAGE_PLACEMENT':
        report=verify_thumbnail(plan,evidence)
        pending=state.get('pending_result',{})
        if pending.get('thumbnail_sha256') and pending['thumbnail_sha256']!=report['image_sha256']:
            raise ValueError('copied thumbnail differs from generated image')
        outputs=list(pending.get('outputs',[]))
        outputs=[x for x in outputs if x.get('relative_path')!=report['relative_path']]
        outputs.append({'relative_path':report['relative_path'],'sha256':report['image_sha256']})
        out['resumed_result']={'status':'DONE','outputs':outputs,'thumbnail_evidence':evidence}
        # The same authenticated copy+approval message resolves both gates.
        out.setdefault('approved_human_gates',[]).append('G11B_THUMBNAIL')
    elif action in CREATIVE_GATES.values():
        stage=next(k for k,v in CREATIVE_GATES.items() if v==action)
        if stage in state.get('stage_proposals',{}):
            proposal=state['stage_proposals'][stage]
            checked=validate_artifacts(plan['JOB_DIR'],proposal['outputs'],plan['stage_proposals'][stage])
            if not checked['ok'] or proposal['inputs']!=expected_inputs(plan,state,stage):raise ValueError('proposal changed')
        else:
            if stage not in state.get('stage_completions',{}):raise ValueError('cannot approve an uncreated proposal')
            verify_completion(plan,state,stage,state['stage_completions'][stage])
        out.setdefault('approved_human_gates',[]).append(action)
    elif action!='EXTERNAL_INPUT':raise ValueError('unsupported user wait')
    out.update(status='RUNNING',external_resolved_by=user_ref)
    out.pop('wait_reason',None);out.pop('pending_result',None)
    _save(plan,out,'USER_RESUMED',persist,action=action,user_ref=user_ref,evidence=evidence)
    return out


def user_review(plan,state,*,action,user_ref,notes,targets=None,persist=False,session_owner=None):
    authenticate_context(plan,state,session_owner or state.get('lock_owner'),force_source=True)
    if 'G15' not in plan['allowed_stages'] or state.get('status')!='FINAL_REVIEW' or not isinstance(user_ref,str) or not user_ref.strip():
        raise ValueError('final review and authentic user message required')
    if action not in {'ACCEPTED','REVISION_REQUESTED'}:raise ValueError('unknown review decision')
    decision=decide_next(plan,{**state,'status':'RUNNING'},session_owner=state['lock_owner'])
    if not decision.get('allowed') or decision.get('next_stage') is not None:raise ValueError('delivery evidence is no longer valid')
    validate_media(plan,state['stage_completions']['G15']['outputs'],prior_evidence=state['stage_completions']['G15'].get('media_evidence'))
    out=copy.deepcopy(state);out['status']=action;out['project_status']=action
    review={'user_ref':user_ref,'notes':notes,'delivery':copy.deepcopy(state['delivery'])}
    if action=='ACCEPTED':out['acceptance']=review
    else:
        if not isinstance(targets,list) or not targets or not all(t in plan['allowed_stages'] for t in targets):
            raise ValueError('revision requires specific previously authorized stages')
        review.update(targets=targets,affected_stages=revision_targets(plan,targets),requires_new_revision_scope=True)
        review['affected_files']=[p for st in review['affected_stages'] for p in plan['stage_outputs'][st]]
        out.setdefault('revision_requests',[]).append(review)
    _save(plan,out,action,persist,review=review)
    return out


def merge_verified_completions(plan,state,previous,*,expected_inputs,session_owner=None,persist=False):
    authenticate_context(plan,state,session_owner or state.get('lock_owner'),force_source=True)
    if state.get('status')!='RUNNING' or not isinstance(previous,dict):raise ValueError('authorized running package required')
    out=copy.deepcopy(state);out.setdefault('stage_completions',{})
    for stage in plan['allowed_stages']:
        if stage not in previous:continue
        if stage in out['stage_completions']:raise ValueError('cannot overwrite existing completion')
        record=previous[stage]
        verify_completion(plan,out,stage,record)
        if record.get('inputs')!=expected_inputs.get(stage):raise ValueError('changed or unknown input hashes')
        media=validate_media(plan,record['outputs'],prior_evidence=record.get('media_evidence'))
        adopted=copy.deepcopy(record)
        adopted.update(WORK_PACKAGE_ID=plan['WORK_PACKAGE_ID'],approval_ref=state['approval_ref'],plan_hash=hash_plan(plan),
            imported_from_package=record['WORK_PACKAGE_ID'],imported_approval_ref=record['approval_ref'],
            provenance=copy.deepcopy(record),media_evidence=media)
        adopted['record_sha256']=completion_hash(adopted)
        out['stage_completions'][stage]=adopted
    if set(previous)-set(plan['allowed_stages']):raise ValueError('cannot import outside scope')
    _save(plan,out,'COMPLETIONS_IMPORTED',persist,stages=list(previous))
    return out


def revision_targets(plan,targets):
    affected=set(targets)
    for stage in plan['allowed_stages']:
        deps=plan.get('stage_dependencies',{}).get(stage,plan['allowed_stages'][:plan['allowed_stages'].index(stage)])
        if affected.intersection(deps):affected.add(stage)
    affected.add('G15')
    return [s for s in plan['allowed_stages'] if s in affected]


def propose_revision(plan,state):
    """Return a concrete new plan; approval remains a host/user action."""
    if state.get('status')!='REVISION_REQUESTED':raise ValueError('user revision request required')
    request=state['revision_requests'][-1]
    new=copy.deepcopy(plan);number=plan.get('revision_number',1)+1
    new['revision_number']=number;new['WORK_PACKAGE_ID']=plan['WORK_PACKAGE_ID']+'-R'+str(number)
    new['revision_of']=hash_plan(plan)
    new['revision_request']=copy.deepcopy(request)
    for stage in request['affected_stages']:
        new['stage_outputs'][stage]=['revisions/r'+str(number)+'/'+p for p in plan['stage_outputs'][stage]]
        for old_path,new_path in zip(plan['stage_outputs'][stage],new['stage_outputs'][stage]):
            if old_path in new.get('media_contracts',{}):new['media_contracts'][new_path]=new['media_contracts'].pop(old_path)
        if stage in new.get('stage_proposals',{}):
            new['stage_proposals'][stage]=['revisions/r'+str(number)+'/'+p for p in plan['stage_proposals'][stage]]
    validate_plan(new)
    return new


def begin_revision(old_plan,new_plan,old_state,new_state,*,session_owner,persist=False):
    if new_plan!=propose_revision(old_plan,old_state):raise ValueError('revision differs from concrete requested scope')
    authenticate_context(new_plan,new_state,session_owner)
    affected=old_state['revision_requests'][-1]['affected_stages']
    prior={s:r for s,r in old_state['stage_completions'].items() if s not in affected}
    out=merge_verified_completions(new_plan,new_state,prior,expected_inputs={s:r['inputs'] for s,r in prior.items()},session_owner=session_owner)
    out['previous_deliveries']=copy.deepcopy(old_state.get('previous_deliveries',[]))+[old_state['delivery']]
    _save(new_plan,out,'REVISION_STARTED',persist,affected_stages=affected)
    return out
