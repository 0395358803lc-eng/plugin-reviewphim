# -*- coding: utf-8 -*-
from pathlib import Path
import re, unittest
R=Path(__file__).resolve().parents[1]
class TestMicrotaskOrchestration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=(R/'references/MICROTASK_ORCHESTRATION.md').read_text('utf-8')
        cls.entry=(R/'SKILL.md').read_text('utf-8')
    def test_all_fifteen_stages(self):
        self.assertEqual(re.findall(r'^\| \*\*G(\d\d) —',self.doc,re.M),[f'{i:02d}' for i in range(1,16)])
    def test_group_scope_and_internal_qc(self):
        for s in ('WORK_PACKAGE_ID','plan_hash','Mnn/Bxxx','QC','Tiếp tục gói','microtask_state.json','microtask_ledger.jsonl'):
            self.assertIn(s,self.doc)
        self.assertIn('SMART_BATCH_APPROVAL.md',self.entry)
    def test_small_batches_but_no_reapproval_each(self):
        for s in ('40 segment','1.000 từ','8 scene','12 beat','không xin phê duyệt từng batch'):
            self.assertIn(s,self.doc)
    def test_stops_on_unapproved_scope(self):
        for s in ('BLOCKED','WAITING_FOR_JOB','WAITING_FOR_AUDIO_UPLOAD','G15','G05','G07','G10'):
            self.assertIn(s,self.doc)
        self.assertIn('không được chạy bất kỳ task mới',self.doc)
if __name__=='__main__':unittest.main()
