import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('matcher',ROOT/'tools'/'visual_narration_matcher_v1328.py')
matcher=importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(matcher)
except FileNotFoundError:
    raise

SCENES=[
 {'scene_id':'S1','src_in_s':10,'src_out_s':20,'visible_actor_ids':['AN'], 'visible_actions':['phát hiện thư'], 'storyline':'present','event_ids':['E1'],'scene_status':'VISUALLY_REVIEWED','motion_clips':['analysis/clip1.mp4'],'visual_description':'An tìm thấy lá thư bí mật'},
 {'scene_id':'S2','src_in_s':21,'src_out_s':29,'visible_actor_ids':['AN'], 'visible_actions':['nổi giận'], 'storyline':'present','event_ids':['E2'],'scene_status':'VISUALLY_REVIEWED','motion_clips':['analysis/clip2.mp4'],'visual_description':'An tức giận'},
 {'scene_id':'S3','src_in_s':30,'src_out_s':40,'visible_actor_ids':['BINH'], 'visible_actions':['nổi giận'], 'storyline':'past','event_ids':['E3'],'scene_status':'VISUALLY_REVIEWED','motion_clips':['analysis/clip3.mp4'],'visual_description':'Binh nổi giận trong quá khứ'},
]
EVENTS=[{'event_id':'E1','scene_ids':['S1'],'characters':['AN'],'action':'phát hiện thư','verification':'VISUAL_ONLY_VERIFIED'},
        {'event_id':'E2','scene_ids':['S2'],'characters':['AN'],'action':'nổi giận','verification':'VISUAL_ONLY_VERIFIED'}]

def beat(id='B1', **kw):
    d={'beat_id':id,'narration_text':'An phát hiện lá thư bí mật','actor':'AN','action':'phát hiện thư','storyline':'present','event_ids':['E1'],'voice_in_s':0,'voice_out_s':5}
    d.update(kw)
    return d

def test_actor_storyline_rejects_before_semantic_rank():
    res=matcher.match_beats([beat()],SCENES,EVENTS,source_duration_s=60,similarities={'B1':{'S3':1.0}})
    assert res['decisions'][0]['selected_scene_id']=='S1'
    assert res['decisions'][0]['selected_shot_id']=='SHOT-B1-S1'
    rejects={x['scene_id']:x['hard_reject_reasons'] for x in res['candidates'] if x['match_status']=='REJECTED'}
    assert 'S3' in rejects and ('ACTOR_MISMATCH' in rejects['S3'] or 'STORYLINE_MISMATCH' in rejects['S3'])

def test_similarity_does_not_fabricate_visual_verification():
    scenes=[dict(SCENES[0],scene_status='INDEXED',motion_clips=[],event_ids=['E1'])]
    res=matcher.match_beats([beat()],scenes,EVENTS,source_duration_s=60,similarities={'B1':{'S1':0.99}})
    assert res['decisions'][0]['match_status']=='CANDIDATE'
    assert any(w['code']=='UNVERIFIED_VISUAL' for w in res['warnings'])

def test_uninspected_motion_clip_is_not_verified_visual():
    r=matcher.match_beats([beat()],SCENES[:1],EVENTS,source_duration_s=60)
    assert r['decisions'][0]['match_status']=='CANDIDATE'
    verified=[dict(SCENES[0],motion_verification='VERIFIED')]
    r2=matcher.match_beats([beat()],verified,EVENTS,source_duration_s=60)
    assert r2['decisions'][0]['match_status']=='VERIFIED_VISUAL'

def test_unknown_actor_is_not_false_hard_reject():
    scenes=[dict(SCENES[0],visible_actor_ids=[],scene_status='INDEXED')]
    res=matcher.match_beats([beat()],scenes,EVENTS,source_duration_s=60)
    assert all(x['match_status']!='REJECTED' for x in res['candidates'])

def test_no_match_does_not_fill_with_wrong_scene():
    res=matcher.match_beats([beat(actor='CHI',storyline='future',event_ids=['X'],action='bắt tàu')],SCENES,EVENTS,source_duration_s=60)
    assert res['decisions'][0]['selected_shot_id'] is None
    assert res['decisions'][0]['match_status']=='NO_MATCH'
    assert any(w['code']=='NO_VISUAL_MATCH' for w in res['warnings'])

