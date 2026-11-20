"""Legacy workflow invariants preserved; v1.3.24 manifests synchronized."""
from pathlib import Path
import json,re,unittest
R=Path(__file__).resolve().parents[1]
def d(path):return (R/path).read_text(encoding='utf-8')
class WorkflowConsistency(unittest.TestCase):
    def test_new_protocol_is_explicit_entrypoint_and_manifest_mirror(self):
        for path in ('SKILL.md','references/SMART_BATCH_APPROVAL.md','references/SESSION_ORCHESTRATION.md'):
            self.assertIn('WORKFLOW_CONSISTENCY_V1312.md',d(path))
        for path in ('plugin.json','.codex-plugin/plugin.json'):
            manifest=json.loads((R.parents[1]/path).read_text('utf-8'))
            self.assertEqual(manifest['version'],'1.3.27')
            self.assertIn('state machine',manifest['description'].lower())
    def test_g09_limited_to_preview_before_g10_pilot_and_g11_full(self):
        p=d('references/MICROTASK_ORCHESTRATION.md')
        g09=[x for x in p.splitlines() if re.match(r'^\|\s*(?:\*\*)?G09\b',x)][0]
        g10=[x for x in p.splitlines() if re.match(r'^\|\s*(?:\*\*)?G10\b',x)][0]
        g11=[x for x in p.splitlines() if re.match(r'^\|\s*(?:\*\*)?G11\b',x)][0]
        self.assertIn('pilot',g09.lower());self.assertNotIn('ghép verify MP4',g09)
        self.assertIn('người dùng duyệt',g10);self.assertIn('full',g11.lower())
        canon=d('references/WORKFLOW_CONSISTENCY_V1312.md')
        self.assertLess(canon.index('G09 |'),canon.index('G10 |'))
        self.assertLess(canon.index('G10 |'),canon.index('G11 |'))
    def test_stop_states_human_and_audio_are_distinct(self):
        for path in ('references/SMART_BATCH_APPROVAL.md','references/SESSION_ORCHESTRATION.md','references/MICROTASK_ACCEPTANCE_REPAIR.md'):
            content=d(path)
            for tok in ('WAITING_FOR_HUMAN_APPROVAL','WAITING_FOR_AUDIO_UPLOAD','PACKAGE_PASS'):self.assertIn(tok,content,path)
        canon=d('references/WORKFLOW_CONSISTENCY_V1312.md')
        for tok in ('G05_SCRIPT','G07_VOICE','G10_PILOT','G15_DELETE','DELIVERY_PASS','DELETE_NOT_REQUESTED'):self.assertIn(tok,canon)
    def test_resume_migration_lock_and_budgets_have_documented_guards(self):
        c=d('references/WORKFLOW_CONSISTENCY_V1312.md')
        for tok in ('LEGACY_INVENTORY','read-only','work_package.lock','atomic exclusive','Dedupe','plan_hash','per_issue','total','work-package.v2'):self.assertIn(tok,c)
        self.assertIn('canonical',c)
    def test_new_brief_and_final_report_are_available_and_preferred(self):
        e=d('SKILL.md')
        for p in ('templates/WORK_PACKAGE_BRIEF.md','templates/WORK_PACKAGE_FINAL.md'):
            self.assertIn(p,e);self.assertTrue((R/p).is_file())
        self.assertIn('WAITING_FOR_HUMAN_APPROVAL',d('templates/WORK_PACKAGE_FINAL.md'))
    def test_old_individual_approval_phrases_are_replaced_with_explicit_override(self):
        c=d('references/WORKFLOW_CONSISTENCY_V1312.md')
        for old in ('WORKFLOW.md','INSTALLATION_CATALOG.md','DEFAULTS_AND_TOOLS.md','MODEL_ROLE_POLICY.md','JOB_BRIEF.md','FINAL_REPORT.md'):self.assertIn(old,c)
        self.assertIn('không tự cài',c);self.assertIn('không tự chạy nền',c)
        self.assertIn('workflow_integrity_v1323.py',d('SKILL.md'))
if __name__=='__main__':unittest.main(verbosity=2)
