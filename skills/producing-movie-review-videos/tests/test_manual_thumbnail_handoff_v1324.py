"""v1.3.24 TDD: user manually places a ChatGPT-generated thumbnail into JOB_DIR."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import zlib

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'tools' / 'manual_thumbnail_handoff_v1324.py'


def get_module():
    spec = importlib.util.spec_from_file_location('manual_thumbnail_handoff_v1324', SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_png(path, width=1280, height=720):
    def chunk(name, data):
        return (struct.pack('>I', len(data)) + name + data +
                struct.pack('>I', zlib.crc32(name + data) & 0xffffffff))
    row = b'\x00' + b'\x00\x00\x00' * width
    payload = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',width,height,8,2,0,0,0)) +
               chunk(b'IDAT',zlib.compress(row*height)) + chunk(b'IEND',b''))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def inputs(job, file_hash=None):
    m=get_module()
    title='Bí mật sau màn đêm'
    approval={'source':'user_message','action':'G11B_THUMBNAIL','approval_ref':'turn-real-user-1',
              'title_sha256':m.title_digest(title),'user_confirmed_placement':True,
              'user_selected_file':'youtube_thumbnail.png'}
    visual={'generated_image_seen_by_chatgpt':True,'text_checked_by_chatgpt':True,
            'source_image_evidence_ref':'chat-image-1'}
    return m, title, approval, visual


def verify(job, title, approval, visual, **kw):
    return get_module().verify_drop(job, title=title, approval=approval, visual=visual,
                                    image_name='youtube_thumbnail.png', **kw)


def test_one_exact_folder_with_no_automatic_transfer(tmp_path):
    m=get_module()
    d=m.handoff_destination(tmp_path, 'png')
    assert d['relative_path']=='assets/youtube_thumbnail.png'
    assert Path(d['absolute_path'])==tmp_path/'assets'/'youtube_thumbnail.png'
    assert d['requires_user_copy'] is True
    assert not (tmp_path/'assets').exists()  # only returns instructions; no side effect
    with pytest.raises(ValueError):m.handoff_destination(tmp_path, 'webp')
    with pytest.raises(ValueError):m.handoff_destination(tmp_path, '../jpg')


def test_wait_for_user_copy_not_false_pass(tmp_path):
    m,title,approval,visual=inputs(tmp_path)
    out=verify(tmp_path,title,approval,visual)
    assert out['status']=='WAITING_FOR_USER_IMAGE_PLACEMENT'
    assert not out['ready_for_q11b_qc']


def test_one_explicit_user_reply_can_both_confirm_copy_and_approve(tmp_path):
    digest=make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    m,title,approval,visual=inputs(tmp_path)
    out=verify(tmp_path,title,approval,visual,expected_source_sha256=digest)
    assert out['status']=='FILE_ACCEPTED'
    assert out['ready_for_q11b_qc']
    assert out['image_sha256']==digest
    assert out['image_identity']=='SHA256_MATCH'
    assert out['image_width']==1280 and out['image_height']==720
    assert out['relative_path']=='assets/youtube_thumbnail.png'
    assert out['title_sha256']==m.title_digest(title)
    assert out['qc_pass_claimed'] is False # actual visual/FFmpeg QC happens later
    assert not (tmp_path/'assets'/'intro_card.png').exists()


def test_without_generated_byte_digest_record_user_attestation_not_false_byte_match(tmp_path):
    make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    m,title,approval,visual=inputs(tmp_path)
    out=verify(tmp_path,title,approval,visual)
    assert out['status']=='FILE_ACCEPTED'
    assert out['image_identity']=='USER_ATTESTED_NOT_BYTE_MATCHED'
    assert not out['qc_pass_claimed']


def test_download_copy_alone_is_not_content_approval(tmp_path):
    make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    m,title,approval,visual=inputs(tmp_path)
    for bad in ({**approval,'source':'assistant'},
                {**approval,'action':'COPY_COMPLETE'},
                {**approval,'user_confirmed_placement':False},
                {**approval,'approval_ref':''}):
        assert verify(tmp_path,title,bad,visual)['status']=='WAITING_FOR_HUMAN_APPROVAL'


def test_wrong_generated_image_hash_never_passes(tmp_path):
    make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    m,title,approval,visual=inputs(tmp_path)
    out=verify(tmp_path,title,approval,visual,expected_source_sha256='0'*64)
    assert out['status']=='BLOCKED_SOURCE_HASH'
    assert not out['ready_for_q11b_qc']


def test_title_change_invalidates_existing_approval(tmp_path):
    make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    m,title,approval,visual=inputs(tmp_path)
    out=verify(tmp_path,title+' mới',approval,visual)
    assert out['status']=='WAITING_FOR_HUMAN_APPROVAL'


def test_visual_evidence_missing_never_verifies(tmp_path):
    make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    m,title,approval,visual=inputs(tmp_path)
    for bad in ({**visual,'generated_image_seen_by_chatgpt':False},
                {**visual,'source_image_evidence_ref':''}):
        assert verify(tmp_path,title,approval,bad)['status']=='NOT_VERIFIED'


def test_extension_cannot_masquerade_as_png(tmp_path):
    path=tmp_path/'assets'/'youtube_thumbnail.png'
    path.parent.mkdir();path.write_bytes(b'not a real png')
    m,title,approval,visual=inputs(tmp_path)
    assert verify(tmp_path,title,approval,visual)['status']=='BLOCKED_IMAGE_FORMAT'


def test_low_resolution_and_wrong_aspect_rejected(tmp_path):
    m,title,approval,visual=inputs(tmp_path)
    for size in [(320,180),(1280,800)]:
        make_png(tmp_path/'assets'/'youtube_thumbnail.png',*size)
        assert verify(tmp_path,title,approval,visual)['status']=='BLOCKED_IMAGE_GEOMETRY'


def test_explicit_expected_path_cannot_escape_job(tmp_path):
    m,title,approval,visual=inputs(tmp_path)
    make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    for path in ('../youtube_thumbnail.png','other.png','intro_card.png'):
        assert m.verify_drop(tmp_path,title=title,approval=approval,visual=visual,image_name=path)['status']=='BLOCKED_PATH'


def test_symlink_file_not_followed(tmp_path):
    m,title,approval,visual=inputs(tmp_path)
    real=tmp_path/'source.png';make_png(real)
    (tmp_path/'assets').mkdir()
    try:(tmp_path/'assets'/'youtube_thumbnail.png').symlink_to(real)
    except OSError as exc:
        if getattr(exc,'winerror',None)==1314:pytest.skip('Windows account lacks symbolic-link privilege')
        raise
    assert verify(tmp_path,title,approval,visual)['status']=='BLOCKED_PATH'


def test_repeat_verification_does_not_write_or_reapprove(tmp_path):
    m,title,approval,visual=inputs(tmp_path)
    path=tmp_path/'assets'/'youtube_thumbnail.png'
    make_png(path)
    before=(path.stat().st_mtime_ns,path.read_bytes())
    one=verify(tmp_path,title,approval,visual)
    two=verify(tmp_path,title,approval,visual)
    assert one==two
    assert (path.stat().st_mtime_ns,path.read_bytes())==before


def test_manual_handoff_policy_enters_main_skill_and_intro(tmp_path):
    policy=(ROOT/'references'/'MANUAL_THUMBNAIL_HANDOFF_V1324.md').read_text('utf-8')
    main=(ROOT/'SKILL.md').read_text('utf-8')
    old=(ROOT/'references'/'THUMBNAIL_INTRO_POLICY_V1319.md').read_text('utf-8')
    intro=(ROOT/'references'/'INTRO_CARD_INTEGRATION_V1319.md').read_text('utf-8')
    one=(ROOT.parent/'one-click-review-execution'/'SKILL.md').read_text('utf-8')
    assert 'MANUAL_THUMBNAIL_HANDOFF_V1324.md' in main
    assert 'WAITING_FOR_USER_IMAGE_PLACEMENT' in policy
    assert 'assets/youtube_thumbnail.png' in policy
    assert 'G11B_THUMBNAIL' in policy
    assert 'MANUAL_THUMBNAIL_HANDOFF_V1324.md' in old
    assert 'MANUAL_THUMBNAIL_HANDOFF_V1324.md' in intro
    assert 'MANUAL_THUMBNAIL_HANDOFF_V1324.md' in one


def test_g11b_package_cannot_finish_without_verified_manual_file():
    """A human checkbox and Q11B string do not prove that an image is on disk."""
    import importlib.util
    fp=ROOT/'tools'/'workflow_integrity_v1323.py'
    spec=importlib.util.spec_from_file_location('wf1323', fp)
    w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
    plan={'WORK_PACKAGE_ID':'WP24','schema_version':'work-package.v2','deviceId':'d1',
          'JOB_DIR':'D:\\Film\\Job','SOURCE_MOVIE':'D:\\Film\\movie.mkv','source_hash':'a'*64,
          'allowed_stages':['G11B'],'task_ids':['G11B.THUMBNAIL.FULL'],
          'allowed_read_roots':['D:\\Film'],'allowed_write_roots':['D:\\Film\\Job'],
          'repair_budget':{'per_issue':0,'total':0,'allowed_kinds':[]},
          'install_budget':[],'human_gates':[]}
    dig=w.hash_plan(plan)
    state={'status':'RUNNING','approval_ref':'turn-user','plan_hash':dig,'approved_plan_hash':dig,
           'source_hash':'a'*64,'deviceId':'d1','JOB_DIR':plan['JOB_DIR'],
           'lock_verified':True,'lock_owner':'session','task_qc':{'G11B.THUMBNAIL.FULL':'PASS'},
           'qc_gates_passed':['Q11B'],'approved_human_gates':['G11B_THUMBNAIL'],
           'final_qc':True,'unresolved_blockers':[],'stage_evidence':{}}
    assert not w.validate_package_completion(plan,state).allowed
    state['stage_evidence']['Q11B']={'thumbnail_file_verified':True,'thumbnail_approval_hash_matches':True}
    assert w.validate_package_completion(plan,state).allowed


def test_assets_symlink_folder_is_not_followed(tmp_path):
    m,title,approval,visual=inputs(tmp_path)
    outside=tmp_path/'elsewhere'
    make_png(outside/'youtube_thumbnail.png')
    try:(tmp_path/'assets').symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        if getattr(exc,'winerror',None)==1314:pytest.skip('Windows account lacks symbolic-link privilege')
        raise
    assert verify(tmp_path,title,approval,visual)['status']=='BLOCKED_PATH'
