"""v1.3.15: G01/G03/G05 are atomic stage tasks; newer G04 policy remains additive."""
import importlib.util
import json
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
PLUGIN=ROOT.parents[1]
def read(path): return (ROOT/path).read_text(encoding='utf-8')
class AtomicStageTests(unittest.TestCase):
    def test_primary_contract_declares_exact_three_atomic_stages(self):
        entry=read('SKILL.md');policy=read('references/ATOMIC_STAGES_V1315.md')
        self.assertIn('ATOMIC_STAGES_V1315.md',entry)
        for task in ('G01.SOURCE.FULL','G03.TRANSLATE.FULL','G05.REVIEW.FULL'):
            self.assertIn(task,policy);self.assertIn(task,entry)
        self.assertIn('G02.ASR.FULL',policy)
        self.assertIn('WHOLE_FILM_TRANSCRIPT_V1314.md',policy)
        self.assertIn('NO_STAGE_SPLIT',policy)
        for key in ('G01','G03','G05'): self.assertIn(key,policy)
    def test_g03_translation_uses_chatgpt_all_transcript_with_one_qc(self):
        p=read('references/ATOMIC_STAGES_V1315.md')
        for word in ('ChatGPT trực tiếp','toàn bộ','segment_id','timecode','Q03','không dùng model dịch','không dùng script dịch','40 segment','không phải task','PARTIAL'):
            self.assertIn(word.casefold(),p.casefold())
    def test_g05_full_story_review_preserves_approval_and_grounding(self):
        p=read('references/ATOMIC_STAGES_V1315.md')
        for word in ('sáu bước','G05_SCRIPT','REVIEW_STORY_READY','FILM_UNDERSTANDING_READY','story_map','event_id','visual_intent','Q05','không bịa','không tự chạy G06'):
            self.assertIn(word.casefold(),p.casefold())
    def test_g01_is_once_without_rerunning_p00_or_unapproved_fatman(self):
        p=read('references/ATOMIC_STAGES_V1315.md')
        for word in ('Q01','SOURCE_MOVIE','FFprobe','SHA-256','read-only','JOB_DIR','checkpoint','Fatman','P00','không tự chạy'):
            self.assertIn(word.casefold(),p.casefold())
    def test_other_stages_and_existing_g02_are_unchanged(self):
        p=read('references/ATOMIC_STAGES_V1315.md')
        for word in ('G04','G06','G07','G08','G09','G10','G11','G12','G13','G14','G15','G07_VOICE','G10_PILOT','SHOT_SELECTION_READY','G14','G02.ASR.FULL','G15_DELETE'):
            self.assertIn(word,p)
        self.assertIn('NO_BATCH_SPLIT',read('references/WHOLE_FILM_TRANSCRIPT_V1314.md'))
    def test_policy_module_atomic_task_scope_and_checkpoint_behavior(self):
        path=ROOT/'tools/atomic_stage_policy.py'
        spec=importlib.util.spec_from_file_location('atomic_stage_policy',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        for stage,tid in [('G01','G01.SOURCE.FULL'),('G03','G03.TRANSLATE.FULL'),('G05','G05.REVIEW.FULL')]:
            plan=m.make_stage_scope(stage,source_sha256='a'*64,device_id='approved-device',job_dir=r'D:\Movies\WORKSPACE',source_duration_s=5823.632)
            self.assertEqual(plan['task_ids'],[tid]);self.assertEqual(plan['stage'],stage)
            self.assertEqual(plan['work_split_policy'],'NO_STAGE_SPLIT')
            self.assertEqual(plan['stage_qc'],f'Q{stage[1:]}');self.assertFalse(plan['auto_install'])
        with self.assertRaises(ValueError):m.make_stage_scope('G04',source_sha256='a'*64,device_id='approved-device',job_dir=r'D:\Movies\WORKSPACE')
    def test_q03_and_q05_not_claimed_pass_from_partial_data(self):
        path=ROOT/'tools/atomic_stage_policy.py'
        spec=importlib.util.spec_from_file_location('atomic_stage_policy2',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertEqual(m.qc_translation(total_source=100,total_translated=99,all_ids_match=True,all_times_match=True)['status'],'PARTIAL')
        self.assertEqual(m.qc_translation(total_source=100,total_translated=100,all_ids_match=False,all_times_match=True)['status'],'BLOCKED')
        self.assertEqual(m.qc_review(six_steps_complete=True,story_facts_verified=True,visual_evidence_ready=True,human_script_approved=False)['status'],'WAITING_FOR_HUMAN_APPROVAL')
        self.assertEqual(m.qc_review(six_steps_complete=True,story_facts_verified=True,visual_evidence_ready=True,human_script_approved=True)['status'],'PASS')
    def test_versions_and_entrypoint(self):
        manifest=json.loads((PLUGIN/'plugin.json').read_text(encoding='utf-8'))
        codex=json.loads((PLUGIN/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['version'],'1.3.27');self.assertEqual(codex['version'],'1.3.27')
        self.assertEqual(manifest['extensions']['com.openai']['apps'],'./.app.json')
        self.assertEqual(codex['apps'],'./.app.json')
        prompt=' '.join(manifest['extensions']['com.openai']['interface']['defaultPrompt'])
        self.assertIn('PRODUCTION_FIRST_V1325',prompt)
        self.assertIn('PRODUCTION_RELIABILITY_V1326',prompt)
if __name__=='__main__':unittest.main(verbosity=2)
