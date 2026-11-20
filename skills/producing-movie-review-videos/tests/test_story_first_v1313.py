"""Regression contract for review-phim story-first policy, no unverifiable PASS claims."""
import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLUGIN_ROOT=ROOT.parents[1]
def read(relative):return (ROOT/relative).read_text(encoding='utf-8')
class StoryFirstContract(unittest.TestCase):
    def test_current_entrypoint_gives_new_policy_precedence(self):
        skill=read('SKILL.md');ref=read('references/STORY_FIRST_WORKFLOW_V1313.md')
        self.assertIn('STORY_FIRST_WORKFLOW_V1313.md',skill)
        for tok in ('ƯU TIÊN CAO','MINOR_NONBLOCKING','MATERIAL_BLOCKER'):self.assertIn(tok,ref)
    def test_small_asr_issue_not_human_audio_gate(self):
        p=read('references/STORY_FIRST_WORKFLOW_V1313.md')
        for tok in ('G02-B003-S0062','G02-B001-S0101','không đòi người dùng upload WAV','không sử dụng làm chứng cứ','không được bịa'):self.assertIn(tok,p)
    def test_minor_alerts_have_bounded_threshold_and_hard_breakers(self):
        p=read('references/STORY_FIRST_WORKFLOW_V1313.md')
        for tok in ('2%', '2 ứng viên','phủ định','tử vong','nhân vật','mất lô','hash','PASS_WITH_WARNINGS','TECHNICAL_QC','STORY_QC'):self.assertIn(tok,p)
    def test_visual_matching_remains_required_and_is_prioritized(self):
        p=read('references/STORY_FIRST_WORKFLOW_V1313.md')
        for tok in ('G04','G05','G08','SHOT_SELECTION_READY','VERIFIED_VISUAL','actor','action','G14','G05_SCRIPT','G07_VOICE','G10_PILOT'):self.assertIn(tok,p)
    def test_legacy_logs_are_not_mutated_by_policy_publication(self):
        p=read('references/STORY_FIRST_WORKFLOW_V1313.md')
        for tok in ('append-only','NOT_VERIFIED','không ghi đè','plan_hash','approval'):self.assertIn(tok,p)
    def test_manifest_versions_and_app_binding(self):
        a=json.loads((PLUGIN_ROOT/'plugin.json').read_text('utf-8'))
        b=json.loads((PLUGIN_ROOT/'.codex-plugin/plugin.json').read_text('utf-8'))
        self.assertEqual(a['version'],'1.3.26');self.assertEqual(b['version'],'1.3.26')
        self.assertEqual(a['extensions']['com.openai']['apps'],'./.app.json')
        self.assertEqual(b['apps'],'./.app.json')
        self.assertIn('PRODUCTION_FIRST_V1325',' '.join(a['extensions']['com.openai']['interface']['defaultPrompt']))
if __name__=='__main__':unittest.main(verbosity=2)
