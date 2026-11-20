"""Regression for new G04/G05 single-task policy; no remote machine involved."""
import unittest
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'tools'/'g04_g05_atomic_policy.py'


def load_policy():
    assert MODULE.exists(), 'G04/G05 atomic policy tool must exist'
    spec=importlib.util.spec_from_file_location('atomic_g04_g05', MODULE)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class AtomicG04G05(unittest.TestCase):
    def test_g04_one_job_not_batches(self):
        p=load_policy()
        self.assertEqual(p.validate_stage_tasks(['G04.FILM.UNDERSTANDING.FULL'],[],['G04']),
                         {'G04':'G04.FILM.UNDERSTANDING.FULL'})
        for tasks in [['G04.M01'], ['G04.M02.B001'],
                      ['G04.FILM.UNDERSTANDING.FULL','G04.M04.B001']]:
            with self.subTest(tasks=tasks),self.assertRaises(ValueError):
                p.validate_stage_tasks(tasks,[],['G04'])

    def test_g05_no_paragraph_microtasks(self):
        p=load_policy()
        self.assertEqual(p.validate_stage_tasks(['G05.REVIEW.FULL'],[],['G05']),
                         {'G05':'G05.REVIEW.FULL'})
        with self.assertRaises(ValueError):
            p.validate_stage_tasks(['G05.M01','G05.M02.B001'],[],['G05'])

    def test_no_bounded_batches_for_either_stage(self):
        p=load_policy()
        for stem in ['G04.M02','G05.M02']:
            with self.subTest(stem=stem),self.assertRaises(ValueError):
                p.validate_stage_tasks(['G04.FILM.UNDERSTANDING.FULL','G05.REVIEW.FULL'],
                                       [{'stem':stem,'start':1,'end':2}],['G04','G05'])

    def test_other_stages_unaffected(self):
        p=load_policy()
        self.assertEqual(p.validate_stage_tasks(['G08.M01'],[],['G08']),{})

    def test_g04_gate_not_passed_by_index_or_transcript_only(self):
        p=load_policy()
        base={'scene_index_start_end':True,'film_evidence_exists':True,'core_events':[
              {'event_id':'EV1','importance':'CORE','status':'VERIFIED_VISUAL','media_inspected':True}],
              'unresolved_core_claims':[]}
        self.assertEqual(p.g04_readiness(base),'PASS')
        fail={**base,'core_events':[{'event_id':'EV1','importance':'CORE','status':'INDEXED','media_inspected':False}]}
        self.assertEqual(p.g04_readiness(fail),'NOT_VERIFIED')
        fail={**base,'unresolved_core_claims':['suspect identity unresolved']}
        self.assertEqual(p.g04_readiness(fail),'NEEDS_REVIEW')
        fail={**base,'film_evidence_exists':False}
        self.assertEqual(p.g04_readiness(fail),'BLOCKED')

    def test_g05_one_qc_and_human_gate(self):
        p=load_policy()
        record={'g04_status':'PASS','review_complete':True,'narrative_only':'PASS',
                'story_evidence':'PASS','web_crosscheck':'PASS','q05_count':1,
                'human_approval_g05_script':False}
        self.assertEqual(p.g05_readiness(record),'WAITING_FOR_HUMAN_APPROVAL')
        self.assertEqual(p.g05_readiness({**record,'human_approval_g05_script':True}),'PASS')
        self.assertEqual(p.g05_readiness({**record,'web_crosscheck':'NOT_VERIFIED'}),'NOT_VERIFIED')
        self.assertEqual(p.g05_readiness({**record,'q05_count':2}),'NEEDS_FIX')

    def test_rule_text_and_no_new_approval(self):
        s=(ROOT/'SKILL.md').read_text(encoding='utf8')
        ref=(ROOT/'references'/'G04_G05_FAST_TRACK_V1322.md').read_text(encoding='utf8')
        self.assertIn('G04.FILM.UNDERSTANDING.FULL',s)
        self.assertIn('G05.REVIEW.FULL',s)
        self.assertIn('G04_G05_FAST_TRACK_V1322.md',s)
        self.assertIn('G05_SCRIPT',ref)
        self.assertIn('G08',ref)
        self.assertIn('không xin duyệt',ref)
        self.assertIn('Q04',ref)
        self.assertIn('Q05',ref)

    def test_compatibility_with_one_click(self):
        s=(ROOT/'SKILL.md').read_text(encoding='utf8')
        self.assertIn('ONE_APPROVAL_START_POLICY_V1321',s)
        self.assertIn('MEDIA_EVIDENCE_HANDOFF_V1320',s)
        self.assertIn('G11A',s)
        self.assertIn('G11B',s)

if __name__=='__main__':unittest.main()
