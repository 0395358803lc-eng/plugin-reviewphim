"""Compare an explicitly supplied old flow module with the current journal.

Example: git show da820b4:skills/producing-movie-review-videos/tools/project_flow_v1325.py
Save that file unchanged, then pass --baseline and a new --output directory.
This benchmark never opens a production ledger.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import time


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def measure(module,root,count):
    state={'status':'RUNNING','stage_completions':{}}
    start=time.perf_counter()
    for i in range(count):
        state['stage_completions'][str(i)]={'record_sha256':str(i),'outputs':[{'path':f'output/{i}.json','payload':'x'*4096}]}
        module.checkpoint(root,state,event='TASK_DONE')
        assert module.read_checkpoint(root)==state
    elapsed=time.perf_counter()-start
    if hasattr(module,'_ledger_head'):module._sibling('project_journal_v1326').clear()
    start=time.perf_counter();assert module.read_checkpoint(root)==state;cold=time.perf_counter()-start
    start=time.perf_counter();assert module.read_checkpoint(root)==state;warm=time.perf_counter()-start
    return {'events':count,'write_and_read_seconds':elapsed,'cold_resume_seconds':cold,'warm_resume_seconds':warm,
            'ledger_bytes':(root/'logs/project_flow_v1325.jsonl').stat().st_size,
            'snapshot_bytes':(root/'logs/project_flow_v1325.json').stat().st_size}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',required=True);parser.add_argument('--output',required=True);parser.add_argument('--events',type=int,default=200);args=parser.parse_args()
    root=Path(args.output).resolve();root.mkdir(parents=True,exist_ok=False)
    old=load(args.baseline,'baseline_flow');new=load(Path(__file__).with_name('project_flow_v1325.py'),'current_flow')
    result={'fixture':'one 4 KiB output record added per event; checkpoint plus resume on every event',
            'before':measure(old,root/'before',args.events),'after':measure(new,root/'after',args.events)}
    result['time_reduction_percent']=100*(1-result['after']['write_and_read_seconds']/result['before']['write_and_read_seconds'])
    result['ledger_reduction_percent']=100*(1-result['after']['ledger_bytes']/result['before']['ledger_bytes'])
    (root/'benchmark.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
