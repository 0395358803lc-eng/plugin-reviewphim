"""REVIEW_PHIM v1.3.29: safe contract adaptation of v1325 for new packages only.

Keeps the original production/recovery ledger and legacy manual-copy behavior.
For opted-in NEW packages, G11B stores a real delivery manifest in JOB_DIR
while the image itself is delivered separately through ChatGPT for upload to
YouTube Studio. G12 renders a persistent upper-left watermark, not intro video.
No thumbnail bytes, watermark frames, or upload action are fabricated here.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import project_flow_v1325 as _core

MODE='DOWNLOAD_SEPARATELY_UPLOAD_IN_YOUTUBE_STUDIO'
_original_validate_plan=_core.validate_plan
_original_verify_thumbnail=_core.verify_thumbnail


def is_youtube_separate_mode(plan):
    return isinstance(plan,dict) and plan.get('production_config',{}).get('thumbnail_delivery')==MODE


def _digest(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def validate_plan(plan):
    result=_original_validate_plan(plan)
    if not is_youtube_separate_mode(plan):
        return result
    config=plan['production_config']; logo=config.get('logo_overlay')
    if config.get('thumbnail_embed_in_video') is not False or config.get('intro_card_enabled') is not False or config.get('g12_input_thumbnail') is not False:
        raise ValueError('thumbnail must be separate; intro and image embedding are forbidden')
    if not isinstance(logo,dict) or any(logo.get(k)!=v for k,v in {
        'enabled':True,'position':'top_left','start':'first_frame','end':'last_frame','mode':'persistent_watermark'}.items()):
        raise ValueError('logo overlay must cover first through last frame at top_left')
    stages=plan['allowed_stages']; outputs=plan['stage_outputs']; dependencies=plan.get('stage_dependencies',{})
    for stage in ('G11B','G12','G15'):
        if stage not in stages:
            continue
        names=outputs[stage]
        if stage=='G11B':
            if len(names)!=1 or not names[0].endswith('.json') or 'thumbnail' not in names[0].lower():
                raise ValueError('G11B requires one real thumbnail handoff manifest JSON, not an intro image')
        if stage=='G12':
            if not any(n.lower().endswith('.mp4') for n in names):
                raise ValueError('G12 must output a branded MP4')
            if any('intro' in n.lower() or 'thumbnail' in n.lower() for n in names):
                raise ValueError('G12 output must not be an intro or thumbnail')
            if 'G12' not in dependencies or 'G11' not in dependencies['G12'] or any(s in dependencies['G12'] for s in ('G11B','G11A')):
                raise ValueError('G12 requires explicit G11 dependency and must not depend on G11B thumbnail')
            if not plan.get('stage_inputs',{}).get('G12'):
                raise ValueError('G12 must bind a real logo asset as a hashed stage input')
            g12=plan.get('stage_config',{}).get('G12',{})
            if g12.get('logo_overlay') is not True or g12.get('intro_card_enabled') is not False:
                raise ValueError('G12 stage config must enable persistent logo and disable intro')
        if stage=='G15' and not any(n.lower().endswith('.json') for n in names):
            raise ValueError('G15 must deliver YouTube thumbnail download metadata in a JSON sidecar')
    return result


def verify_thumbnail(plan,evidence):
    if not is_youtube_separate_mode(plan):
        return _original_verify_thumbnail(plan,evidence)
    if not isinstance(evidence,dict):
        raise ValueError('thumbnail delivery evidence missing')
    rels=plan.get('stage_outputs',{}).get('G11B',[])
    if len(rels)!=1 or evidence.get('relative_path')!=rels[0]:
        raise ValueError('thumbnail delivery manifest outside approved output contract')
    path=(Path(plan['JOB_DIR'])/rels[0])
    root=Path(plan['JOB_DIR']).resolve(strict=True)
    resolved=path.resolve(strict=True)
    if root not in resolved.parents or path.is_symlink() or not path.is_file():
        raise ValueError('thumbnail delivery manifest path invalid')
    try:
        info=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,OSError,UnicodeError) as exc:
        raise ValueError('thumbnail delivery manifest not readable JSON') from exc
    if not isinstance(info,dict) or info.get('schema')!='youtube-thumbnail-handoff.v1' or info.get('delivery_mode')!=MODE or info.get('embed_in_video') is not False:
        raise ValueError('thumbnail delivery manifest schema or mode invalid')
    for k in ('title','title_sha256','image_sha256','generation_ref'):
        if info.get(k)!=evidence.get(k):
            raise ValueError('thumbnail delivery mismatch: '+k)
    if not isinstance(info.get('title'),str) or not info['title'].strip() or hashlib.sha256(info['title'].strip().encode()).hexdigest()!=info.get('title_sha256'):
        raise ValueError('thumbnail title hash mismatch')
    if not _digest(info.get('image_sha256')) or info.get('format') not in ('png','jpg','jpeg'):
        raise ValueError('thumbnail image digest/format invalid')
    if not isinstance(info.get('width'),int) or not isinstance(info.get('height'),int) or info['width']<640 or info['height']<=0 or abs(info['width']/info['height']-16/9)>.015:
        raise ValueError('thumbnail image geometry must be 16:9')
    if any(not isinstance(info.get(k),str) or not info[k].strip() for k in ('generation_ref','download_ref')) or info.get('user_can_download') is not True or info.get('image_inspected') is not True:
        raise ValueError('thumbnail must be genuinely generated, inspected, and available for download')
    # IMPORTANT: manifest checks cannot themselves inspect ChatGPT-hosted image
    # bytes or prove that a remote image exists. The executor/host must produce
    # the actual image and user-facing verified download reference separately.
    return {'status':'DELIVERABLE_REFERENCED','relative_path':rels[0],
            'image_sha256':info['image_sha256'], 'title_sha256':info['title_sha256'],
            'download_ref':info['download_ref'], 'requires_user_copy':False}


_core.validate_plan=validate_plan
_core.verify_thumbnail=verify_thumbnail
for _name in dir(_core):
    if not _name.startswith('_') and _name not in ('validate_plan','verify_thumbnail'):
        globals()[_name]=getattr(_core,_name)
