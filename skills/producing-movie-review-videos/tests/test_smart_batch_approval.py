# -*- coding: utf-8 -*-
"""Regression contract: package-level consent, microtask-level evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / 'references'

class SmartBatchApprovalContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = (REFS/'SMART_BATCH_APPROVAL.md').read_text(encoding='utf-8')
        cls.entry = (ROOT/'SKILL.md').read_text(encoding='utf-8')
        cls.micro = (REFS/'MICROTASK_ORCHESTRATION.md').read_text(encoding='utf-8')
        cls.qc = (REFS/'MICROTASK_ACCEPTANCE_REPAIR.md').read_text(encoding='utf-8')
        cls.session = (REFS/'SESSION_ORCHESTRATION.md').read_text(encoding='utf-8')

    def test_authoritative_batch_mode(self):
        self.assertIn('SMART_BATCH_APPROVAL.md', self.entry)
        for text in (self.policy,self.entry,self.micro,self.session):
            self.assertIn('WORK_PACKAGE_ID', text)
        self.assertIn('ưu tiên cao hơn',self.policy)

    def test_one_approval_for_multiple_internal_tasks(self):
        self.assertIn('một phê duyệt gói',self.policy)
        self.assertIn('G03.M02.B001',self.policy)
        self.assertIn('G03.M02.B002',self.policy)
        self.assertIn('không xin phê duyệt lại',self.policy)

    def test_qc_and_checkpoint_do_not_disappear(self):
        for token in ('microtask_ledger.jsonl','microtask_state.json','input_hashes',
                      'output_hashes','PASS','NEEDS_FIX','NOT_VERIFIED','BLOCKED'):
            self.assertIn(token,self.policy)
        self.assertIn('QC từng microtask',self.qc)
        self.assertIn('QC tổng hợp của gói',self.qc)

    def test_boundary_and_human_gates(self):
        for token in ('deviceId','JOB_DIR','phim nguồn','kịch bản G05',
                      'giọng G07','pilot G10','xóa G15','GPU.PLAN',
                      'WAITING_FOR_AUDIO_UPLOAD','không tự chạy nền'):
            self.assertIn(token,self.policy)
        self.assertIn('không suy rộng',self.policy)

    def test_resume_same_package_does_not_escalate_scope(self):
        for token in ('Tiếp tục gói','plan_hash','source_hash','approval_ref',
                      'WAITING_FOR_JOB','PARTIAL','không phê duyệt lại'):
            self.assertIn(token,self.policy)

    def test_bounded_repair(self):
        for token in ('tối đa 2','không tải/cài','không xóa','ngoài phạm vi',
                      'issue_id','recheck'):
            self.assertIn(token,self.qc)

if __name__ == '__main__': unittest.main(verbosity=2)
