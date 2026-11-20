"""v1.3.18: web research happens after full draft, only as a crosscheck to G04."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "g05_web_crosscheck_policy.py"


def api():
    spec = importlib.util.spec_from_file_location("web_crosscheck_policy", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def example():
    return {
        "schema_version":"g05-web-crosscheck.v1",
        "film_identity":{"title":"Fatman","year":2020,"identity_checked":True},
        "search":{"performed":True,"provider":"CHATGPT_NATIVE_WEB_SEARCH",
                  "queries":["Fatman 2020 Saban Films plot","Fatman 2020 detailed film synopsis"],
                  "retrieved_at":"2026-11-20T08:30:00+07:00"},
        "sources":[
            {"source_id":"WEB-001", "url":"https://www.sabanfilms.com/films/fatman/",
             "publisher":"Saban Films","source_group":"SABAN_FILMS",
             "source_type":"OFFICIAL_DISTRIBUTOR","identity_match":True,"summary_scope":"SHORT"},
            {"source_id":"WEB-002", "url":"https://www.imdb.com/title/tt10310140/plotsummary/",
             "publisher":"IMDb","source_group":"IMDB",
             "source_type":"FILM_CATALOG","identity_match":True,"summary_scope":"DETAILED"},
        ],
        "findings":[
            {"finding_id":"WEB-F-001","type":"MATCH","severity":"MINOR",
             "source_ids":["WEB-001","WEB-002"],"review_paragraph_ids":["P-0018"],
             "g04_event_ids":["EV-0008"],"film_evidence":"G04_VERIFIED",
             "resolution":"KEEP","resolved":True,
             "note":"Two sources agree with the existing narrative in substance."},
        ],
        "review_sha256_before":"a"*64,"review_sha256_after":"a"*64,
        "narrative_only_gate":"PASS","evidence_map_consistent":True,
        "g05_script_human_approved":False,
    }


class WebCrosscheckContract(unittest.TestCase):
    def test_basic_crosscheck_passes_without_gating_human_approval(self):
        result = api().evaluate_crosscheck(example())
        self.assertEqual(result["Q05_WEB_STORY_CROSSCHECK"], "PASS")
        self.assertFalse(result["G05_SCRIPT_approved"])
        self.assertFalse(result["auto_start_G06"])
        self.assertEqual(result["recommendation"],"KEEP")

    def test_missing_or_fake_search_never_claims_pass(self):
        d=example();d["search"]["performed"]=False
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"NOT_VERIFIED")
        d=example();d["search"]["provider"]="PYTHON_REQUESTS"
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"NOT_VERIFIED")

    def test_two_same_publisher_sources_do_not_count_as_independent(self):
        d=example();d["sources"][1]["source_group"]="SABAN_FILMS"
        x=api().evaluate_crosscheck(d)
        self.assertEqual(x["status"],"NOT_VERIFIED")
        self.assertEqual(x["credible_independent_sources"],1)

    def test_url_and_film_identity_cannot_be_fabricated(self):
        d=example();d["sources"][0]["url"]="javascript:alert(1)"
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"BLOCKED")
        d=example();d["sources"][0]["identity_match"]=False
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"NOT_VERIFIED")

    def test_web_only_claim_never_silently_added_to_review(self):
        d=example();d["findings"]=[{
          "finding_id":"WEB-F-002","type":"MISSING_BEAT","severity":"MAJOR",
          "source_ids":["WEB-001"],"review_paragraph_ids":["P-0016"],
          "g04_event_ids":[],"film_evidence":"WEB_ONLY","resolution":"REVISED_G04_SUPPORTED",
          "resolved":True,"note":"Source alone is not primary movie evidence."}]
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"BLOCKED")

    def test_major_missing_beat_flags_film_reinspection(self):
        d=example();d["findings"]=[{
          "finding_id":"WEB-F-COAL","type":"MISSING_BEAT","severity":"MAJOR",
          "source_ids":["WEB-001","WEB-002"],"review_paragraph_ids":["P-0016"],
          "g04_event_ids":[],"film_evidence":"G04_UNVERIFIED","resolution":"ESCALATE_G04",
          "resolved":False,"note":"Billy got coal before hiring the assassin; verify in source film."}]
        x=api().evaluate_crosscheck(d)
        self.assertEqual(x["status"],"NEEDS_REVIEW")
        self.assertEqual(x["recommendation"],"NEEDS_FILM_VERIFICATION")

    def test_revisions_need_source_support_and_changed_script_hash(self):
        d=example();d["findings"]=[{
          "finding_id":"WEB-F-COAL","type":"MISSING_BEAT","severity":"MAJOR",
          "source_ids":["WEB-001","WEB-002"],"review_paragraph_ids":["P-0016"],
          "g04_event_ids":["EV-0008"],"film_evidence":"G04_VERIFIED",
          "resolution":"REVISED_G04_SUPPORTED","resolved":True,
          "note":"A newly checked G04 event supports this missing beat."}]
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"BLOCKED")
        d["review_sha256_after"]="b"*64
        r=api().evaluate_crosscheck(d)
        self.assertEqual(r["status"],"PASS_WITH_WARNINGS")
        self.assertEqual(r["recommendation"],"REVISED_FROM_FILM_EVIDENCE")

    def test_short_synopsis_omission_is_not_a_film_contradiction(self):
        d=example();d["findings"]=[{
          "finding_id":"WEB-F-SHORT","type":"NOT_COVERED","severity":"MINOR",
          "source_ids":["WEB-001"],"review_paragraph_ids":["P-0039"],
          "g04_event_ids":["EV-0021"],"film_evidence":"G04_VERIFIED",
          "resolution":"NO_ACTION_SHORT_SYNOPSIS","resolved":True,
          "note":"A brief synopsis lacks ending details; not a conflict."}]
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"PASS_WITH_WARNINGS")

    def test_no_review_if_last_script_contains_workflow_leak(self):
        d=example();d["narrative_only_gate"]="BLOCKED"
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"BLOCKED")
        d=example();d["evidence_map_consistent"]=False
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"BLOCKED")

    def test_invalid_finding_refs_block(self):
        d=example();d["findings"][0]["source_ids"]=["WEB-NONE"]
        self.assertEqual(api().evaluate_crosscheck(d)["status"],"BLOCKED")

    def test_policy_contract_integrates_story_first_and_no_auto_revision(self):
        skill=(ROOT/"SKILL.md").read_text(encoding="utf-8")
        ref=(ROOT/"references/G05_WEB_STORY_CROSSCHECK_V1318.md").read_text(encoding="utf-8")
        policy=(ROOT/"references/G05_NARRATIVE_ONLY_V1317.md").read_text(encoding="utf-8")
        self.assertIn("G05_WEB_STORY_CROSSCHECK_V1318",skill)
        self.assertIn("CHATGPT_NATIVE_WEB_SEARCH",ref)
        self.assertIn("G05_SCRIPT",ref)
        self.assertIn("G04",ref)
        self.assertIn("G05.REVIEW.FULL",ref)
        self.assertIn("review_evidence_map",ref)
        self.assertIn("Q05_WEB_STORY_CROSSCHECK",ref)
        self.assertIn("G05_NARRATIVE_ONLY_V1317",ref)
        self.assertIn("G05_NARRATIVE_ONLY_V1317",skill)
        self.assertIn("Q05_NARRATIVE_ONLY",policy)

if __name__=="__main__":unittest.main(verbosity=2)
