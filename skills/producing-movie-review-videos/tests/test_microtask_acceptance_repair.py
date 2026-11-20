# -*- coding: utf-8 -*-
from pathlib import Path
import json, unittest
R=Path(__file__).resolve().parents[1]
class TestMicrotaskAcceptanceRepair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.entry=(R/'SKILL.md').read_text('utf-8')
  cls.qc=(R/'references/MICROTASK_ACCEPTANCE_REPAIR.md').read_text('utf-8')
 def test_each_internal_task_remains_audited(self):
  for s in ('acceptance_criteria','criterion_id','expected','actual','evidence_refs','input_hashes','output_hashes','QC_STATUS','microtask_ledger.jsonl','append-only'):
   self.assertIn(s,self.qc)
 def test_report_only_package_summary_for_clicks(self):
  self.assertIn('QC tổng hợp của gói',self.qc)
  self.assertIn('tự làm task kế trong cùng gói',self.qc)
 def test_safe_repairs_are_bounded(self):
  for s in ('repair_budget','issue_id','tối đa 2','recheck','không xóa','ngoài phạm vi'):
   self.assertIn(s,self.qc)
 def test_unverified_is_never_pass(self):
  for s in ('NOT_VERIFIED','BLOCKED','WAITING_FOR_AUDIO_UPLOAD','G05','G07','G10','G15','người dùng upload'):
   self.assertIn(s,self.qc)
 def test_version(self):
  p=json.loads((R.parents[1]/'plugin.json').read_text('utf-8'))
  self.assertEqual(p['version'],'1.3.27')
if __name__=='__main__':unittest.main()
