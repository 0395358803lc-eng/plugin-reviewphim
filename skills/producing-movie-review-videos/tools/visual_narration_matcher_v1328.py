#!/usr/bin/env python3
"""REVIEW_PHIM G08 evidence-first scene retrieval and G09 placement suggestions.

Standard library only. Does not decode video, execute remote tools, translate text,
run CLIP/Qwen-VL, listen to WAV, or assert that an indexed shot was visually seen.
Call from an authorized G08 executor against previously generated G04/G06 data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

_VISUAL_VERIFICATIONS = {'VISUAL_ONLY_VERIFIED', 'VISUAL_AND_DIALOGUE_VERIFIED'}
_STOPWORDS = frozenset('anh chi co va la cua da dang trong voi khi mot hai ba den de luc nay do duoc cho the vao'.split())


def _words(value: Any) -> set[str]:
    s = unicodedata.normalize('NFD', str(value or '').casefold())
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return {w for w in re.findall(r'[a-z0-9]+', s) if len(w) > 1 and w not in _STOPWORDS}


def _items(v: Any) -> list[Any]:
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple, set)) else [v]


def _ids(v: Any) -> set[str]:
    return {str(x).strip().casefold() for x in _items(v) if str(x).strip()}


def _overlap(a: Any, b: Any) -> float:
    aa, bb = _words(a), _words(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / max(1, len(aa | bb))


def _valid_time(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _unique(rows: list[dict], key: str, label: str) -> None:
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError(f'invalid {label} identifier')
        if row[key] in seen:
            raise ValueError(f'duplicate {label} id: {row[key]}')
        seen.add(row[key])


def _event_indexes(events: list[dict]) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    by_id: dict[str, dict] = {}
    by_scene: dict[str, list[dict]] = {}
    for event in events:
        if not isinstance(event, dict) or not event.get('event_id'):
            raise ValueError('event without event_id')
        eid = str(event['event_id'])
        if eid in by_id:
            raise ValueError('duplicate event id: ' + eid)
        by_id[eid] = event
        for scene_id in _items(event.get('scene_ids')):
            by_scene.setdefault(str(scene_id), []).append(event)
    return by_id, by_scene


def _similarity(sims: dict, bid: str, sid: str) -> float:
    raw = sims.get(bid, {}).get(sid, 0) if isinstance(sims.get(bid, {}), dict) else 0
    if not _valid_time(raw) or raw < 0 or raw > 1:
        raise ValueError('semantic similarity must be within [0, 1]')
    return float(raw)


def _candidate(beat: dict, scene: dict, events_for_scene: list[dict], duration: float,
               similarity: float, reuse: int) -> dict:
    bid, sid = beat['beat_id'], scene['scene_id']
    reasons = []
    start, end = scene.get('src_in_s'), scene.get('src_out_s')
    if not (_valid_time(start) and _valid_time(end) and 0 <= start < end <= duration):
        reasons.append('INVALID_SOURCE_RANGE')
    bline, sline = str(beat.get('storyline') or '').casefold(), str(scene.get('storyline') or '').casefold()
    if bline and sline and bline != sline:
        reasons.append('STORYLINE_MISMATCH')
    actor = _ids(beat.get('actor') or beat.get('actor_ids'))
    actors_on_screen = _ids(scene.get('visible_actor_ids'))
    if actor and actors_on_screen and not actor.intersection(actors_on_screen):
        reasons.append('ACTOR_MISMATCH')
    if str(beat.get('action') or '').casefold() in _ids(scene.get('contradicted_actions')):
        reasons.append('ACTION_CONTRADICTION')
    if scene.get('source_kind', 'ORIGINAL_FILM') != 'ORIGINAL_FILM':
        reasons.append('UNAUTHORIZED_SOURCE_KIND')

    scene_events = _ids(scene.get('event_ids')) | _ids([e['event_id'] for e in events_for_scene])
    beat_events = _ids(beat.get('event_ids'))
    event_match = bool(scene_events & beat_events)
    actor_match = bool(actor and actors_on_screen and actor & actors_on_screen)
    action_text = ' '.join(str(v) for v in _items(scene.get('visible_actions')) +
                           [e.get('action', '') for e in events_for_scene])
    action_overlap = _overlap(beat.get('action'), action_text)
    semantic_overlap = max(_overlap(beat.get('narration_text'), scene.get('visual_description')),
                           _overlap(beat.get('visual_intent'), scene.get('visual_description')))
    visual_purpose = str(scene.get('visual_purpose') or '').upper()
    meaningful = (event_match or (actor_match and (action_overlap > 0 or semantic_overlap > 0
                   or visual_purpose in {'REACTION', 'CONSEQUENCE', 'CONTEXT', 'ESTABLISH'})))
    if not meaningful and not reasons:
        reasons.append('NO_SEMANTIC_ANCHOR')

    visual_event_verified = any(str(e.get('verification') or '') in _VISUAL_VERIFICATIONS
                                for e in events_for_scene if (not beat_events or e['event_id'].casefold() in beat_events))
    observed = scene.get('scene_status') == 'VISUALLY_REVIEWED'
    evidence_refs = [str(x) for x in _items(scene.get('motion_clips')) if x]
    evidence_refs.extend(str(x.get('file_path')) for x in _items(scene.get('frames'))
                         if isinstance(x, dict) and x.get('file_path'))
    has_motion_proof = scene.get('motion_verification') == 'VERIFIED'
    claims_motion = bool(beat.get('action') and (action_overlap > 0 or event_match))
    fully_verified = observed and visual_event_verified and bool(evidence_refs) and (not claims_motion or has_motion_proof)
    score = round(52 * int(event_match) + 22 * int(actor_match) +
                  20 * action_overlap + 8 * semantic_overlap + 5 * similarity +
                  6 * int(bline and bline == sline) - 48 * reuse -
                  4 * int(bool(scene.get('quality_flags'))), 4)
    return {
        'shot_id': 'SHOT-' + bid + '-' + sid, 'scene_id': sid, 'beat_id': bid,
        'src_in_s': start, 'src_out_s': end, 'source_scene_id': sid,
        'event_ids': sorted(scene_events), 'score': score,
        'semantic_similarity': similarity, 'match_status': ('REJECTED' if reasons else
            ('VERIFIED_VISUAL' if fully_verified else 'CANDIDATE')),
        'hard_reject_reasons': reasons, 'actor_match': actor_match,
        'action_overlap': round(action_overlap, 4), 'event_match': event_match,
        'evidence_refs': evidence_refs, 'reuse_count_before': reuse,
        'visual_purpose': visual_purpose or 'UNKNOWN',
        'source_kind': scene.get('source_kind', 'ORIGINAL_FILM'),
    }


def match_beats(beats: list[dict], scenes: list[dict], events: list[dict],
                *, source_duration_s: float, similarities: dict | None = None,
                max_candidates: int = 5) -> dict[str, list[dict]]:
    """Return ranked candidates, decisions and nonblocking content warnings.

    This ranks *available* metadata, not raw frames. Optional similarities are
    precomputed authorized-model hints (0..1), never proof of actor or motion.
    """
    if not _valid_time(source_duration_s) or source_duration_s <= 0:
        raise ValueError('invalid source duration')
    if not isinstance(beats, list) or not isinstance(scenes, list) or not isinstance(events, list):
        raise ValueError('beats/scenes/events must be lists')
    if not isinstance(max_candidates, int) or max_candidates < 1:
        raise ValueError('invalid max_candidates')
    _unique(beats, 'beat_id', 'beat')
    _unique(scenes, 'scene_id', 'scene')
    _, by_scene = _event_indexes(events)
    similarities = similarities or {}
    if not isinstance(similarities, dict):
        raise ValueError('similarities must be an object')
    used: Counter[str] = Counter()
    candidates: list[dict] = []
    decisions: list[dict] = []
    warnings: list[dict] = []
    for beat in beats:
        bid = beat['beat_id']
        ranked = [_candidate(beat, scene, by_scene.get(scene['scene_id'], []),
                             float(source_duration_s), _similarity(similarities,bid,scene['scene_id']),
                             used[scene['scene_id']]) for scene in scenes]
        ranked.sort(key=lambda x: (x['match_status'] == 'REJECTED', -x['score'], x['scene_id']))
        valid = [c for c in ranked if c['match_status'] != 'REJECTED']
        selected = valid[0] if valid else None
        if selected:
            used[selected['scene_id']] += 1
        top = valid[:max_candidates]
        candidates.extend(top + [c for c in ranked if c['match_status'] == 'REJECTED'])
        selected_id = selected['shot_id'] if selected else None
        status = selected['match_status'] if selected else 'NO_MATCH'
        decisions.append({
            'beat_id':bid, 'narration_text':beat.get('narration_text',''),
            'selected_shot_id': selected_id, 'selected_scene_id': selected['scene_id'] if selected else None,
            'match_status': status, 'selected_rank': 1 if selected else None,
            'alternate_shot_ids': [c['shot_id'] for c in valid[1:max_candidates]],
            'rejected_shot_ids': [c['shot_id'] for c in ranked if c['match_status']=='REJECTED'],
            'source_in_s':selected['src_in_s'] if selected else None,
            'source_out_s':selected['src_out_s'] if selected else None,
            'selection_reason': ('evidence-first candidate: event/actor/action/intent and continuity; '
                                 + ('visual support recorded' if status=='VERIFIED_VISUAL'
                                    else 'requires visual confirmation')) if selected else 'no justified film-source shot',
            'decision_by_chatgpt': 'PENDING',
            'evidence_refs': selected['evidence_refs'] if selected else [],
        })
        if not selected:
            warnings.append({'beat_id':bid,'code':'NO_VISUAL_MATCH','severity':'WARNING',
                             'detail':'No semantically defensible original-film candidate; do not use unrelated filler'})
        elif status != 'VERIFIED_VISUAL':
            warnings.append({'beat_id':bid,'code':'UNVERIFIED_VISUAL','severity':'WARNING',
                             'detail':'Candidate selected for draft only; embedding/metadata does not prove visual action'})
        elif used[selected['scene_id']] > 1:
            warnings.append({'beat_id':bid,'code':'VISUAL_REUSE','severity':'WARNING',
                             'detail':'Repeated selected scene; check alternatives at final review'})
    return {'candidates': candidates, 'decisions': decisions, 'warnings': warnings}


def build_placement_suggestions(beats: list[dict], decisions: list[dict],
                                *, source_duration_s: float) -> dict[str, list[dict]]:
    """Plan source ranges against actual WAV-aligned beat anchors; never infer time."""
    if not _valid_time(source_duration_s) or source_duration_s <= 0:
        raise ValueError('invalid source duration')
    by_id = {d['beat_id']:d for d in decisions}
    placements: list[dict] = []
    warnings: list[dict] = []
    end_prev = 0.0
    for beat in beats:
        bid = beat['beat_id']
        d = by_id.get(bid)
        if not d:
            raise ValueError('missing beat decision: '+bid)
        t0,t1 = beat.get('voice_in_s'),beat.get('voice_out_s')
        valid_voice = _valid_time(t0) and _valid_time(t1) and 0 <= t0 < t1
        if ('voice_in_s' in beat or 'voice_out_s' in beat) and not valid_voice:
            raise ValueError('invalid supplied voice interval: '+bid)
        if valid_voice and t0 < end_prev - 1e-6:
            raise ValueError('overlapping voice beats: '+bid)
        if valid_voice:
            end_prev = t1
        s0,s1 = d.get('source_in_s'),d.get('source_out_s')
        source_valid = _valid_time(s0) and _valid_time(s1) and 0 <= s0 < s1 <= source_duration_s
        if d.get('selected_shot_id') is not None and not source_valid:
            raise ValueError('invalid selected source interval: '+bid)
        anchored_end = min(float(t1), float(t0)+(s1-s0)) if valid_voice and source_valid else None
        source_end = float(s0) + (anchored_end-float(t0)) if anchored_end is not None else s1 if source_valid else None
        item={
            'beat_id':bid, 'selected_shot_id':d.get('selected_shot_id'),
            'source_in_s': s0 if source_valid else None, 'source_out_s':source_end,
            'timeline_in_s': t0 if valid_voice else None,
            'timeline_out_s': anchored_end, 'voice_end_s':t1 if valid_voice else None,
            'anchor_provenance': 'VOICE_BEAT_TIMESTAMP' if valid_voice else 'UNKNOWN',
            'placement_status':('UNMATCHED' if d.get('selected_shot_id') is None else
                                'ANCHORED' if valid_voice else 'UNANCHORED'),
            'match_status':d.get('match_status'),
            'word_anchors':_validated_word_anchors(beat.get('word_timestamps'), t0, t1) if valid_voice else [],
        }
        if valid_voice and source_valid and anchored_end < t1 - 1e-6:
            warnings.append({'beat_id':bid,'code':'SHORT_VISUAL','severity':'WARNING',
                             'detail':'Clip shorter than voice beat; follow-on shot must cover remaining narration'})
        if not valid_voice:
            warnings.append({'beat_id':bid,'code':'VOICE_ANCHOR_MISSING','severity':'WARNING',
                             'detail':'No measured beat timestamps supplied; do not invent placement offsets'})
        placements.append(item)
    return {'placements': placements, 'warnings': warnings}


def _validated_word_anchors(words: Any, t0: float, t1: float) -> list[dict]:
    out=[]
    for word in _items(words):
        if not isinstance(word, dict):
            raise ValueError('invalid word timestamp')
        start, end = word.get('start_s'), word.get('end_s')
        if not (_valid_time(start) and _valid_time(end) and t0 <= start < end <= t1):
            raise ValueError('word timestamps outside voice beat')
        out.append({'text':str(word.get('text','')), 'start_s':start,'end_s':end,
                    'provenance':'MEASURED_WORD_ALIGNMENT'})
    return out


def _job_path(job: Path, rel: str) -> Path:
    if not isinstance(rel,str) or '\\' in rel or ':' in rel or not rel or rel.startswith('/'):
        raise ValueError('invalid relative job path')
    p=PurePosixPath(rel)
    if str(p)!=rel or any(x in {'..','.'} for x in p.parts):
        raise ValueError('unsafe relative job path')
    target=job.joinpath(*p.parts)
    if any(x.is_symlink() for x in (job,*job.parents,target,*target.parents)):
        raise ValueError('symlink path forbidden')
    if job.resolve() != target.resolve() and job.resolve() not in target.resolve().parents:
        raise ValueError('path escapes job')
    return target


def _json_data(job:Path,rel:str) -> Any:
    return json.loads(_job_path(job,rel).read_text(encoding='utf-8'))


def _atomic_new(dest:Path,contents:str) -> None:
    if dest.exists():
        raise FileExistsError('refusing to overwrite existing output: '+str(dest))
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x',encoding='utf-8',newline='') as f:
        f.write(contents)


def _run_cli() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--job-dir',required=True)
    p.add_argument('--source-duration',required=True,type=float)
    p.add_argument('--beats',default='beats/beats.json')
    p.add_argument('--scenes',default='analysis/scene_catalog.json')
    p.add_argument('--events',default='analysis/visual_events.json')
    p.add_argument('--similarities',default=None,help='Optional precomputed 0..1 similarities in JSON; does not invoke a model')
    args=p.parse_args()
    job=Path(args.job_dir).resolve(strict=True)
    if not job.is_dir():
        raise ValueError('job-dir must be directory')
    beats=_json_data(job,args.beats);scenes=_json_data(job,args.scenes);events=_json_data(job,args.events)
    sims=_json_data(job,args.similarities) if args.similarities else None
    matched=match_beats(beats,scenes,events,source_duration_s=args.source_duration,similarities=sims)
    timing=build_placement_suggestions(beats,matched['decisions'],source_duration_s=args.source_duration)
    paths=['shots/shot_candidates.json','shots/shot_selection_decisions.json',
           'shots/matching_warnings.json','shots/shot_map.csv','timeline/visual_placement_suggestions.json']
    dest=[_job_path(job,p) for p in paths]
    if any(x.exists() for x in dest):
        raise FileExistsError('one or more output files already exist; use approved fresh revision paths')
    pretty=lambda x: json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    _atomic_new(dest[0],pretty({'schema_version':'1.3.28','candidates':matched['candidates']}))
    _atomic_new(dest[1],pretty({'schema_version':'1.3.28','decisions':matched['decisions']}))
    _atomic_new(dest[2],pretty({'schema_version':'1.3.28','warnings':matched['warnings']+timing['warnings']}))
    import io
    stream=io.StringIO(newline='')
    keys=['beat_id','source_scene_id','src_in_s','src_out_s',
          'actor_evidence','action_evidence','transcript_evidence','visual_evidence','match_status','evidence',
          'shot_id','selected_rank','reuse_count','selection_reason','decision_by_chatgpt']
    writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader()
    for d in matched['decisions']:
        writer.writerow({'beat_id':d['beat_id'],'shot_id':d['selected_shot_id'] or '',
                         'source_scene_id':d['selected_scene_id'] or '',
                         'src_in_s':d['source_in_s'] if d['source_in_s'] is not None else '',
                         'src_out_s':d['source_out_s'] if d['source_out_s'] is not None else '',
                         'actor_evidence': next((str(b.get('actor') or '') for b in beats if b['beat_id']==d['beat_id']), ''),
                         'action_evidence': next((str(b.get('action') or '') for b in beats if b['beat_id']==d['beat_id']), ''),
                         'transcript_evidence': '',
                         'visual_evidence': json.dumps(d['evidence_refs'],ensure_ascii=False),
                         'evidence': json.dumps({'refs':d['evidence_refs'], 'status':d['match_status']},ensure_ascii=False),
                         'match_status':d['match_status'],'shot_id':d['selected_shot_id'] or '',
                         'selected_rank':d['selected_rank'] if d['selected_rank'] is not None else '',
                         'reuse_count': next((x['reuse_count_before'] for x in matched['candidates']
                                          if x['beat_id']==d['beat_id'] and x['shot_id']==d['selected_shot_id']),0),
                         'selection_reason':d['selection_reason'],
                         'decision_by_chatgpt':d['decision_by_chatgpt']})
    _atomic_new(dest[3],stream.getvalue())
    _atomic_new(dest[4],pretty({'schema_version':'1.3.28',**timing}))
    print(pretty({'stage':'G08','beat_count':len(beats),'matched_count':sum(d['selected_shot_id'] is not None for d in matched['decisions']),
                 'warning_count':len(matched['warnings'])+len(timing['warnings']), 'outputs':paths}).rstrip())


if __name__=='__main__':
    try: _run_cli()
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('visual-narration matching failed: '+str(exc),file=sys.stderr)
        sys.exit(2)
