"""REVIEW_PHIM v1.3.19: offline metadata schema/QC oracle, not a YouTube publisher."""
from __future__ import annotations
import hashlib
from typing import Any


def title_digest(title: str) -> str:
    return hashlib.sha256(title.strip().encode('utf-8')).hexdigest()


def validate_metadata(data: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    titles = data.get('candidate_titles', [])
    if not (isinstance(titles,list) and 3 <= len(titles) <= 5 and
            all(isinstance(t,str) and t == t.strip() and 0 < len(t) <= 100 for t in titles) and
            len(set(titles)) == len(titles)):
        issues.append('INVALID_CANDIDATES')
    selected = data.get('title_selected')
    if not isinstance(selected,str) or selected not in titles:
        issues.append('TITLE_NOT_CANDIDATE')
    desc = data.get('description')
    if not isinstance(desc,str) or not desc.strip():
        issues.append('DESCRIPTION_MISSING')
    return {'ready':not issues, 'issues':issues,
            'title_sha256':title_digest(selected) if isinstance(selected,str) and selected else None}


def approved_title(title: str, approval: dict[str,Any]) -> bool:
    return bool(title and isinstance(approval,dict) and
        approval.get('gate') == 'G11A_METADATA' and
        isinstance(approval.get('approval_ref'),str) and approval['approval_ref'].strip() and
        approval.get('title_sha256') == title_digest(title))


if __name__ == '__main__':
    import argparse,json
    p=argparse.ArgumentParser(description='Offline G11A QC: validates shape only; human approval and source truths remain external')
    p.add_argument('metadata_json')
    args=p.parse_args()
    with open(args.metadata_json,encoding='utf-8') as f:
        result=validate_metadata(json.load(f))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['ready'] else 1)
