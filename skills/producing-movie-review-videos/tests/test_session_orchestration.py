# -*- coding: utf-8 -*-
from pathlib import Path
import json, unittest
R=Path(__file__).resolve().parents[1]
class TestSessionOrchestration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.entry=(R/'SKILL.md').read_text('utf-8')
  cls.session=(R/'references/SESSION_ORCHESTRATION.md').read_text('utf-8')
 def test_p00_scope(self):
  for s in ('list_devices','A01–A08/O01–O03','JOB_DIR','deviceId','reuse','gói','GPU.PLAN'):
   self.assertIn(s,self.entry+self.session)
 def test_resume(self):
  for s in ('WORK_PACKAGE_ID','plan_hash','approval_ref','Tiếp tục gói','PARTIAL','WAITING_FOR_JOB','QC'):
   self.assertIn(s,self.session)
 def test_human_gates(self):
  for s in ('G05','G07','G10','G15','FILM_UNDERSTANDING_READY','không đề xuất chạy G05'):
   self.assertIn(s,self.session)
 def test_version(self):
  for filename in ('plugin.json','.codex-plugin/plugin.json'):
   d=json.loads((R.parents[1]/filename).read_text('utf-8'))
   self.assertEqual(d['version'],'1.3.26')
if __name__=='__main__': unittest.main()
