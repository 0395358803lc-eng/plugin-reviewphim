"""Regression and pressure-scenario checks: one full movie transcript task."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLUG=ROOT.parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
class WholeFilmTranscriptContract(unittest.TestCase):
    def test_primary_contract_overrides_old_ten_minute_batches(self):
        entry=read('SKILL.md');policy=read('references/WHOLE_FILM_TRANSCRIPT_V1314.md');story=read('references/STORY_FIRST_WORKFLOW_V1313.md')
        self.assertIn('WHOLE_FILM_TRANSCRIPT_V1314.md',entry)
        self.assertIn('WHOLE_FILM_TRANSCRIPT_V1314.md',story)
        for tok in ('G02.ASR.FULL','NO_BATCH_SPLIT','one_model_transcribe_call','B001–B010','G03','G04'):self.assertIn(tok,policy)
        self.assertIn('G02.ASR.FULL',entry)
    def test_no_new_ten_minute_tasks_and_no_workflow_split(self):
        p=read('references/WHOLE_FILM_TRANSCRIPT_V1314.md')
        for tok in ('không phân lô 10 phút','không chia G02 thành nhiều microtask','checkpoint','một qc','không tự chạy ngầm'):self.assertIn(tok.lower(),p.lower())
    def test_protection_of_historical_evidence_and_human_gates(self):
        p=read('references/WHOLE_FILM_TRANSCRIPT_V1314.md')
        for tok in ('append-only','NOT_VERIFIED','không ghi đè','source_sha256','plan_hash','G05_SCRIPT','G07_VOICE','G10_PILOT','Q02','MATERIAL_BLOCKER','visual'):self.assertIn(tok.lower(),p.lower())
    def test_manifest_versions_and_app_bindings(self):
        main=json.loads((PLUG/'plugin.json').read_text(encoding='utf-8'))
        codex=json.loads((PLUG/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        self.assertEqual(main['version'],'1.3.25');self.assertEqual(codex['version'],'1.3.25')
        self.assertEqual(main['extensions']['com.openai']['apps'],'./.app.json');self.assertEqual(codex['apps'],'./.app.json')
        self.assertIn('WHOLE_FILM_TRANSCRIPT_V1314',' '.join(main['extensions']['com.openai']['interface']['defaultPrompt']))
    def test_plan_generator_is_single_scope_no_batched_task_list(self):
        path=ROOT/'tools/whole_film_transcript_policy.py'
        spec=importlib.util.spec_from_file_location('whole_policy',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        p=m.make_asr_scope(source_sha256='a'*64,source_duration_s=5823.632,source_movie=r'D:\Phim\phim-3\film.mp4',job_dir=r'D:\Phim\phim-3\WORKSPACE\fatman',device_id='test-device-01')
        self.assertEqual(p['task_ids'],['G02.ASR.FULL']);self.assertEqual(len(p['asr_operations']),1)
        self.assertEqual(p['asr_operations'][0]['time_window_s'],[0.0,5823.632])
        self.assertTrue(p['asr_operations'][0]['one_model_transcribe_call'])
        self.assertEqual(p['asr_operations'][0]['transcript_output'],'analysis/transcript_original.jsonl')
        self.assertTrue(p['asr_operations'][0]['gpu_first']);self.assertEqual(p['batch_split_policy'],'NO_BATCH_SPLIT');self.assertFalse(p['auto_install'])
    def test_q02_coverage_separate_from_speech_segment_gaps(self):
        path=ROOT/'tools/whole_film_transcript_policy.py'
        spec=importlib.util.spec_from_file_location('whole_policy2',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        a=m.qc_full_film(source_duration_s=5823.632,decoded_audio_duration_s=5823.632,input_sha256_verified=True,whole_file_audio=True,one_transcribe_call=True,raw_count=2,provisional_count=1,quarantined_count=1,segments=[{'segment_id':'S1','start':40.2,'end':40.9}],material_blockers=[])
        self.assertEqual(a['technical_qc'],'PASS');self.assertEqual(a['Q02_GATE_STATUS'],'PASS');self.assertEqual(a['QC_STATUS'],'PASS_WITH_WARNINGS')
        self.assertIn('silence_is_not_missing_audio',a);self.assertTrue(a['silence_is_not_missing_audio'])
        failed=m.qc_full_film(source_duration_s=5823.632,decoded_audio_duration_s=1800,input_sha256_verified=True,whole_file_audio=False,one_transcribe_call=True,raw_count=2,provisional_count=2,quarantined_count=0,segments=[{'segment_id':'S1','start':40.2,'end':40.9}],material_blockers=[])
        self.assertEqual(failed['Q02_GATE_STATUS'],'BLOCKED')
if __name__=='__main__':unittest.main(verbosity=2)
