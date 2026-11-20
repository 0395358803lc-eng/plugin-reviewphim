"""REVIEW_PHIM 1.3.19 additive guard for publish/thumbnail stages.

Call *in addition* to legacy work_package_state.can_dispatch. This is an
offline policy oracle, not approval, permission, or execution infrastructure.
"""
from typing import Any


def _set(state:dict[str,Any],name:str)->set[str]:
    values=state.get(name,[])
    return set(values) if isinstance(values,(tuple,list,set)) else set()


def can_start_stage(stage:str,state:dict[str,Any])->bool:
    stages=_set(state,'allowed_stages')
    qcs=_set(state,'passed_qc')
    gates=_set(state,'approved_human_gates')
    if stage not in stages:
        return False
    if stage=='G11A':
        return 'Q11' in qcs
    if stage=='G11B':
        return 'G11A' in stages and 'Q11A' in qcs and 'G11A_METADATA' in gates
    if stage=='G12' and ('G11A' in stages or 'G11B' in stages):
        return {'G11A','G11B'}.issubset(stages) and {'Q11A','Q11B'}.issubset(qcs) and {'G11A_METADATA','G11B_THUMBNAIL'}.issubset(gates)
    return True


def publish_gates_complete(state:dict[str,Any])->bool:
    stages=_set(state,'allowed_stages')
    if not (stages & {'G11A','G11B'}):
        return True  # pre-v1.3.19 legacy package
    if not {'G11A','G11B'}.issubset(stages):
        return False
    return {'Q11A','Q11B'}.issubset(_set(state,'passed_qc')) and {'G11A_METADATA','G11B_THUMBNAIL'}.issubset(_set(state,'approved_human_gates'))
