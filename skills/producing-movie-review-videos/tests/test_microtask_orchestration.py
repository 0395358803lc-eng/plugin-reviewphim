# -*- coding: utf-8 -*-
"""v1.3.22: verify orchestration retains real QC without old G04/G05 batches."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class TestMicrotaskOrchestration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=(ROOT/'references/MICROTASK_ORCHESTRATION.md').read_text(encoding='utf8')
        cls.policy=(ROOT/'references/G04_G05_FAST_TRACK_V1322.md').read_text(encoding='utf8')
        cls.entry=(ROOT/'SKILL.md').read_text(encoding='utf8')
    def test_stages_retained(self):
        for idx in range(1,16):
            self.assertIn(f'G{idx:02d}',self.doc)
        self.assertIn('G11A',self.doc)
        self.assertIn('G11B',self.doc)
    def test_g04_g05_one_task_one_qc(self):
        for task in ('G04.FILM.UNDERSTANDING.FULL','G05.REVIEW.FULL'):
            self.assertIn(task,self.doc)
            self.assertIn(task,self.entry)
        self.assertIn('Một Q04',self.doc)
        self.assertIn('Một Q05',self.doc)
        self.assertIn('G05_SCRIPT',self.doc)
        self.assertIn('không xin duyệt',self.policy)
    def test_source_checkpoints_safety_preserved(self):
        for token in ('WORK_PACKAGE_ID','QC','Tiếp tục gói','source_hash',
                      'BLOCKED','NOT_VERIFIED','G15_DELETE','WAITING_FOR_AUDIO_UPLOAD',
                      'G07_VOICE','G10_PILOT'):
            self.assertIn(token,self.doc)
        self.assertIn('SMART_BATCH_APPROVAL.md',self.entry)
    def test_no_fake_visual_pass(self):
        self.assertIn('ChatGPT',self.policy)
        self.assertIn('VERIFIED',self.policy) if 'VERIFIED' in self.policy else self.assertIn('bằng chứng',self.policy)
        self.assertIn('G08',self.policy)

if __name__=='__main__':unittest.main()
