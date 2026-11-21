"""Contract regression for REVIEW_PHIM v1.3.29 sidecar thumbnail and persistent logo."""
import hashlib
import importlib
import json
import sys
import types
from pathlib import Path
import pytest

TOOLS=Path(__file__).parents[1]/'tools'


def workflow(monkeypatch):
    # Import patch layer against a stub of the legacy engine. This test is for
    # v1.3.29 contract, not existing stage-state-machine integration.
    core=types.ModuleType('project_flow_v1325')
    core.validate_plan=lambda plan:['G11B','G12','G15']
    core.verify_thumbnail=lambda plan,evidence: {'status':'LEGACY_FILE_ACCEPTED'}
    monkeypatch.setitem(sys.modules,'project_flow_v1325',core)
    monkeypatch.syspath_prepend(str(TOOLS))
    sys.modules.pop('project_flow_v1329',None)
    return importlib.import_module('project_flow_v1329')


def plan(tmp_path):
    manifest='publish/thumbnail_handoff_v1329.json'
    return {
      'JOB_DIR':str(tmp_path),
      'production_config':{
         'thumbnail_delivery':'DOWNLOAD_SEPARATELY_UPLOAD_IN_YOUTUBE_STUDIO',
         'thumbnail_embed_in_video':False,'intro_card_enabled':False,
         'g12_input_thumbnail':False,
         'logo_overlay':{'enabled':True,'position':'top_left','start':'first_frame','end':'last_frame','mode':'persistent_watermark'}},
      'stage_config':{'G12':{'logo_overlay':True,'intro_card_enabled':False}},
      'allowed_stages':['G11','G11A','G11B','G12','G13','G14','G15'],
      'stage_outputs':{'G11':['output/base.mp4'],'G11A':['publish/metadata.json'],
        'G11B':[manifest], 'G12':['output/with_logo.mp4'],'G13':['output/mixed.mp4'],
        'G14':['output/checked.mp4'],'G15':['output/final.mp4','publish/youtube_assets.json']},
      'stage_dependencies':{'G12':['G11'],'G13':['G12'],'G14':['G13'],
        'G15':['G14','G11B','G11A']},
      'stage_inputs':{'G12':{str(tmp_path/'logo.png'):'a'*64}}
    }


def test_new_plan_keeps_thumbnail_separate_from_video(tmp_path,monkeypatch):
    m=workflow(monkeypatch); p=plan(tmp_path)
    assert m.validate_plan(p)==['G11B','G12','G15']
    assert m.is_youtube_separate_mode(p)


def test_new_plan_rejects_intro_or_thumbnail_dependency(tmp_path,monkeypatch):
    m=workflow(monkeypatch); p=plan(tmp_path)
    p['production_config']['intro_card_enabled']=True
    with pytest.raises(ValueError,match='intro'):
        m.validate_plan(p)
    p=plan(tmp_path);p['stage_dependencies']['G12']=['G11','G11B']
    with pytest.raises(ValueError,match='G11B'):
        m.validate_plan(p)


def test_new_plan_requires_logo_source_and_g12_mp4(tmp_path,monkeypatch):
    m=workflow(monkeypatch); p=plan(tmp_path)
    p['stage_inputs']['G12']={}
    with pytest.raises(ValueError,match='logo'):
        m.validate_plan(p)
    p=plan(tmp_path);p['stage_outputs']['G12']=['output/G12.dat']
    with pytest.raises(ValueError,match='MP4'):
        m.validate_plan(p)


def test_thumbnail_manifest_is_verified_without_user_copy(tmp_path,monkeypatch):
    m=workflow(monkeypatch);p=plan(tmp_path)
    data={'schema':'youtube-thumbnail-handoff.v1','delivery_mode':'DOWNLOAD_SEPARATELY_UPLOAD_IN_YOUTUBE_STUDIO',
          'title':'Giải mã bộ phim','title_sha256':hashlib.sha256('Giải mã bộ phim'.encode()).hexdigest(),
          'image_sha256':'b'*64, 'format':'png','width':1280,'height':720,
          'generation_ref':'tool-image-output-actual','download_ref':'verified-chatgpt-file-link',
          'image_inspected':True,'user_can_download':True,
          'embed_in_video':False}
    f=tmp_path/p['stage_outputs']['G11B'][0];f.parent.mkdir(parents=True);f.write_text(json.dumps(data),encoding='utf-8')
    ev={'delivery_mode':data['delivery_mode'],'title':data['title'],
        'title_sha256':data['title_sha256'],'image_sha256':data['image_sha256'],
        'relative_path':p['stage_outputs']['G11B'][0], 'generation_ref':data['generation_ref']}
    assert m.verify_thumbnail(p,ev)['status']=='DELIVERABLE_REFERENCED'
    ev['image_sha256']='c'*64
    with pytest.raises(ValueError,match='image_sha256'):
        m.verify_thumbnail(p,ev)


def test_legacy_thumbnail_path_is_still_supported(tmp_path,monkeypatch):
    m=workflow(monkeypatch)
    assert m.verify_thumbnail({},None)=={'status':'LEGACY_FILE_ACCEPTED'}
