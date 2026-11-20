"""Safe CLI facade for production-first project_flow_v1325.py.

Run this on the authorized machine from an already-approved work package.
The CLI never runs FFmpeg, downloads, deletes or invokes remote/model tools.
Call `next`, execute the returned task using a separately approved tool,
then pass its real completion JSON to `record`. No background work.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import project_flow_v1325 as flow


def load_json(path:Path)->dict:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict):raise ValueError('JSON object required')
    return value


def command(args)->dict:
    plan=load_json(Path(args.plan))
    flow.validate_plan(plan)
    root=Path(plan['JOB_DIR'])
    if args.operation=='init':
        state=load_json(Path(args.approved_state))
        item=flow.decide_next(plan,state,session_owner=state.get('lock_owner',''))
        if not item.get('allowed'):raise ValueError('approved state is invalid: '+item['reason'])
        flow.checkpoint(root,state)
        return {'status':'RUNNING','next_task':item['next_task']}
    state=flow.read_checkpoint(root)
    if args.operation=='next':
        if state.get('status') in {'PACKAGE_DONE','FINAL_REVIEW','ACCEPTED','REVISION_REQUESTED'}:
            return {'allowed':False,'status':state['status'],'next_task':None}
        return flow.decide_next(plan,state,session_owner=state.get('lock_owner',''))
    if args.operation=='record':
        result=load_json(Path(args.result))
        decision=flow.decide_next(plan,state,session_owner=state.get('lock_owner',''))
        if not decision.get('allowed') or decision.get('needs_user') or not decision.get('next_task'):
            raise ValueError('no authorized pending task for this record')
        next_stage=decision['next_stage'];next_task=decision['next_task']
        s=flow.run_until_hinge(plan,state,lambda task,stage: result if task==next_task and stage==next_stage else
                               {'status':'FAILED','reason':'wrong executor task'},
                               session_owner=state.get('lock_owner',''),persist=True,max_steps=1)
        return {'status':s['status'],'completed_stage':next_stage if next_stage in s['stage_completions'] else None,
                'next_stage':s.get('next_stage'),'reason':s.get('last_blocker')}
    if args.operation=='resume':
        evidence=load_json(Path(args.evidence)) if args.evidence else None
        s=flow.resume_after_user(plan,state,action=args.action,user_ref=args.user_ref,evidence=evidence)
        flow.checkpoint(root,s)
        return {'status':s['status'],'next_stage':s.get('next_stage')}
    if args.operation=='review':
        targets=args.targets.split(',') if args.targets else None
        s=flow.user_review(plan,state,action=args.action,user_ref=args.user_ref,
                           notes=args.notes or '',targets=targets)
        flow.checkpoint(root,s)
        return {'status':s['status'],'targeted_revision':targets}
    raise ValueError('unsupported operation')


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('operation',choices=('init','next','record','resume','review'))
    parser.add_argument('--plan',required=True)
    parser.add_argument('--approved-state')
    parser.add_argument('--result')
    parser.add_argument('--action')
    parser.add_argument('--user-ref')
    parser.add_argument('--notes')
    parser.add_argument('--targets')
    parser.add_argument('--evidence')
    args=parser.parse_args()
    try:
        if args.operation=='init' and not args.approved_state:raise ValueError('--approved-state required')
        if args.operation=='record' and not args.result:raise ValueError('--result required')
        if args.operation in {'resume','review'} and (not args.action or not args.user_ref):
            raise ValueError('--action and --user-ref required')
        print(json.dumps(command(args),ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,RuntimeError,OSError,TypeError,KeyError) as exc:
        print(json.dumps({'status':'BLOCKED','reason':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':sys.exit(main())
