"""REVIEW_PHIM v1.3.23 — one fail-closed workflow dispatch gate (stdlib only).

The caller must authenticate user approval, inspect actual remote lock and files,
check real media content and then call this BEFORE EACH task execution. A positive
Decision is never remote authorization or evidence that the task was executed.
Does not mutate legacy state, run remote tools, download models or approve content.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

STAGE_PREDECESSOR = {
    'G01': None, 'G02':'Q01','G03':'Q02','G04':'Q03','G05':'Q04',
    'G06':'Q05','G07':'Q06','G08':'Q07','G09':'Q08','G10':'Q09',
    'G11':'Q10','G11A':'Q11','G11B':'Q11A','G12':'Q11B','G13':'Q12',
    'G14':'Q13','G15':'Q14',
}
ATOMIC = {'G01':'G01.SOURCE.FULL','G02':'G02.ASR.FULL',
          'G03':'G03.TRANSLATE.FULL','G04':'G04.FILM.UNDERSTANDING.FULL',
          'G05':'G05.REVIEW.FULL','G11A':'G11A.YOUTUBE_METADATA.FULL',
          'G11B':'G11B.THUMBNAIL.FULL'}
MANDATORY_CONTENT_APPROVAL = {
    'G05':'G05_SCRIPT','G07':'G07_VOICE','G10':'G10_PILOT',
    'G11A':'G11A_METADATA','G11B':'G11B_THUMBNAIL',
}
NO_PREAPPROVAL_STAGES = {'P00','G01','G02','G03','G04','G05'}
G07_PREVIEW_TASKS = {'G07.M01','G07.M02','G07.VOICE_SAMPLE','G07.VOICE_PREVIEW'}
STAGE_TO_Q = {s:'Q'+s[1:] for s in STAGE_PREDECESSOR}


class Decision:
    def __init__(self, allowed: bool, reason: str):
        self.allowed, self.reason = bool(allowed), str(reason)
    def __repr__(self):
        return f'Decision(allowed={self.allowed!r}, reason={self.reason!r})'


def _stage(t: str) -> str:
    return t.split('.',1)[0] if isinstance(t,str) and '.' in t else str(t)


def hash_plan(plan: dict[str, Any]) -> str:
    """Canonical hash matching the existing `work_package_state.plan_hash`."""
    if not isinstance(plan, dict) or 'plan_hash' in plan:
        raise ValueError('invalid/self-referential plan')
    raw=json.dumps(plan,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def expand_tasks(plan: dict[str,Any]) -> list[str]:
    tasks=plan.get('task_ids')
    ranges=plan.get('bounded_batches',[])
    if not isinstance(tasks,list) or not isinstance(ranges,list):
        raise ValueError('task IDs / bounded batches must be lists')
    out=list(tasks)
    for b in ranges:
        if not isinstance(b,dict):
            raise ValueError('invalid batch')
        stem,start,end=b.get('stem'),b.get('start'),b.get('end')
        if not isinstance(stem,str) or type(start)!=int or type(end)!=int or not 1<=start<=end<=400 or '*' in stem or '.B' in stem:
            raise ValueError('unbounded or invalid batch')
        out.extend(f'{stem}.B{i:03d}' for i in range(start,end+1))
    if not out or len(out)>400 or len(out)!=len(set(out)):
        raise ValueError('empty, duplicate or unbounded tasks')
    if not all(isinstance(t,str) and t.startswith(('G','P00')) and '*' not in t and '?' not in t for t in out):
        raise ValueError('bad task IDs')
    return out


def validate_new_package(plan: dict[str,Any]) -> list[str]:
    """Validate task granularity and stage scope; never auto-migrate legacy jobs."""
    required={'WORK_PACKAGE_ID','schema_version','deviceId','JOB_DIR','SOURCE_MOVIE',
              'source_hash','allowed_stages','task_ids','allowed_read_roots',
              'allowed_write_roots','repair_budget','install_budget','human_gates'}
    if not isinstance(plan,dict) or not required.issubset(plan):
        raise ValueError('incomplete work-package.v2 plan')
    if plan['schema_version']!='work-package.v2' or not isinstance(plan['allowed_stages'],list):
        raise ValueError('invalid work package / allowed stages')
    if not plan['JOB_DIR'] or not plan['deviceId'] or not plan['WORK_PACKAGE_ID']:
        raise ValueError('empty device/work package/job')
    if not isinstance(plan['source_hash'],str) or len(plan['source_hash'])!=64:
        if not (plan['source_hash']=='UNKNOWN' and plan['allowed_stages']==['P00']):
            raise ValueError('invalid source hash')
    expanded=expand_tasks(plan)
    for t in expanded:
        st=_stage(t)
        if st not in plan['allowed_stages']:
            raise ValueError('task outside approved stages')
        if st in ATOMIC and t!=ATOMIC[st]:
            raise ValueError(f'atomic stage {st} must use {ATOMIC[st]}')
    for stage,expected in ATOMIC.items():
        if stage in plan['allowed_stages'] and expanded.count(expected)!=1:
            raise ValueError(f'{stage} requires exactly one FULL task')
    hash_plan(plan)
    return expanded


def _qc_set(state:dict[str,Any]) -> set[str]:
    """Reject contradictory legacy/new field values; never union inconsistent truth."""
    modern=state.get('qc_gates_passed')
    older=state.get('passed_qc')
    if modern is not None and not isinstance(modern,(list,tuple,set)):
        raise ValueError('invalid qc_gates_passed')
    if older is not None and not isinstance(older,(list,tuple,set)):
        raise ValueError('invalid passed_qc')
    a=set(modern or []);b=set(older or [])
    if modern is not None and older is not None and a!=b:
        raise ValueError('QC aliases conflict: reconcile evidence before dispatch')
    return a if modern is not None else b


def decide_dispatch(plan:dict[str,Any],state:dict[str,Any],task_id:str,
                    *,session_owner:str,legacy:bool=False) -> Decision:
    """The ONLY v1.3.23 dispatch decision. Must be called before every task.

    `legacy=True` requires a separately verified legacy package record, not just
    a self-declared flag. It does NOT bypass stage QC, approvals or hash checks.
    """
    try:
        if not legacy:
            actual_tasks=validate_new_package(plan)
        else:
            if not state.get('legacy_package_verified'):
                return Decision(False,'unverified legacy package')
            actual_tasks=expand_tasks(plan)
        if not isinstance(state,dict):return Decision(False,'invalid state')
        if state.get('status')!='RUNNING':return Decision(False,'not running')
        digest=hash_plan(plan)
        if not state.get('approval_ref') or state.get('plan_hash')!=digest or state.get('approved_plan_hash')!=digest:
            return Decision(False,'package approval/hash mismatch')
        for field in ('deviceId','JOB_DIR','source_hash'):
            if state.get(field)!=plan.get(field):return Decision(False,f'{field} mismatch')
        if not session_owner or state.get('lock_owner')!=session_owner or state.get('lock_verified') is not True:
            return Decision(False,'lock owner or actual file lock not verified')
        if task_id not in actual_tasks or task_id not in state.get('allowed_tasks',[]):
            return Decision(False,'task outside approved package')
        if state.get('task_qc',{}).get(task_id)=='PASS':
            return Decision(False,'task already PASS; verify output hashes and reuse, no rerun')
        if state.get('unresolved_blockers'):return Decision(False,'unresolved blocker')
        st=_stage(task_id)
        if st=='P00':return Decision(True,'approved read-only/scoped P00 task')
        if st not in STAGE_PREDECESSOR:return Decision(False,'unknown stage')
        qcs=_qc_set(state)
        legacy_publish = bool(legacy and state.get('legacy_without_thumbnail_verified') is True)
        pred = 'Q11' if (legacy_publish and st == 'G12') else STAGE_PREDECESSOR[st]
        if pred and pred not in qcs:
            return Decision(False,f'prerequisite {pred} missing')
        gates=set(state.get('approved_human_gates') or [])
        if st in {'G06','G07','G08','G09','G10','G11','G11A','G11B','G12','G13','G14','G15'} and 'G05_SCRIPT' not in gates:
            return Decision(False,'G05_SCRIPT approval missing')
        if st=='G07':
            if task_id not in G07_PREVIEW_TASKS and 'G07_VOICE' not in gates:
                return Decision(False,'G07_VOICE required before TTS generation')
        elif st in {'G08','G09','G10','G11','G11A','G11B','G12','G13','G14','G15'} and 'G07_VOICE' not in gates:
            return Decision(False,'G07_VOICE missing')
        if st in {'G11','G11A','G11B','G12','G13','G14','G15'} and 'G10_PILOT' not in gates:
            return Decision(False,'G10_PILOT missing')
        if st in {'G11B','G12','G13','G14','G15'} and not (legacy_publish and st in {'G12','G13','G14','G15'}) and 'G11A_METADATA' not in gates:
            return Decision(False,'G11A_METADATA missing')
        if st in {'G12','G13','G14','G15'} and 'G11B_THUMBNAIL' not in gates:
            if not legacy_publish:
                return Decision(False,'G11B_THUMBNAIL missing')
        if st in {'G05','G09'}:
            ev=state.get('stage_evidence',{}).get(pred,{})
            if ev.get('visual_inspected') is not True or ev.get('source_hash')!=plan['source_hash']:
                return Decision(False,f'{pred} lacks actual visual evidence for source')
        if st=='G12' and not (legacy and state.get('legacy_without_thumbnail_verified') is True):
            ev=state.get('stage_evidence',{}).get('Q11B',{})
            if ev.get('thumbnail_file_verified') is not True or ev.get('thumbnail_approval_hash_matches') is not True:
                return Decision(False,'thumbnail bytes/title approval proof missing')
        if st=='G15':
            if not _g14_verified(state):return Decision(False,'Q14 technical/story/visual or media unverified')
        if st=='G15' and task_id.startswith('G15.M05'):
            if 'G15_DELETE' not in gates or not isinstance(plan.get('delete_paths'),list) or not plan['delete_paths']:
                return Decision(False,'explicit deletion approval/path list missing')
        return Decision(True,'approved stage prerequisites, human gates and scoped lock verified')
    except (ValueError,KeyError,TypeError,AttributeError) as exc:
        return Decision(False,str(exc))


def _g14_verified(state:dict[str,Any]) -> bool:
    axes=state.get('g14_axes',{})
    ev=state.get('stage_evidence',{}).get('Q14',{})
    return (isinstance(axes,dict) and all(axes.get(k)=='PASS' for k in
           ('TECHNICAL_STATUS','STORY_STATUS','VISUAL_EDITING_STATUS'))
           and isinstance(ev,dict) and ev.get('actual_video_inspected') is True
           and ev.get('audio_inspected') is True)


def validate_package_completion(plan:dict[str,Any],state:dict[str,Any]) -> Decision:
    """Precheck for PACKAGE_PASS; still call legacy transition after this returns True."""
    try:
        tasks=expand_tasks(plan)
        if (state.get('status') != 'RUNNING' or not state.get('approval_ref')
                or state.get('plan_hash') != hash_plan(plan)
                or state.get('approved_plan_hash') != hash_plan(plan)
                or state.get('source_hash') != plan.get('source_hash')
                or state.get('deviceId') != plan.get('deviceId')
                or state.get('JOB_DIR') != plan.get('JOB_DIR')
                or state.get('lock_verified') is not True or not state.get('lock_owner')):
            return Decision(False,'not running or approved context/lock not verified')
        if not tasks or not state.get('final_qc'):
            return Decision(False,'final package QC missing')
        if any(state.get('task_qc',{}).get(t)!='PASS' for t in tasks):
            return Decision(False,'task QC incomplete')
        if state.get('unresolved_blockers'):
            return Decision(False,'blockers not closed')
        qcs=_qc_set(state)
        gates=set(state.get('approved_human_gates',[]))
        stages={_stage(t) for t in tasks}
        for stage in stages:
            if stage in STAGE_TO_Q and STAGE_TO_Q[stage] not in qcs:
                return Decision(False,f'{STAGE_TO_Q[stage]} missing')
            gate=MANDATORY_CONTENT_APPROVAL.get(stage)
            if gate and gate not in gates:
                return Decision(False,f'{gate} not approved')
        if 'G11B' in stages:
            # v1.3.24: the user placing/approving a thumbnail is not proof the
            # remote bytes were verified. The caller must authenticate this QC
            # from actual JOB_DIR inspection (manual_thumbnail_handoff_v1324).
            ev=state.get('stage_evidence',{}).get('Q11B',{})
            if (not isinstance(ev,dict) or ev.get('thumbnail_file_verified') is not True
                    or ev.get('thumbnail_approval_hash_matches') is not True):
                return Decision(False,'G11B thumbnail has no verified remote file and approval hash')
        if 'G15' in stages and any(t.startswith('G15.M05') for t in tasks):
            if 'G15_DELETE' not in gates or not plan.get('delete_paths'):
                return Decision(False,'G15 deletion not authorized')
        if 'G14' in stages and not _g14_verified(state):
            return Decision(False,'G14 lacks real media and three-axis QC evidence')
        return Decision(True,'all scoped task QC and stage gates present')
    except (TypeError,KeyError,ValueError,AttributeError) as exc:
        return Decision(False,str(exc))


def reuse_evidence(job_dir:Path,record:dict[str,Any],*,source_hash:str,inputs:dict[str,str])->Decision:
    """Inspect actual bounded output bytes; no reuse by log/JSON existence alone."""
    try:
        if record.get('qc_status')!='PASS' or record.get('source_hash')!=source_hash or record.get('inputs')!=inputs:
            return Decision(False,'QC/source/input changed')
        root=Path(job_dir).resolve(strict=True)
        outputs=record.get('outputs')
        if not isinstance(outputs,list) or not outputs:return Decision(False,'missing outputs')
        for item in outputs:
            rel=item['relative_path']
            if not isinstance(rel,str) or not rel or '\\' in rel or rel.startswith('/') or '..' in PurePosixPath(rel).parts:
                return Decision(False,'unsafe output relative path')
            candidate=root.joinpath(*PurePosixPath(rel).parts)
            if candidate.is_symlink() or not candidate.is_file():return Decision(False,'output missing or symlink')
            actual=candidate.resolve(strict=True)
            if root not in actual.parents:return Decision(False,'output outside job root')
            if candidate.stat().st_size==0:return Decision(False,'empty output')
            h=hashlib.sha256()
            with candidate.open('rb') as fh:
                for chunk in iter(lambda:fh.read(1024*1024),b''):
                    h.update(chunk)
            digest=h.hexdigest()
            if digest!=item.get('sha256'):
                return Decision(False,'output hash mismatch')
        return Decision(True,'every output byte hash and input/source lineage verified')
    except (KeyError,OSError,TypeError,ValueError) as exc:
        return Decision(False,str(exc))


def select_g03_transcript(report:dict[str,Any])->str:
    """Prefer verified cleaned version; a declared but invalid cleaned file blocks."""
    if report.get('cleaned_declared') or report.get('cleaned_path'):
        if report.get('cleaned_verified') is not True or not report.get('cleaned_path'):
            raise ValueError('cleaned transcript was declared but not verified')
        return report['cleaned_path']
    if report.get('original_verified') is True and report.get('original_path'):
        return report['original_path']
    raise ValueError('no verified transcript available for G03')
