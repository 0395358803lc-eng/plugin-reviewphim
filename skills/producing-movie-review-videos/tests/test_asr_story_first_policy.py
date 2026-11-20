"""Behavior-driven tests of factual ASR triage that never fabricates hearing."""
import importlib.util
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools/asr_story_first_policy.py"

def load():
    spec = importlib.util.spec_from_file_location("asr_story_first_policy", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class PolicyTests(unittest.TestCase):
    def test_b001_b003_noncritical_and_quarantined(self):
        p = load()
        for phrase in ("Thank you.", "I don't know."):
            s = {"segment_id":"S", "text_original":phrase, "flags":["LOW_LOGPROB_REVIEW"],
                 "story_role":"peripheral", "used_in_review":False,"linked_key_event":False,
                 "unverified":True, "raw_preserved":True}
            self.assertEqual(p.classify(s)["impact_classification"],"MINOR_NONBLOCKING")
            self.assertFalse(p.classify(s)["may_quote_in_review"])

    def test_single_word_can_block_plot_fact(self):
        p = load()
        s={"segment_id":"S", "text_original":"No.", "story_role":"core",
           "used_in_review":True,"linked_key_event":True,"unverified":True,
           "raw_preserved":True,"flags":["LOW_LOGPROB_REVIEW"]}
        self.assertEqual(p.classify(s)["impact_classification"],"MATERIAL_BLOCKER")

    def test_unknown_role_triggers_group_context_review(self):
        p = load()
        s={"segment_id":"S", "text_original":"Maybe.", "story_role":"unknown",
           "used_in_review":False,"linked_key_event":False,"unverified":True,
           "raw_preserved":True,"flags":["LOW_LOGPROB_REVIEW"]}
        self.assertEqual(p.classify(s)["impact_classification"],"MATERIAL_REVIEW")

    def test_threshold_batch_and_no_false_Q02_PASS(self):
        p = load()
        segments=[{"segment_id":f"S{i}", "text_original":"Thanks.", "story_role":"peripheral",
          "used_in_review":False,"linked_key_event":False,"unverified":True,"raw_preserved":True,
          "flags":["LOW_LOGPROB_REVIEW"]} for i in range(2)]
        decision=p.summarize(segments,total_raw_candidates=100,full_film_coverage=False,source_hash_ok=True)
        self.assertEqual(decision["batch_status"],"PASS_WITH_WARNINGS")
        self.assertEqual(decision["Q02_GATE_STATUS"],"NOT_VERIFIED")
        self.assertEqual(decision["ignored_in_review_segment_ids"],["S0","S1"])
        segments.append(dict(segments[0],segment_id="S2"))
        decision=p.summarize(segments,total_raw_candidates=100,full_film_coverage=False,source_hash_ok=True)
        self.assertEqual(decision["batch_status"],"MATERIAL_REVIEW")

    def test_missing_batch_or_bad_hash_is_hard_stop(self):
        p=load()
        d=p.summarize([],total_raw_candidates=5,full_film_coverage=False,source_hash_ok=False)
        self.assertEqual(d["batch_status"],"MATERIAL_BLOCKER")
        d=p.summarize([],total_raw_candidates=5,full_film_coverage=False,source_hash_ok=True,missing_batch=True)
        self.assertEqual(d["batch_status"],"MATERIAL_BLOCKER")

    def test_not_uploaded_audio_does_not_claim_heard(self):
        p=load()
        s={"segment_id":"S","text_original":"I don't know.","story_role":"peripheral",
           "used_in_review":False,"linked_key_event":False,"unverified":True,"raw_preserved":True}
        self.assertFalse(p.classify(s)["heard_verified"])

if __name__=="__main__": unittest.main(verbosity=2)
