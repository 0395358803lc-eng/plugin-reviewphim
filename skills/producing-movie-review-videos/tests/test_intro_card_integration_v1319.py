import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('intro',ROOT/'tools/thumbnail_intro_policy.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_intro_two_seconds_25fps_and_voice_shift():
    res=mod.validate_intro_timing({'fps_num':25,'fps_den':1,'intro_frames':50,'intro_actual_duration_s':2.0,'narration_start_frame':50,'intro_visual_inspected':True,'visual_evidence':'qc/frame.png'})
    assert res['ready']


def test_intro_early_narration_and_wrong_duration_rejected():
    res=mod.validate_intro_timing({'fps_num':25,'fps_den':1,'intro_frames':40,'intro_actual_duration_s':1.6,'narration_start_frame':0,'intro_visual_inspected':True,'visual_evidence':'qc/frame.png'})
    assert not res['ready'] and 'INTRO_NOT_TWO_SECONDS' in res['issues'] and 'VOICE_START_BEFORE_INTRO_END' in res['issues']


def test_intro_not_passed_from_timing_only():
    res=mod.validate_intro_timing({'fps_num':30,'fps_den':1,'intro_frames':60,'intro_actual_duration_s':2.,'narration_start_frame':60,'intro_visual_inspected':False,'visual_evidence':''})
    assert not res['ready'] and 'INTRO_VISUAL_NOT_VERIFIED' in res['issues']
