from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('workflow',ROOT/'tools/publish_workflow_state.py')
w=importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def test_stage_order_and_two_human_gates():
    state={'allowed_stages':['G11A','G11B','G12'],'passed_qc':['Q11'],'approved_human_gates':[]}
    assert w.can_start_stage('G11A', state)
    assert not w.can_start_stage('G11B',state)
    state['passed_qc'].append('Q11A');state['approved_human_gates'].append('G11A_METADATA')
    assert w.can_start_stage('G11B', state)
    assert not w.can_start_stage('G12', state)
    state['passed_qc'].append('Q11B');state['approved_human_gates'].append('G11B_THUMBNAIL')
    assert w.can_start_stage('G12', state)


def test_no_legacy_project_unexpected_gate():
    state={'allowed_stages':['G11','G12'],'passed_qc':['Q11'],'approved_human_gates':[]}
    assert w.can_start_stage('G12', state)


def test_new_workflow_cannot_be_marked_complete_without_approvals():
    state={'allowed_stages':['G11','G11A','G11B','G12'],'passed_qc':['Q11','Q11A','Q11B','Q12'],'approved_human_gates':['G11A_METADATA']}
    assert not w.publish_gates_complete(state)
    state['approved_human_gates'].append('G11B_THUMBNAIL')
    assert w.publish_gates_complete(state)


def test_g11a_not_allowed_without_q11_or_scope():
    state={'allowed_stages':['G11A','G11B','G12'],'passed_qc':[],'approved_human_gates':[]}
    assert not w.can_start_stage('G11A',state)
    assert not w.can_start_stage('G13',state)
