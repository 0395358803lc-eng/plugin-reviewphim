"""Offline G05 narration-only lint / hard gate (Python standard library).

Only inspect explicitly provided text. Never fetch a film, translate, edit user
files, update a QC checkpoint or grant any downstream stage permission.
Narrative semantic accuracy still requires source/evidence review by ChatGPT.
"""
from __future__ import annotations

import re
from typing import Any

# Audience-facing prose must be diegetic: characters, decisions, events, causes,
# reactions, consequences. These patterns catch *workflow leakage*, not film
# names or the in-film use of ordinary terms such as "bằng chứng" or "nguồn".
_RULES = {
    "technical_source": (
        r"\btranscript\b", r"\b(?:asr|timecode|segment(?:_id)?|subtitle|subtitles)\b",
        r"\bbản\s+(?:dịch|ghi(?:\s+âm|\s+chữ)?)\b",
        r"\b(?:đoạn|phần|lời)\s+thoại\s+(?:đã\s+)?được\s+dịch\b",
        r"\b(?:được\s+dịch|chưa\s+nghe\s+xác\s+minh|chưa\s+được\s+nghe)\b",
        r"\b(?:theo|trong|qua)\s+(?:phần|bản|các\s+đoạn|những\s+đoạn)\s+thoại\b",
        r"\b(?:theo|trong)\s+(?:phần\s+)?nội\s+dung\s+(?:cuộc|đoạn|trao\s+đổi|đối\s+chất)\b",
        r"\b(?:bản\s+ghi|được\s+ghi\s+lại)\b",
        r"\b(?:lời\s+thoại|nội\s+dung)\s+trong\s+(?:transcript|bản\s+dịch)\b",
    ),
    "visual_inspection": (
        r"\bkhung\s+(?:hình|ảnh)\b", r"\b(?:chuỗi|loạt|các\s+chuỗi)\s+(?:hình|ảnh)\b",
        r"\b(?:các|những)\s+(?:hình\s+ảnh|khung\s+ảnh)\s+(?:liên\s+tiếp|tiếp\s+theo)\b",
        r"\b(?:trên|trong)\s+hình\b", r"\bhình\s+ảnh\s+(?:cho\s+thấy|tiếp\s+theo|được\s+kiểm\s+tra)\b",
        r"\b(?:các|những)\s+hình\s+ảnh\s+(?:cho\s+thấy|đã\s+xem|đã\s+kiểm\s+tra)\b",
        r"\b(?:cảnh\s+quay|góc\s+quay|góc\s+cắt|máy\s+quay|cận\s+cảnh\s+cho\s+thấy)\b",
        r"\b(?:được\s+nhìn\s+thấy|đã\s+xem|được\s+kiểm\s+tra)\b",
        r"\b(?:từ|qua)\s+(?:ảnh|những\s+ảnh|các\s+ảnh|hình\s+ảnh)\s+(?:được\s+kiểm\s+tra|lấy\s+mẫu|đã\s+xem)\b",
    ),
    "production_process": (
        r"\b(?:chatgpt|plugin|workflow|work[_ -]?package|qc|q0[1-9]|g0[1-9]|g1[0-5]|tts|ffmpeg)\b",
        r"\b(?:kịch\s+bản|bản\s+review|đoạn\s+review|lời\s+review)\b",
        r"\b(?:chưa|đã|cần)\s+(?:được\s+)?(?:xác\s+minh|đối\s+chiếu|kiểm\s+tra)\b",
        r"\b(?:không\s+đủ\s+(?:bằng\s+chứng|căn\s+cứ)|không\s+(?:thể|được)\s+khẳng\s+định)\b",
        r"\b(?:kịch\s+bản|bộ\s+phim)\s+(?:không\s+khẳng\s+định|cho\s+thấy|đang\s+nói|đặt|kết\s+thúc)\b",
        r"\b(?:theo\s+chứng\s+cứ|nguồn\s+chứng\s+cứ|chứng\s+cứ\s+hình\s+ảnh)\b",
        r"\b(?:phim\s+cho\s+thấy|bộ\s+phim\s+cho\s+thấy|người\s+xem|khán\s+giả)\b",
    ),
}
_COMPILED = [(category, re.compile(pattern, re.IGNORECASE | re.UNICODE))
             for category, patterns in _RULES.items() for pattern in patterns]


def audit_narration(text: str) -> dict[str, Any]:
    """Audit viewer-facing script/TTS only; return offset/line for human repair."""
    if not isinstance(text, str):
        raise TypeError("narration must be a string")
    issues: list[dict[str, Any]] = []
    for category, regex in _COMPILED:
        for match in regex.finditer(text):
            offset = match.start()
            issues.append({"category": category, "term": match.group(0),
                           "start": offset, "end": match.end(),
                           "line": text.count("\n", 0, offset) + 1})
    issues.sort(key=lambda item: (item["start"], item["category"], item["end"]))
    return {"passed": bool(text.strip()) and not issues,
            "issue_count": len(issues), "issues": issues,
            "public_narration_only": True}


def q05_narrative_gate(review_text: str, tts_text: str,
                       *, evidence_map: object | None = None) -> dict[str, Any]:
    """Hard-block Q05 public text leakage; evidence metadata stays outside scope.

    This check alone cannot certify story accuracy or approve G05_SCRIPT.
    """
    review = audit_narration(review_text)
    tts = audit_narration(tts_text)
    problems: list[str] = []
    if not review["passed"]:
        problems.append("REVIEW_NOT_AUDIENCE_ONLY")
    if not tts["passed"]:
        problems.append("TTS_NOT_AUDIENCE_ONLY")
    if review_text != tts_text:
        problems.append("REVIEW_TTS_TEXT_DIVERGENCE")
    return {"status": "PASS" if not problems else "BLOCKED",
            "Q05_NARRATIVE_ONLY": "PASS" if not problems else "BLOCKED",
            "review_audit": review, "tts_audit": tts,
            "problems": problems,"evidence_map_is_a_separate_internal_artifact": True,
            "G05_SCRIPT_approved": False, "auto_start_G06": False}
