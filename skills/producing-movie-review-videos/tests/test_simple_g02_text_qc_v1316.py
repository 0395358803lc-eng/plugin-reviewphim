"""Tests for one-pass G02 text-only QC; raw ASR remains immutable."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def module():
    p = ROOT / 'tools' / 'simple_g02_text_qc.py'
    spec = importlib.util.spec_from_file_location('g02_text', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

class SimpleG02TextQC(unittest.TestCase):
    def test_stage_contract_explicitly_overrides_17_cluster_gate(self):
        entry = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        policy = (ROOT / 'references' / 'SIMPLE_G02_TEXT_QC_V1316.md').read_text(encoding='utf-8')
        self.assertIn('SIMPLE_G02_TEXT_QC_V1316.md', entry)
        self.assertIn('Q02_TEXT_PASS', policy)
        self.assertIn('Không kiểm 17 cụm', policy)
        self.assertIn('không chặn vì', policy)
        self.assertIn('G03.TRANSLATE.FULL', policy)
        self.assertIn('G04', policy)

    def test_text_repairs_are_conservative_and_keep_words(self):
        m = module()
        src = '  Cafe\u0301   now ,  please !  \r\n'
        fixed, edits = m.normalize_visible_text(src)
        self.assertEqual(fixed, 'Café now, please!')
        self.assertGreaterEqual(len(edits), 1)
        self.assertEqual(m.normalize_visible_text("  I don't  know.  ")[0], "I don't know.")

    def test_complete_transcript_passes_even_with_asr_warnings(self):
        m=module()
        rows = [
          {'segment_id':'S1','start':0.0,'end':2.0,'text_original':' Hello ,  world ! ', 'speaker_id':'UNKNOWN'},
          {'segment_id':'S2','start':10.0,'end':15.0,'text_original':' I don\u2019t know. ', 'speaker_id':'UNKNOWN'},
        ]
        result=m.process_transcript_rows(rows, source_duration_s=60.0, source_hash_verified=True,
            full_audio_processed=True, model_transcribe_completed=True, asr_warning_count=111)
        self.assertEqual(result['Q02_GATE_STATUS'],'PASS')
        self.assertEqual(result['text_qc'],'PASS')
        self.assertEqual(result['clean_rows'][0]['text_original'],'Hello, world!')
        self.assertEqual(result['clean_rows'][1]['text_original'],'I don\u2019t know.')
        self.assertEqual(result['asr_warnings_recorded'],111)
        self.assertEqual(result['raw_rows_preserved'],True)

    def test_out_of_range_asr_tail_is_excluded_not_17_cluster_recheck(self):
        m=module()
        rows=[{'segment_id':'S1','start':1.0,'end':2.0,'text_original':'Hi.'},
              {'segment_id':'S2','start':59.0,'end':66.0,'text_original':'Transcription by CastingWords'}]
        result=m.process_transcript_rows(rows,source_duration_s=60.0,source_hash_verified=True,
            full_audio_processed=True,model_transcribe_completed=True,asr_warning_count=17)
        self.assertEqual(result['Q02_GATE_STATUS'],'PASS')
        self.assertEqual(result['excluded_invalid_timing_ids'],['S2'])
        self.assertEqual(len(result['clean_rows']),1)
        self.assertEqual(result['text_qc'],'PASS')

    def test_real_text_corruption_blocks_until_repaired_without_guessing(self):
        m=module()
        rows=[{'segment_id':'S1','start':0.0,'end':2.0,'text_original':'I\ufffd guess.'}]
        result=m.process_transcript_rows(rows,source_duration_s=60.0,source_hash_verified=True,
            full_audio_processed=True,model_transcribe_completed=True,asr_warning_count=0)
        self.assertEqual(result['Q02_GATE_STATUS'],'NOT_VERIFIED')
        self.assertEqual(result['unresolved_text_error_ids'],['S1'])

    def test_legacy_full_film_gate_does_not_block_on_content_flags(self):
        modpath = ROOT / 'tools' / 'whole_film_transcript_policy.py'
        spec = importlib.util.spec_from_file_location('whole_g02_policy', modpath)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        result = m.qc_full_film(source_duration_s=60.0, decoded_audio_duration_s=60.0,
            input_sha256_verified=True, whole_file_audio=True, one_transcribe_call=True,
            raw_count=2, provisional_count=1, quarantined_count=1,
            segments=[{'segment_id':'S1','start':1.0,'end':2.0}],
            material_blockers=['S2_ASR_SEMANTIC_UNCERTAIN'])
        self.assertEqual(result['Q02_GATE_STATUS'], 'PASS')
        self.assertIn('S2_ASR_SEMANTIC_UNCERTAIN', result['asr_content_warnings'])

    def test_incomplete_ASR_still_not_pass_and_no_fake_approval(self):
        m=module()
        rows=[{'segment_id':'S1','start':0.0,'end':1.0,'text_original':'Hi.'}]
        result=m.process_transcript_rows(rows,source_duration_s=60.0,source_hash_verified=True,
            full_audio_processed=True,model_transcribe_completed=False,asr_warning_count=0)
        self.assertNotEqual(result['Q02_GATE_STATUS'],'PASS')
        self.assertFalse(result['G03_authorized'])
        self.assertFalse(result['G04_authorized'])

if __name__=='__main__':unittest.main()
