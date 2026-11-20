"""Offline structure/gate checks for a *ChatGPT-researched* G05 web comparison.

This module NEVER fetches URLs, invokes a model, edits a review or certifies that
ChatGPT actually visited any webpage. Its input must first be independently
assembled from real web search results, film evidence and review paragraphs.
Only an explicitly approved G05 work package may execute it in a film workspace.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

_HASH = re.compile(r"[a-fA-F0-9]{64}\Z")
_ID = re.compile(r"(?:P-\d{4}|EV-\d{4})\Z")
_VALID_TYPES = {"MATCH", "MISSING_BEAT", "POTENTIAL_CONFLICT",
                "SOURCE_DISAGREEMENT", "NOT_COVERED"}
_VALID_EVIDENCE = {"G04_VERIFIED", "G04_UNVERIFIED", "WEB_ONLY", "NOT_APPLICABLE"}
_VALID_RESOLUTIONS = {"KEEP", "REVISED_G04_SUPPORTED", "OMITTED_UNVERIFIED",
                      "ESCALATE_G04", "NO_ACTION_SHORT_SYNOPSIS"}
_VALID_SOURCES = {"OFFICIAL_DISTRIBUTOR", "OFFICIAL_STUDIO", "FILM_CATALOG",
                  "EDITORIAL_REVIEW", "INDEPENDENT_PLOT"}


def _safe_url(value: Any) -> bool:
    if not isinstance(value, str) or any(x.isspace() for x in value):
        return False
    parsed = urlparse(value)
    return (parsed.scheme == "https" and bool(parsed.hostname) and
            parsed.username is None and parsed.password is None and
            parsed.hostname not in ("localhost", "127.0.0.1", "::1") and
            not parsed.fragment and len(value) <= 2048)


def _result(status: str, recommendation: str, *, sources: int = 0,
            reviewed_findings: int = 0, issues: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "Q05_WEB_STORY_CROSSCHECK": status,
        "recommendation": recommendation,
        "credible_independent_sources": sources,
        "findings_reviewed": reviewed_findings,
        "issues": issues or [],
        "verified_external_web_access_by_this_helper": False,
        "G05_SCRIPT_approved": False,
        "auto_start_G06": False,
        "auto_start_G07": False,
        "auto_start_G08": False,
    }


def evaluate_crosscheck(report: Mapping[str, Any]) -> dict[str, Any]:
    """Check submitted source/findings structure, conservative review decisions.

    `PASS` only means the *provided, genuinely retrieved evidence report* is
    internally consistent. Actual web provenance must be checked by ChatGPT,
    independently of this offline function. Never confuse this PASS with G05
    story acceptance or human G05_SCRIPT approval.
    """
    if not isinstance(report, Mapping):
        raise TypeError("report must be a mapping")
    bad = lambda problem: _result("BLOCKED", "REPAIR_INVALID_REPORT", issues=[problem])
    missing = lambda problem, n=0: _result("NOT_VERIFIED", "RESEARCH_MORE", sources=n,
                                           issues=[problem])

    if report.get("schema_version") != "g05-web-crosscheck.v1":
        return bad("SCHEMA_VERSION_MISSING")
    film = report.get("film_identity")
    if (not isinstance(film, Mapping) or not isinstance(film.get("title"), str) or
        not film["title"].strip() or type(film.get("year")) is not int or
        film["year"] < 1888 or film["year"] > 2100):
        return bad("FILM_IDENTITY_INVALID")
    if film.get("identity_checked") is not True:
        return missing("FILM_IDENTITY_NOT_RECONFIRMED")

    searched = report.get("search")
    if not isinstance(searched, Mapping):
        return missing("NO_WEB_SEARCH_RECORD")
    if (searched.get("performed") is not True or
        searched.get("provider") != "CHATGPT_NATIVE_WEB_SEARCH" or
        not isinstance(searched.get("queries"), list) or
        not any(isinstance(x, str) and x.strip() for x in searched["queries"]) or
        not isinstance(searched.get("retrieved_at"), str) or
        not searched["retrieved_at"].strip()):
        return missing("CHATGPT_NATIVE_WEB_SEARCH_NOT_EVIDENCED")

    sources = report.get("sources")
    if not isinstance(sources, list):
        return missing("NO_RESEARCH_SOURCES")
    source_ids = set()
    credible_groups = set()
    for source in sources:
        if not isinstance(source, Mapping):
            return bad("INVALID_SOURCE_ROW")
        sid = source.get("source_id")
        if not isinstance(sid, str) or not re.fullmatch(r"WEB-\d{3,4}", sid) or sid in source_ids:
            return bad("INVALID_OR_DUPLICATE_SOURCE_ID")
        source_ids.add(sid)
        if not _safe_url(source.get("url")):
            return bad("SOURCE_HAS_UNSAFE_OR_INVALID_URL")
        if (not isinstance(source.get("publisher"), str) or
            not source["publisher"].strip() or not isinstance(source.get("source_group"), str) or
            not source["source_group"].strip()):
            return bad("SOURCE_PUBLISHER_OR_INDEPENDENCE_MISSING")
        if source.get("source_type") not in _VALID_SOURCES or source.get("summary_scope") not in ("SHORT", "DETAILED"):
            return bad("SOURCE_TYPE_OR_SCOPE_INVALID")
        if source.get("identity_match") is True:
            credible_groups.add(source["source_group"].casefold())
        elif source.get("identity_match") is not False:
            return bad("UNVERIFIED_SOURCE_IDENTITY")

    independent = len(credible_groups)
    if independent < 2:
        return missing("NEED_TWO_INDEPENDENT_CREDIBLE_MOVIE_SOURCES", independent)

    before, after = report.get("review_sha256_before"), report.get("review_sha256_after")
    if not all(isinstance(h, str) and _HASH.fullmatch(h) for h in (before, after)):
        return bad("REVIEW_HASH_PROVENANCE_MISSING")
    if report.get("narrative_only_gate") != "PASS" or report.get("evidence_map_consistent") is not True:
        return bad("FINAL_REVIEW_NARRATIVE_OR_EVIDENCE_MAP_FAILED")
    if report.get("g05_script_human_approved") is not False:
        return bad("WEB_CROSSCHECK_CANNOT_APPROVE_G05_SCRIPT")
    findings = report.get("findings")
    if not isinstance(findings, list) or not findings:
        return missing("NO_REVIEW_TO_WEB_COMPARISON_RECORDED", independent)
    seen_fids = set()
    warnings = False
    was_revised = False
    needs_film_review = False
    for item in findings:
        if not isinstance(item, Mapping):
            return bad("FINDING_NOT_MAPPING")
        fid=item.get("finding_id")
        if not isinstance(fid,str) or not fid.startswith("WEB-F-") or fid in seen_fids:
            return bad("FINDING_ID_INVALID_OR_DUPLICATED")
        seen_fids.add(fid)
        ftype=item.get("type")
        if ftype not in _VALID_TYPES or item.get("severity") not in ("MAJOR", "MINOR"):
            return bad("FINDING_TYPE_OR_SEVERITY_INVALID")
        if item.get("film_evidence") not in _VALID_EVIDENCE or item.get("resolution") not in _VALID_RESOLUTIONS:
            return bad("FINDING_EVIDENCE_OR_ACTION_INVALID")
        if item.get("resolved") not in (True,False) or type(item.get("resolved")) is not bool:
            return bad("FINDING_RESOLUTION_STATUS_MISSING")
        if not isinstance(item.get("note"),str) or not item["note"].strip():
            return bad("FINDING_REASONING_MISSING")
        refs=item.get("source_ids")
        if not isinstance(refs,list) or not refs or not set(refs).issubset(source_ids):
            return bad("FINDING_CITES_NONEXISTENT_SOURCE")
        for field in ("review_paragraph_ids","g04_event_ids"):
            v=item.get(field)
            if not isinstance(v,list) or any(not isinstance(k,str) or not _ID.fullmatch(k) for k in v):
                return bad("INVALID_FINDING_REVIEW_OR_EVENT_REFERENCES")
            if len(v)!=len(set(v)):
                return bad("DUPLICATE_REVIEW_OR_EVENT_REFERENCE")
        decision=item["resolution"]
        evidence=item["film_evidence"]
        if decision=="REVISED_G04_SUPPORTED":
            if evidence!="G04_VERIFIED" or not item["g04_event_ids"] or item["resolved"] is not True:
                return bad("WEB_SOURCE_WAS_PROMOTED_TO_FACT_WITHOUT_G04_EVIDENCE")
            was_revised=True
            warnings=True
        elif decision=="NO_ACTION_SHORT_SYNOPSIS":
            if ftype!="NOT_COVERED":
                return bad("SHORT_SYNOPSIS_NONCOVERAGE_MISUSED")
            warnings=True
        elif decision=="ESCALATE_G04":
            if item["resolved"] is True:
                return bad("ESCALATED_EVENT_CLAIMED_RESOLVED")
            if item["severity"]=="MAJOR":
                needs_film_review=True
            warnings=True
        elif decision=="OMITTED_UNVERIFIED":
            if item["resolved"] is not True:
                needs_film_review=item["severity"]=="MAJOR"
            warnings=True
        elif decision=="KEEP":
            if ftype in ("MISSING_BEAT", "POTENTIAL_CONFLICT", "SOURCE_DISAGREEMENT") and item["severity"]=="MAJOR":
                if item["resolved"] is not True:
                    needs_film_review=True
                warnings=True
        if ftype!="MATCH":
            warnings=True
        if ftype in ("POTENTIAL_CONFLICT", "SOURCE_DISAGREEMENT", "MISSING_BEAT") and item["severity"]=="MAJOR" and item["resolved"] is not True:
            needs_film_review=True
    if was_revised and before==after:
        return bad("REPORTED_REVISION_WITH_UNCHANGED_REVIEW_HASH")
    if not was_revised and before!=after:
        return bad("UNEXPLAINED_REVIEW_HASH_CHANGE")
    if needs_film_review:
        return _result("NEEDS_REVIEW","NEEDS_FILM_VERIFICATION",sources=independent,
                       reviewed_findings=len(findings),issues=["UNRESOLVED_MATERIAL_FILM_PLOT_CLAIM"])
    return _result("PASS_WITH_WARNINGS" if warnings else "PASS",
                   "REVISED_FROM_FILM_EVIDENCE" if was_revised else "KEEP",
                   sources=independent, reviewed_findings=len(findings))
