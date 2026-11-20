"""Lightweight G02 transcript text QC; offline only, no ASR/audio/movie reads.

Does not certify the meaning of ASR words or grant permission for later stages.
Kept raw model output must be saved separately by an approved work package.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

# UTF-8 plain text has no intrinsic font family; check Unicode and layout instead.
_BAD = ('\ufffd', '\ufffe', '\uffff')


def normalize_visible_text(text: str) -> tuple[str, list[str]]:
    """Normalize only safe typography. Never infer a word/speaker/plot fact."""
    if not isinstance(text, str):
        raise TypeError('text must be str')
    edits: list[str] = []
    result = text
    normalized = unicodedata.normalize('NFC', result.replace('\ufeff', ''))
    if normalized != result:
        edits.append('UNICODE_NFC_OR_BOM')
    result = normalized
    ws = re.sub(r'\s+', ' ', result).strip()
    if ws != result:
        edits.append('WHITESPACE')
    result = ws
    punct = re.sub(r'\s+([,.;:!?])', r'\1', result)
    punct = re.sub(r'([,;:!?])(?!\s|$|["\u2019\u201d)])(?=[A-Za-z\u00c0-\u024f])', r'\1 ', punct)
    if punct != result:
        edits.append('PUNCTUATION_SPACING')
    result = punct
    return result, edits


def process_transcript_rows(
    rows: list[dict[str, Any]], *, source_duration_s: float,
    source_hash_verified: bool, full_audio_processed: bool,
    model_transcribe_completed: bool, asr_warning_count: int = 0,
) -> dict[str, Any]:
    """Produce a copy suitable for review and the Q02 text-only gate.

    Uncertain ASR words and repetitions are recorded as nonblocking warnings.
    Invalid timecodes are excluded from the clean *copy*, never rewritten in raw.
    Unsafe Unicode corruption requires correction by evidence, not guessing.
    """
    if not isinstance(rows, list):
        raise TypeError('rows must be list')
    if not isinstance(source_duration_s, (float, int)) or not math.isfinite(source_duration_s) or source_duration_s <= 0:
        raise ValueError('source_duration_s must be positive finite')
    if not isinstance(asr_warning_count, int) or asr_warning_count < 0:
        raise ValueError('asr_warning_count must be a nonnegative integer')
    seen: set[str] = set()
    clean: list[dict[str, Any]] = []
    edits: list[dict[str, Any]] = []
    invalid_timing: list[str] = []
    unresolved_text: list[str] = []
    invalid_structure: list[str] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            invalid_structure.append(f'ROW_{index}');continue
        sid = row.get('segment_id')
        st = row.get('start'); et = row.get('end')
        if (not isinstance(sid, str) or not sid or sid in seen or
            not isinstance(st, (float, int)) or not isinstance(et, (float, int)) or
            not math.isfinite(st) or not math.isfinite(et)):
            invalid_structure.append(sid if isinstance(sid, str) else f'ROW_{index}')
            continue
        seen.add(sid)
        if not(0 <= st < et <= source_duration_s + 0.25):
            invalid_timing.append(sid)
            continue
        original = row.get('text_original', row.get('text_raw_asr'))
        if not isinstance(original, str) or not original.strip():
            unresolved_text.append(sid)
            continue
        fixed, changes = normalize_visible_text(original)
        if (not fixed or any(bad in fixed for bad in _BAD) or
            any(unicodedata.category(ch) == 'Cc' for ch in fixed)):
            unresolved_text.append(sid)
            continue
        copy = dict(row)
        copy['text_original'] = fixed
        copy['text_qc_status'] = 'FORMAT_OK'
        copy['text_qc_changes'] = changes
        copy['heard_verified'] = False
        clean.append(copy)
        if changes:
            edits.append({'segment_id':sid, 'changes':changes, 'previous':original, 'corrected':fixed})
    technical_complete = (source_hash_verified is True and full_audio_processed is True
        and model_transcribe_completed is True and bool(rows))
    gate = ('BLOCKED' if not technical_complete or invalid_structure else
            'NOT_VERIFIED' if unresolved_text else 'PASS')
    return {
        'task_id':'G02.ASR.FULL',
        'QC_POLICY':'Q02_TEXT_PASS',
        'Q02_GATE_STATUS':gate,
        'text_qc':'PASS' if gate=='PASS' else 'NOT_VERIFIED',
        'clean_rows':clean,
        'clean_row_count':len(clean),
        'format_edit_count':len(edits),
        'format_edits':edits,
        'excluded_invalid_timing_ids':invalid_timing,
        'unresolved_text_error_ids':unresolved_text,
        'invalid_structural_rows':invalid_structure,
        'asr_warnings_recorded':asr_warning_count,
        'asr_warnings_are_q02_blockers':False,
        'raw_rows_preserved':True,
        'spoken_words_verified':False,
        'G03_authorized':False,
        'G04_authorized':False,
        'next_action':'REQUEST_SEPARATE_G03_STAGE_APPROVAL' if gate=='PASS' else 'FIX_VISIBLE_TEXT_OR_SOURCE_COMPLETENESS',
    }
