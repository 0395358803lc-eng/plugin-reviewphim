"""CLI bridge is usable by ChatGPT's authorized remote command executor."""
import json,subprocess,sys
from pathlib import Path
from test_project_flow_v1325 import plan,state,module,complete

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools'/'project_flow_cli_v1325.py'

def call(*args):
    r=subprocess.run([sys.executable,str(CLI),*map(str,args)],capture_output=True,text=True)
    assert r.returncode==0,(r.stdout,r.stderr)
    return json.loads(r.stdout)

def test_cli_can_advance_from_real_completion_record_to_package_done(tmp_path):
    f=module();p=plan(tmp_path,stages=('G01',));s=state(f,p)
    plan_file=tmp_path/'approved_plan.json';plan_file.write_text(json.dumps(p))
    f.checkpoint(tmp_path,s)
    n=call('next','--plan',plan_file)
    assert n['allowed'] is True and n['next_task']=='G01.SOURCE.FULL'
    result=complete(f,p,'G01');record=tmp_path/'executed.json';record.write_text(json.dumps(result))
    out=call('record','--plan',plan_file,'--result',record)
    assert out['status']=='PACKAGE_DONE'
    assert f.read_checkpoint(tmp_path)['status']=='PACKAGE_DONE'
