"""Regression tests for the remote media upload bridge (no multimedia inference)."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('media_evidence_handoff', ROOT / 'tools/media_evidence_handoff.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def make_job(tmp_path):
    job = tmp_path / 'review-job'
    (job / 'analysis' / 'snippets').mkdir(parents=True)
    (job / 'analysis' / 'snippets' / 'clip.mp4').write_bytes(b'example-small-video-binary')
    (job / 'analysis' / 'snippets' / 'speech.wav').write_bytes(b'example-small-audio-binary')
    return job


def sample_items():
    return [
        {'path': 'analysis/snippets/clip.mp4', 'kind': 'video', 'start_s': 94.0, 'end_s': 105.0},
        {'path': 'analysis/snippets/speech.wav', 'kind': 'audio', 'start_s': 99.0, 'end_s': 105.0},
    ]


def make_bundle(job):
    return mod.build_media_evidence_bundle(job, request_id='G08-EV-001', stage='G08',
        question='Nhân vật có thật sự cầm vật trong tay không?', items=sample_items())


def test_generates_single_zip_with_real_clips_and_manifest(tmp_path):
    job = make_job(tmp_path)
    result = make_bundle(job)
    archive = Path(result['zip_path'])
    assert archive.is_file() and archive.parent.is_relative_to(job)
    assert result['status'] == 'ZIP_READY_NEEDS_TRANSFER'
    assert result['download_url'] is None
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == result['zip_sha256']
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert names[0] == 'manifest.json'
        assert len(names) == 3
        manifest = json.loads(z.read('manifest.json'))
        assert manifest['request_id'] == 'G08-EV-001'
        assert manifest['stage'] == 'G08'
        assert len(manifest['files']) == 2
        for m in manifest['files']:
            assert z.read(m['zip_member']) == (job / m['source_relpath']).read_bytes()
            assert hashlib.sha256(z.read(m['zip_member'])).hexdigest() == m['sha256']
            assert m['inspected_by_chatgpt'] is False


def test_upload_validation_is_not_claim_of_hearing_or_watching(tmp_path):
    job = make_job(tmp_path)
    result = make_bundle(job)
    receipt = mod.verify_received_bundle(Path(result['zip_path']), expected_sha256=result['zip_sha256'])
    assert receipt['status'] == 'RECEIVED_NOT_INSPECTED'
    assert receipt['video_seen'] is False and receipt['audio_heard'] is False
    assert receipt['file_count'] == 2


def test_package_does_not_modify_originals(tmp_path):
    job = make_job(tmp_path)
    before = [(f, f.read_bytes()) for f in (job/'analysis/snippets').iterdir()]
    make_bundle(job)
    assert all(f.read_bytes() == b for f, b in before)


@pytest.mark.parametrize('bad', ['../private.mp4', '/tmp/private.mp4', 'analysis/../../private.mp4', 'C:/private.mp4'])
def test_rejects_paths_outside_job(tmp_path, bad):
    job = make_job(tmp_path)
    with pytest.raises(mod.MediaEvidenceError):
        mod.build_media_evidence_bundle(job, request_id='G04-001', stage='G04', question='Nhìn hành động',
            items=[{'path':bad,'kind':'video','start_s':0,'end_s':5}])


def test_rejects_symlinks(tmp_path):
    job=make_job(tmp_path)
    alias=job/'analysis/snippets/linked.mp4'
    try:
        alias.symlink_to(job/'analysis/snippets/clip.mp4')
    except (OSError,NotImplementedError):
        pytest.skip('symlink unavailable')
    with pytest.raises(mod.MediaEvidenceError):
        mod.build_media_evidence_bundle(job,request_id='G04-002',stage='G04',question='Check',items=[{'path':'analysis/snippets/linked.mp4','kind':'video','start_s':0,'end_s':5}])


@pytest.mark.parametrize('start,end,kind', [(-1,3,'video'),(9,9,'video'),(0,61,'video'),(0,241,'audio')])
def test_rejects_invalid_or_oversize_timeline(tmp_path,start,end,kind):
    job=make_job(tmp_path)
    file='clip.mp4' if kind=='video' else 'speech.wav'
    with pytest.raises(mod.MediaEvidenceError):
        mod.build_media_evidence_bundle(job,request_id='G14-003',stage='G14',question='Check',items=[{'path':f'analysis/snippets/{file}','kind':kind,'start_s':start,'end_s':end}])


def test_size_limit_enforced(tmp_path):
    job=make_job(tmp_path)
    with pytest.raises(mod.MediaEvidenceError):
        mod.build_media_evidence_bundle(job, request_id='G08-004', stage='G08',question='Check',items=sample_items(),max_total_bytes=10)


def test_no_duplicate_output_replacement(tmp_path):
    job=make_job(tmp_path)
    first=make_bundle(job)
    with pytest.raises(mod.MediaEvidenceError):
        make_bundle(job)
    assert Path(first['zip_path']).is_file()


def test_strict_extensions_types_and_request_ids(tmp_path):
    job=make_job(tmp_path)
    with pytest.raises(mod.MediaEvidenceError):
        mod.build_media_evidence_bundle(job,request_id='../../BAD',stage='G08',question='Check',items=sample_items())
    with pytest.raises(mod.MediaEvidenceError):
        mod.build_media_evidence_bundle(job,request_id='G01-001',stage='G999',question='Check',items=sample_items())
    with pytest.raises(mod.MediaEvidenceError):
        mod.build_media_evidence_bundle(job,request_id='G08-002',stage='G08',question='Check',items=[{'path':'analysis/snippets/speech.wav','kind':'video','start_s':0,'end_s':4}])


def test_rejects_checksum_mismatch(tmp_path):
    job=make_job(tmp_path)
    r=make_bundle(job)
    with pytest.raises(mod.MediaEvidenceError):
        mod.verify_received_bundle(Path(r['zip_path']),expected_sha256='0'*64)


def test_rejects_injected_zip_member(tmp_path):
    archive=tmp_path/'dangerous.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('manifest.json','{}')
        z.writestr('../escape.exe', 'x')
    with pytest.raises(mod.MediaEvidenceError):
        mod.verify_received_bundle(archive,expected_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())


def test_policies_force_user_upload_and_real_inspection():
    s=(ROOT/'SKILL.md').read_text(encoding='utf-8')
    p=ROOT/'references/MEDIA_EVIDENCE_HANDOFF_V1320.md'
    assert p.is_file() and p.name in s
    policy=p.read_text(encoding='utf-8')
    for fragment in ['ZIP_READY_NEEDS_TRANSFER','RECEIVED_NOT_INSPECTED','WAITING_FOR_AUDIO_UPLOAD','NOT_VERIFIED','sandbox:/mnt/data/', 'deviceId', 'ChatGPT thực sự', 'G02','G04','G08','G14']:
        assert fragment in policy
    assert 'Không tự tạo link giả' in policy


def test_rejects_symlinked_output_root(tmp_path):
    job=make_job(tmp_path)
    external=tmp_path/'external'
    external.mkdir()
    analysis=job/'analysis'
    alias=analysis/'media_for_chat'
    try:
        alias.symlink_to(external, target_is_directory=True)
    except (OSError,NotImplementedError):
        pytest.skip('symlink unavailable')
    with pytest.raises(mod.MediaEvidenceError):
        make_bundle(job)
    assert list(external.iterdir()) == []
