"""Offline structural checks for REVIEW_PHIM v1.3.19.

These checks DO NOT create an image, inspect its content visually, upload files,
or render video. An agent must obtain actual visual QC evidence and user approval.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import struct
from typing import Any


def title_digest(title: str) -> str:
    return hashlib.sha256(title.strip().encode('utf-8')).hexdigest()


def _png_dims(payload: bytes) -> tuple[int,int] | None:
    if payload[:8] == b'\x89PNG\r\n\x1a\n' and len(payload) >= 24 and payload[12:16] == b'IHDR':
        return struct.unpack('>II',payload[16:24])
    return None


def _jpeg_dims(payload: bytes) -> tuple[int,int] | None:
    if not payload.startswith(b'\xff\xd8'):
        return None
    i=2
    while i+4<len(payload):
        if payload[i]!=0xff:
            i+=1; continue
        marker=payload[i+1];i+=2
        if marker in (0xd8,0xd9):continue
        if marker==0xda:break
        if i+2>len(payload):break
        length=int.from_bytes(payload[i:i+2],'big')
        if length<2 or i+length>len(payload):break
        if marker in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf) and length>=7:
            return int.from_bytes(payload[i+5:i+7],'big'),int.from_bytes(payload[i+3:i+5],'big')
        i+=length
    return None


def validate_thumbnail(image_path: str | Path,*, title: str, manifest:dict[str,Any],approval:dict[str,Any]) -> dict[str,Any]:
    issues:list[str]=[]
    path=Path(image_path)
    if not path.is_file():
        issues.append('IMAGE_MISSING')
    else:
        raw=path.read_bytes()
        dimensions=_png_dims(raw) or _jpeg_dims(raw)
        if dimensions is None or dimensions[0]<640 or dimensions[1]<1 or abs(dimensions[0]/dimensions[1]-16/9)>.015:
            issues.append('IMAGE_GEOMETRY_INVALID')
        if manifest.get('image_sha256') != hashlib.sha256(raw).hexdigest():
            issues.append('IMAGE_HASH_MISMATCH')
        if approval.get('image_sha256') != hashlib.sha256(raw).hexdigest():
            issues.append('IMAGE_NOT_APPROVED')
    if manifest.get('title') != title or manifest.get('title_sha256') != title_digest(title):
        issues.append('TITLE_HASH_MISMATCH')
    if not (manifest.get('visual_inspected') is True and manifest.get('visual_evidence')):
        issues.append('VISUAL_NOT_VERIFIED')
    if not (approval.get('gate') == 'G11B_THUMBNAIL' and isinstance(approval.get('approval_ref'),str) and approval['approval_ref'].strip()):
        issues.append('THUMBNAIL_NOT_APPROVED')
    return {'ready':not issues,'issues':issues}


def validate_intro_timing(info:dict[str,Any]) -> dict[str,Any]:
    issues:list[str]=[]
    fpsn=info.get('fps_num');fpsd=info.get('fps_den')
    frames=info.get('intro_frames'); actual=info.get('intro_actual_duration_s')
    if (not isinstance(fpsn,int) or not isinstance(fpsd,int) or fpsn<=0 or fpsd<=0 or
        not isinstance(frames,int) or frames<=0 or not isinstance(actual,(float,int))):
        issues.append('INTRO_TIMING_INVALID')
        return {'ready':False,'issues':issues}
    fps=fpsn/fpsd
    tolerance=(1/fps)+.0001
    if abs(actual-2.0)>tolerance or abs(frames/fps-2.)>tolerance:
        issues.append('INTRO_NOT_TWO_SECONDS')
    if not isinstance(info.get('narration_start_frame'),int) or info['narration_start_frame']<frames:
        issues.append('VOICE_START_BEFORE_INTRO_END')
    if info.get('intro_visual_inspected') is not True or not info.get('visual_evidence'):
        issues.append('INTRO_VISUAL_NOT_VERIFIED')
    return {'ready':not issues,'issues':issues}