def test_source_time_out_of_bounds_rejected():
    scenes=[dict(SCENES[0],src_out_s=80)]
    res=matcher.match_beats([beat()],scenes,EVENTS,source_duration_s=60)
    assert res['candidates'][0]['match_status']=='REJECTED'
    assert 'INVALID_SOURCE_RANGE' in res['candidates'][0]['hard_reject_reasons']

def test_voice_placement_preserves_time_domains_and_anchors():
    res=matcher.match_beats([beat()],SCENES,EVENTS,source_duration_s=60)
    placement=matcher.build_placement_suggestions([beat()],res['decisions'],source_duration_s=60)
    item=placement['placements'][0]
    assert item['timeline_in_s']==0 and item['timeline_out_s']==5
    assert item['source_in_s']==10 and item['source_out_s']==15
    assert item['anchor_provenance']=='VOICE_BEAT_TIMESTAMP'

def test_no_fake_word_alignment_without_real_timestamps():
    b=beat();b.pop('voice_in_s');b.pop('voice_out_s')
    r=matcher.match_beats([b],SCENES,EVENTS,source_duration_s=60)
    placement=matcher.build_placement_suggestions([b],r['decisions'],source_duration_s=60)
    assert placement['placements'][0]['timeline_in_s'] is None
    assert placement['placements'][0]['anchor_provenance']=='UNKNOWN'

def test_scene_reuse_penalty_prefers_nonrepeated_relevant_scene():
    b1=beat('B1',event_ids=[],action='',narration_text='An nổi giận',actor='AN')
    b2=beat('B2',event_ids=[],action='',narration_text='An nổi giận',actor='AN')
    res=matcher.match_beats([b1,b2],SCENES,EVENTS,source_duration_s=60)
    selected=[d['selected_scene_id'] for d in res['decisions']]
    assert len(set(selected))==2

def test_duplicate_ids_rejected():
    try: matcher.match_beats([beat(),beat()],SCENES,EVENTS,source_duration_s=60)
    except ValueError as e: assert 'duplicate beat' in str(e).lower()
    else: assert False,'Expected duplicate failure'

def test_cli_job_bound_outputs(tmp_path):
    job=tmp_path/'JOB';(job/'analysis').mkdir(parents=True)
    (job/'beats').mkdir()
    (job/'analysis'/'scene_catalog.json').write_text(json.dumps(SCENES),encoding='utf-8')
    (job/'analysis'/'visual_events.json').write_text(json.dumps(EVENTS),encoding='utf-8')
    (job/'beats'/'beats.json').write_text(json.dumps([beat()]),encoding='utf-8')
    cmd=[sys.executable,str(ROOT/'tools'/'visual_narration_matcher_v1328.py'),'--job-dir',str(job),'--source-duration', '60', '--beats','beats/beats.json','--scenes','analysis/scene_catalog.json','--events','analysis/visual_events.json']
    got=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
    assert got.returncode==0,got.stderr
    assert (job/'shots'/'shot_candidates.json').exists()
    assert (job/'shots'/'shot_selection_decisions.json').exists()
    assert (job/'shots'/'shot_map.csv').exists()
    import csv
    with (job/'shots'/'shot_map.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    assert rows[0]['shot_id']=='SHOT-B1-S1'
    assert rows[0]['actor_evidence']=='AN'
    assert rows[0]['action_evidence']=='phát hiện thư'
    assert rows[0]['visual_evidence']
    assert 'transcript_evidence' in rows[0] and 'evidence' in rows[0]
    assert (job/'timeline'/'visual_placement_suggestions.json').exists()
    assert (job/'shots'/'matching_warnings.json').exists()
    assert not (tmp_path/'shots').exists()

def test_shot_ids_unique_across_beats_even_if_scene_is_reused():
    res=matcher.match_beats([beat('B1'),beat('B2')],SCENES[:1],EVENTS,source_duration_s=60)
    a,b=res['decisions']
    assert a['selected_scene_id']==b['selected_scene_id']=='S1'
    assert a['selected_shot_id']!=b['selected_shot_id']

def test_cli_rejects_escape(tmp_path):
    job=tmp_path/'JOB';job.mkdir()
    r=subprocess.run([sys.executable,str(ROOT/'tools'/'visual_narration_matcher_v1328.py'),'--job-dir',str(job),'--source-duration','60','--beats','../outside.json'],capture_output=True,text=True)
    assert r.returncode!=0
