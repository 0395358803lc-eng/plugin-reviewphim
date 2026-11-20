"""REVIEW_PHIM v1.3.20 -- bounded offline ZIP packaging of short AV evidence.

This helper NEVER extracts movie clips, reads remote devices, creates a public URL,
uploads files, plays audio, watches videos, or grants permission. Callers must
first prepare short clips under an approved JOB_DIR and obtain any necessary
read/write/export approvals. A ZIP is proof of packaging, NOT of inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from datetime import datetime, timezone
import zipfile

SCHEMA = 'review-phim-media-evidence.v1'
MAX_FILES = 6
DEFAULT_MAX_BYTES = 30 * 1024 * 1024
ALLOWED = {
    'video': {'.mp4', '.mov', '.webm'},
    'audio': {'.wav', '.m4a', '.mp3', '.flac'},
    'image': {'.png', '.jpg', '.jpeg', '.webp'},
}
DURATION_CAP = {'video': 60.0, 'audio': 240.0}
VALID_STAGE = {f'G{i:02d}' for i in range(1, 16)} | {'G11A', 'G11B'}
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')


class MediaEvidenceError(ValueError):
    """A request is unsafe, invalid, incomplete or outside its bounded scope."""


def _fail(message: str) -> None:
    raise MediaEvidenceError(message)


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _within(file: Path, root: Path) -> bool:
    try:
        file.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_source(job_dir: Path, rel: str) -> tuple[Path, str]:
    if not isinstance(rel, str) or not rel or '\\' in rel or ':' in rel:
        _fail('Paths must be POSIX-style relative JOB_DIR paths')
    parts = PurePosixPath(rel).parts
    if PurePosixPath(rel).is_absolute() or not parts or any(p in ('.', '..') for p in parts):
        _fail('Path traversal/absolute paths are forbidden')
    candidate = job_dir.joinpath(*parts)
    # Explicitly reject links anywhere in the walk (Windows junctions resolve outside roots).
    walk = job_dir
    for p in parts:
        walk = walk / p
        if walk.is_symlink():
            _fail('Symlink/reparse source is not allowed')
    resolved = candidate.resolve(strict=True)
    if not _within(resolved, job_dir) or not resolved.is_file():
        _fail('Source must be an existing file within approved JOB_DIR')
    return resolved, PurePosixPath(*parts).as_posix()


def _validate_item(item: dict, root: Path) -> tuple[Path, dict]:
    if not isinstance(item, dict) or not isinstance(item.get('kind'), str):
        _fail('Each item requires a kind and a path')
    kind = item['kind']
    if kind not in ALLOWED:
        _fail('Unsupported media kind')
    path, rel = _safe_source(root, item.get('path'))
    if path.suffix.lower() not in ALLOWED[kind]:
        _fail('Media extension does not match declared kind')
    start = item.get('start_s')
    end = item.get('end_s')
    if kind != 'image':
        if type(start) not in (int, float) or type(end) not in (int, float):
            _fail('Audio/video requires start_s and end_s')
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start or end - start > DURATION_CAP[kind]:
            _fail('Requested evidence exceeds time or validity cap')
    else:
        if start is not None and (type(start) not in (int,float) or not math.isfinite(start) or start < 0):
            _fail('Invalid image timestamp')
        if end is not None:
            _fail('Image evidence must not declare an end time')
    return path, {'source_relpath': rel, 'kind': kind, 'start_s': start, 'end_s': end}


def build_media_evidence_bundle(job_dir: str | Path, *, request_id: str, stage: str,
                                question: str, items: list[dict],
                                max_total_bytes: int = DEFAULT_MAX_BYTES) -> dict:
    """Zip EXISTING small clips/images in JOB_DIR, with checksums and a question.

    Does not cut source clips. Refuses overwrites; callers produce a NEW request_id
    for each revision to preserve append-only checkpoint lineage.
    """
    root = Path(job_dir).resolve(strict=True)
    if not root.is_dir() or not root.is_absolute():
        _fail('JOB_DIR must be an existing absolute directory')
    if not isinstance(request_id, str) or not NAME.fullmatch(request_id):
        _fail('Invalid request ID')
    if stage not in VALID_STAGE:
        _fail('Unknown REVIEW_PHIM stage')
    if not isinstance(question, str) or not question.strip() or len(question) > 1000:
        _fail('Question must describe the exact need for real inspection')
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_FILES:
        _fail('Only 1-6 small evidence items are supported per ZIP')
    if type(max_total_bytes) is not int or not 1 <= max_total_bytes <= 500 * 1024 * 1024:
        _fail('Invalid explicit upload size budget')
    sources = []
    used = set()
    total = 0
    for i, item in enumerate(items, 1):
        path, meta = _validate_item(item, root)
        if meta['source_relpath'] in used:
            _fail('Duplicate source item')
        used.add(meta['source_relpath'])
        size = path.stat().st_size
        if size <= 0:
            _fail('Empty media is not valid evidence')
        total += size
        if total > max_total_bytes:
            _fail('Evidence exceeds upload budget; recut/recompress into smaller clips')
        meta.update({'bytes': size, 'sha256': sha256_file(path),
                     'zip_member': f'media/{i:02d}_{path.name}',
                     'inspected_by_chatgpt': False})
        sources.append((path, meta))
    for ancestor in (root / 'analysis', root / 'analysis' / 'media_for_chat'):
        if ancestor.is_symlink() or (ancestor.exists() and not ancestor.resolve().is_relative_to(root)):
            _fail('Output path escapes or uses a symlink/reparse point')
    output_dir = root / 'analysis' / 'media_for_chat' / request_id
    if output_dir.exists():
        _fail('Request exists; never overwrite history; choose a new request_id')
    output_dir.mkdir(parents=True, exist_ok=False)
    zip_path = output_dir / f'REVIEW_PHIM_{stage}_{request_id}_MEDIA.zip'
    manifest = {'schema_version': SCHEMA, 'request_id': request_id, 'stage': stage,
                'question_for_chatgpt': question.strip(),
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'delivery_status': 'ZIP_READY_NEEDS_TRANSFER',
                'actual_visual_inspection': False, 'actual_audio_listening': False,
                'files': [meta for _, meta in sources]}
    manifest_path = output_dir / 'manifest.json'
    try:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        with zipfile.ZipFile(zip_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=False) as z:
            z.write(manifest_path, arcname='manifest.json')
            for path, meta in sources:
                # Revalidate input bytes after writing before accepting ZIP (source is read-only).
                if sha256_file(path) != meta['sha256']:
                    _fail('Input changed during preparation')
                z.write(path, arcname=meta['zip_member'])
        digest = sha256_file(zip_path)
        verify_received_bundle(zip_path, expected_sha256=digest)
    except Exception:
        # Never remove a previously valid request; this directory was created here.
        if zip_path.exists():
            zip_path.unlink()
        if manifest_path.exists():
            manifest_path.unlink()
        try:
            output_dir.rmdir()
        except OSError:
            pass
        raise
    return {'status': 'ZIP_READY_NEEDS_TRANSFER', 'zip_path': str(zip_path),
            'zip_sha256': digest, 'manifest_path': str(manifest_path),
            'file_count': len(sources), 'download_url': None}


def verify_received_bundle(zip_path: str | Path, *, expected_sha256: str) -> dict:
    """Verify physical ZIP bytes; NEVER attest to image/video/audio perception."""
    zip_path = Path(zip_path)
    if not HEX64.fullmatch(expected_sha256) or sha256_file(zip_path) != expected_sha256:
        _fail('ZIP hash differs from expected file')
    if zip_path.stat().st_size > 500 * 1024 * 1024:
        _fail('Oversized uploaded ZIP')
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            infos = z.infolist()
            names = [i.filename for i in infos]
            if not infos or names[0] != 'manifest.json' or len(names) > MAX_FILES+1 or len(set(names)) != len(names):
                _fail('Missing manifest or invalid member count')
            for i in infos:
                p = PurePosixPath(i.filename)
                if p.is_absolute() or any(t in ('.','..') for t in p.parts) or '\\' in i.filename or ':' in i.filename:
                    _fail('Unsafe archive path')
                if stat.S_IFMT(i.external_attr >> 16) == stat.S_IFLNK:
                    _fail('Symlinks are forbidden in evidence ZIP')
            if sum(i.file_size for i in infos) > 500 * 1024 * 1024:
                _fail('Uncompressed ZIP exceeds safety limit')
            manifest = json.loads(z.read('manifest.json'))
            if manifest.get('schema_version') != SCHEMA or not isinstance(manifest.get('files'), list):
                _fail('Unknown manifest schema')
            files = manifest['files']
            if len(files) != len(infos)-1 or not 1 <= len(files) <= MAX_FILES:
                _fail('Manifest/member mismatch')
            for entry in files:
                path = entry.get('zip_member')
                if not isinstance(path, str) or not path.startswith('media/') or path not in names:
                    _fail('Manifest media member not in ZIP')
                blob = z.read(path)
                if len(blob) != entry.get('bytes') or _digest_bytes(blob) != entry.get('sha256'):
                    _fail('Tampered media member')
            if set(names) != {'manifest.json', *(f['zip_member'] for f in files)}:
                _fail('Undeclared archive members')
            return {'status': 'RECEIVED_NOT_INSPECTED', 'request_id': manifest.get('request_id'),
                    'stage': manifest.get('stage'), 'file_count': len(files),
                    'video_seen': False, 'audio_heard': False,
                    'media_members': [f['zip_member'] for f in files]}
    except (zipfile.BadZipFile, KeyError, UnicodeDecodeError, TypeError, json.JSONDecodeError) as exc:
        raise MediaEvidenceError(f'Invalid evidence archive: {exc}') from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    cmds = parser.add_subparsers(dest='command', required=True)
    build = cmds.add_parser('build')
    build.add_argument('--job-dir', required=True)
    build.add_argument('--request-id', required=True)
    build.add_argument('--stage', required=True)
    build.add_argument('--question', required=True)
    build.add_argument('--items-json', required=True, help='JSON file inside approved JOB_DIR listing ready media')
    build.add_argument('--max-bytes', type=int, default=DEFAULT_MAX_BYTES)
    verify = cmds.add_parser('verify')
    verify.add_argument('--zip', required=True)
    verify.add_argument('--sha256', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            root = Path(args.job_dir).resolve(strict=True)
            p, _ = _safe_source(root, str(Path(args.items_json).resolve(strict=True).relative_to(root)).replace('\\', '/'))
            items = json.loads(p.read_text(encoding='utf-8'))
            result = build_media_evidence_bundle(root,request_id=args.request_id,stage=args.stage,question=args.question,items=items,max_total_bytes=args.max_bytes)
        else:
            result = verify_received_bundle(args.zip,expected_sha256=args.sha256)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (MediaEvidenceError, FileNotFoundError, ValueError) as e:
        parser.exit(2, f'ERROR: {e}\n')


if __name__ == '__main__':
    main()
