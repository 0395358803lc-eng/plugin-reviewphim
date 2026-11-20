"""REVIEW_PHIM v1.3.24: inspect a thumbnail the USER placed in the approved JOB_DIR.

NO image generation, no file transfer, no folder creation, no Remote Desktop access.
This offline helper checks path, source-consent metadata, format, geometry and SHA-256.
It DOES NOT perform FFmpeg decoding, visual inspection, or grant Q11B automatically.
The caller must verify the actual remote path/file identity and the human message.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
from typing import Any

ALLOWED_FILENAMES = {'youtube_thumbnail.png', 'youtube_thumbnail.jpg', 'youtube_thumbnail.jpeg'}
MAX_IMAGE_BYTES = 30 * 1024 * 1024


def title_digest(title: str) -> str:
    return hashlib.sha256(title.strip().encode('utf-8')).hexdigest()


def handoff_destination(job_dir: str | Path, image_extension: str = 'png') -> dict[str, Any]:
    """Get the one user-facing target path; no filesystem side effect."""
    if image_extension not in {'png', 'jpg', 'jpeg'}:
        raise ValueError('Only downloaded PNG/JPG files are accepted; never rename extensions')
    target=Path(job_dir)/'assets'/('youtube_thumbnail.'+image_extension)
    return {'relative_path':'assets/'+target.name, 'absolute_path':str(target),
            'requires_user_copy':True, 'automatic_transfer_required':False,
            'on_copy_reply':'ĐÃ CHÉP ẢNH VÀ DUYỆT G11B'}


def _png_dimensions(data: bytes) -> tuple[int,int] | None:
    if not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data)<45:
        return None
    if data[12:16]!=b'IHDR' or int.from_bytes(data[8:12],'big')!=13:
        return None
    if b'IDAT' not in data or data[-12:-8]!=b'\x00\x00\x00\x00' or data[-8:-4]!=b'IEND':
        return None
    if data[24]!=8 or data[25] not in {2,6,0}:
        return None
    width,height=struct.unpack('>II',data[16:24])
    return width,height


def _jpg_dimensions(data: bytes) -> tuple[int,int] | None:
    if not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
        return None
    i=2
    while i+4<len(data):
        if data[i]!=255:
            i+=1;continue
        marker=data[i+1];i+=2
        if marker in (0xd8,0xd9):continue
        if marker==0xda:break
        length=int.from_bytes(data[i:i+2],'big')
        if length<2 or i+length>len(data):break
        if marker in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf) and length>=7:
            return int.from_bytes(data[i+5:i+7],'big'),int.from_bytes(data[i+3:i+5],'big')
        i+=length
    return None


def _unsafe_reparse(path: Path) -> bool:
    """Reject Windows junctions as well as symlinks where pathlib supports them."""
    return path.is_symlink() or bool(getattr(path, 'is_junction', lambda: False)())


def _reply(status: str, **more:Any) -> dict[str,Any]:
    return {'status':status, 'ready_for_q11b_qc':False, 'qc_pass_claimed':False, **more}


def verify_drop(job_dir: str | Path, *, title: str, approval: dict[str,Any],
                visual: dict[str,Any], image_name: str='youtube_thumbnail.png',
                expected_source_sha256: str | None = None, production_first: bool = False) -> dict[str,Any]:
    """Check a user-supplied remote file, with approval and honest provenance.

    A successful result is ONLY `FILE_ACCEPTED` for Q11B final visual/decode QC,
    not Q11B=PASS. If expected source digest is absent, no bit-for-bit match is claimed.
    """
    if image_name not in ALLOWED_FILENAMES:
        return _reply('BLOCKED_PATH')
    root=Path(job_dir)
    if _unsafe_reparse(root) or _unsafe_reparse(root/'assets'):
        return _reply('BLOCKED_PATH')
    image=root/'assets'/image_name
    if _unsafe_reparse(image):
        return _reply('BLOCKED_PATH')
    if not image.is_file():
        return _reply('WAITING_FOR_USER_IMAGE_PLACEMENT',expected_path=str(image))
    try:
        resolved_root=root.resolve(strict=True)
        resolved_image=image.resolve(strict=True)
        if resolved_image.parent != (resolved_root/'assets'):
            return _reply('BLOCKED_PATH')
        if image.stat().st_size <=0 or image.stat().st_size>MAX_IMAGE_BYTES:
            return _reply('BLOCKED_IMAGE_SIZE')
        payload=image.read_bytes()
    except (OSError, ValueError):
        return _reply('BLOCKED_PATH')
    suffix=image.suffix.lower()
    dims=_png_dimensions(payload) if suffix=='.png' else _jpg_dimensions(payload)
    if dims is None:
        return _reply('BLOCKED_IMAGE_FORMAT')
    w,h=dims
    if w<640 or h<=0 or abs(w/h-16/9)>.015:
        return _reply('BLOCKED_IMAGE_GEOMETRY')
    digest=hashlib.sha256(payload).hexdigest()
    if expected_source_sha256 is not None:
        if (not isinstance(expected_source_sha256,str) or len(expected_source_sha256)!=64 or
                any(ch not in '0123456789abcdef' for ch in expected_source_sha256) or
                digest!=expected_source_sha256):
            return _reply('BLOCKED_SOURCE_HASH')
    td=title_digest(title)
    if not isinstance(approval,dict) or not (
        approval.get('source')=='user_message' and approval.get('action')=='G11B_THUMBNAIL' and
        isinstance(approval.get('approval_ref'),str) and approval['approval_ref'].strip() and
        approval.get('title_sha256')==td and approval.get('user_confirmed_placement') is True and
        approval.get('user_selected_file')==image_name):
        return _reply('WAITING_FOR_HUMAN_APPROVAL')
    if not production_first:
        if not isinstance(visual,dict) or not (
            visual.get('generated_image_seen_by_chatgpt') is True and
            visual.get('text_checked_by_chatgpt') is True and
            isinstance(visual.get('source_image_evidence_ref'),str) and visual['source_image_evidence_ref'].strip()):
            return _reply('NOT_VERIFIED')
    # Explicit new mode: verify the actual user-supplied file, not subjective
    # thumbnail aesthetics. The one-time user placement/title binding remains.
    return _reply('FILE_ACCEPTED',ready_for_q11b_qc=not production_first,
                  relative_path='assets/'+image_name,absolute_path=str(image),
                  image_sha256=digest,image_width=w,image_height=h,
                  title_sha256=td,approval_ref=approval['approval_ref'],
                  image_identity=('SHA256_MATCH' if expected_source_sha256 else
                                  'USER_ATTESTED_NOT_BYTE_MATCHED'),
                  next_action=('Record artifact DONE and continue Production First; user reviews final video'
                               if production_first else
                               'Actual remote image decode/visual QC then record Q11B; never assume PASS'))
