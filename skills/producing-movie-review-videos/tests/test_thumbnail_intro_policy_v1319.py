import importlib.util
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('thumb',ROOT/'tools/thumbnail_intro_policy.py')
thumb=importlib.util.module_from_spec(spec)
spec.loader.exec_module(thumb)


def test_png_real_bytes_and_visual_evidence_required(tmp_path):
    # Real 1x1 PNG (invalid aspect, intentionally testing reject first)
    png=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')
    p=tmp_path/'x.png';p.write_bytes(png)
    r=thumb.validate_thumbnail(p, title='Tiêu đề', manifest={'title':'Tiêu đề','title_sha256':thumb.title_digest('Tiêu đề'),'image_sha256':hashlib.sha256(png).hexdigest(),'visual_inspected':True,'visual_evidence':'qc/real.png'},approval={'gate':'G11B_THUMBNAIL','approval_ref':'a','image_sha256':hashlib.sha256(png).hexdigest()})
    assert not r['ready'] and 'IMAGE_GEOMETRY_INVALID' in r['issues']


def test_missing_image_cannot_pass_from_manifest(tmp_path):
    r=thumb.validate_thumbnail(tmp_path/'not-exists.png', title='Tên', manifest={'title':'Tên','visual_inspected':True},approval={'gate':'G11B_THUMBNAIL','approval_ref':'a'})
    assert not r['ready'] and 'IMAGE_MISSING' in r['issues']


def test_no_visual_evidence_cannot_pass(tmp_path):
    from PIL import Image
    p=tmp_path/'ok.png';Image.new('RGB',(1280,720)).save(p)
    d=hashlib.sha256(p.read_bytes()).hexdigest()
    r=thumb.validate_thumbnail(p,title='Tiêu đề',manifest={'title':'Tiêu đề','title_sha256':thumb.title_digest('Tiêu đề'),'image_sha256':d,'visual_inspected':False,'visual_evidence':''},approval={'gate':'G11B_THUMBNAIL','approval_ref':'a','image_sha256':d})
    assert not r['ready'] and 'VISUAL_NOT_VERIFIED' in r['issues']


def test_mismatched_title_sha_blocks_even_with_evidence(tmp_path):
    from PIL import Image
    p=tmp_path/'ok.png';Image.new('RGB',(1280,720)).save(p)
    d=hashlib.sha256(p.read_bytes()).hexdigest()
    r=thumb.validate_thumbnail(p,title='Tên thật',manifest={'title':'Tên cũ','title_sha256':thumb.title_digest('Tên cũ'),'image_sha256':d,'visual_inspected':True,'visual_evidence':'a'},approval={'gate':'G11B_THUMBNAIL','approval_ref':'a','image_sha256':d})
    assert not r['ready'] and 'TITLE_HASH_MISMATCH' in r['issues']
