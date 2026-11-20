"""Safe CLI facade for production-first project_flow_v1325.py.

Run this on the authorized machine from an already-approved work package.
The CLI runs approved FFprobe/FFmpeg only to validate delivered MP4 bytes.
It never downloads, deletes or invokes remote/model tools.
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
    owner=args.owner
    if args.operation=='init':
        state=load_json(Path(args.approved_state))
        if any((root/'logs'/name).exists() for name in ('project_flow_v1325.jsonl','project_flow_v1325.json')):
            raise ValueError('already initialized or legacy snapshot; never overwrite existing state')
        item=flow.decide_next(plan,state,session_owner=owner)
        if not item.get('allowed'):raise ValueError('approved state is invalid: '+item['reason'])
        flow.checkpoint(root,state)
        return {'status':'RUNNING','next_task':item['next_task']}
    state=flow.read_checkpoint(root)
    if args.operation=='revision-start':
        old_plan=load_json(Path(args.previous_plan));fresh=load_json(Path(args.approved_state))
        fresh['ledger_seq']=state['ledger_seq']
        out=flow.begin_revision(old_plan,plan,state,fresh,session_owner=owner,persist=True)
        return {'status':out['status'],'reused_stages':list(out['stage_completions'])}
    flow.authenticate_context(plan,state,owner)
    if args.operation=='next':
        if state.get('status') in {'PACKAGE_DONE','FINAL_REVIEW','ACCEPTED','REVISION_REQUESTED'}:
            return {'allowed':False,'status':state['status'],'next_task':None}
        decision=flow.decide_next(plan,state,session_owner=owner)
        if decision.get('needs_user'):
            state.update(status='WAITING_USER',wait_reason=decision['reason'],next_stage=decision['next_stage'])
            flow.checkpoint(root,state,event='WAITING_USER')
        return decision
    if args.operation=='record':
        result=load_json(Path(args.result))
        inflight=state.get('inflight')
        if inflight:
            if result.get('task_id')!=inflight['task_id']:raise ValueError('result differs from claimed task')
            state.pop('inflight')
        decision=flow.decide_next(plan,state,session_owner=owner)
        if not decision.get('allowed') or decision.get('needs_user') or not decision.get('next_task'):
            raise ValueError('no authorized pending task for this record')
        next_stage=decision['next_stage'];next_task=decision['next_task']
        if result.get('task_id')!=next_task or result.get('plan_hash')!=flow.hash_plan(plan):
            raise ValueError('result must bind exact task_id and plan_hash')
        s=flow.run_until_hinge(plan,state,lambda task,stage: result if task==next_task and stage==next_stage else
                               {'status':'FAILED','reason':'wrong executor task'},
                               session_owner=owner,persist=True,max_steps=1,auto_retry=False)
        return {'status':s['status'],'completed_stage':next_stage if next_stage in s['stage_completions'] else None,
                'next_stage':s.get('next_stage'),'reason':s.get('last_blocker')}
    if args.operation=='resume':
        evidence=load_json(Path(args.evidence)) if args.evidence else None
        s=flow.resume_after_user(plan,state,action=args.action,user_ref=args.user_ref,evidence=evidence,persist=True,session_owner=owner)
        if s.get('resumed_result'):
            s=flow.run_until_hinge(plan,s,lambda t,st:None,session_owner=owner,persist=True,max_steps=1,auto_retry=False)
        return {'status':s['status'],'next_stage':s.get('next_stage')}
    if args.operation=='review':
        targets=args.targets.split(',') if args.targets else None
        s=flow.user_review(plan,state,action=args.action,user_ref=args.user_ref,
                           notes=args.notes or '',targets=targets,persist=True,session_owner=owner)
        return {'status':s['status'],'targeted_revision':targets}
    if args.operation=='retry':
        s=flow.retry_failed(plan,state,session_owner=owner,persist=True)
        return {'status':s['status'],'next_stage':s.get('next_stage'),'retry_counts':s['retry_counts']}
    if args.operation=='start':
        decision=flow.decide_next(plan,state,session_owner=owner)
        if not decision.get('allowed') or decision.get('needs_user') or not decision.get('next_task'):
            raise ValueError('no authorized pending task')
        state['inflight']={'task_id':decision['next_task'],'stage':decision['next_stage'],
                           'phase':decision.get('phase','execute'),
                           'attempt':state.get('retry_counts',{}).get(decision['next_stage'],0)+1}
        flow.checkpoint(root,state,event='TASK_STARTED')
        return {'status':'RUNNING',**state['inflight']}
    if args.operation=='recover':
        evidence=load_json(Path(args.evidence))
        # The host supplies an authorized process-inspection record, not an
        # assumption based on timeout. No process is killed by this CLI.
        if (evidence.get('source')!='host_process_inspection' or not evidence.get('inspection_ref')
                or evidence.get('plan_hash')!=flow.hash_plan(plan) or evidence.get('owner')!=owner
                or evidence.get('task_id')!=(state.get('inflight') or {}).get('task_id')):
            raise ValueError('matching host process inspection required')
        s=flow.recover_interrupted(plan,state,session_owner=owner,recovery_ref=evidence['inspection_ref'],
            verify_inactive=lambda task:evidence.get('active') is False,persist=True)
        return {'status':s['status'],'next_stage':s['next_stage'],'next_action':'retry'}
    if args.operation=='revision-plan':
        return flow.propose_revision(plan,state)
    if args.operation=='import':
        records=load_json(Path(args.result));inputs=load_json(Path(args.evidence))
        s=flow.merge_verified_completions(plan,state,records,expected_inputs=inputs,session_owner=owner,persist=True)
        return {'status':s['status'],'imported_stages':list(records)}
    raise ValueError('unsupported operation')


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('operation',choices=('init','next','start','record','resume','review','retry','recover','revision-plan','revision-start','import'))
    parser.add_argument('--plan',required=True)
    parser.add_argument('--owner',required=True,help='authenticated host session owner, never inferred from checkpoint')
    parser.add_argument('--approved-state')
    parser.add_argument('--previous-plan')
    parser.add_argument('--result')
    parser.add_argument('--action')
    parser.add_argument('--user-ref')
    parser.add_argument('--notes')
    parser.add_argument('--targets')
    parser.add_argument('--evidence')
    args=parser.parse_args()
    try:
        if args.operation=='init' and not args.approved_state:raise ValueError('--approved-state required')
        if args.operation=='revision-start' and (not args.previous_plan or not args.approved_state):
            raise ValueError('--previous-plan and --approved-state required')
        if args.operation=='record' and not args.result:raise ValueError('--result required')
        if args.operation in {'recover','import'} and not args.evidence:raise ValueError('--evidence required')
        if args.operation=='import' and not args.result:raise ValueError('--result required')
        if args.operation in {'resume','review'} and (not args.action or not args.user_ref):
            raise ValueError('--action and --user-ref required')
        print(json.dumps(command(args),ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,RuntimeError,OSError,TypeError,KeyError) as exc:
        print(json.dumps({'status':'BLOCKED','reason':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':sys.exit(main())
