"""Regression contract: public G05 narration never exposes production workflow."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'tools' / 'g05_narrative_only_policy.py'


def policy_module():
    spec = importlib.util.spec_from_file_location('g05_narrative_only_policy', POLICY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicNarrativeOnlyTests(unittest.TestCase):
    def test_rejects_workflow_leaks_seen_in_fatman_original_review(self):
        p = policy_module()
        examples = [
            'Theo phần thoại đã được dịch, Billy gây sức ép lên Christine.',
            'Trong bản dịch cuộc đối thoại ở quầy, nhân viên giải thích địa chỉ.',
            'Các chuỗi hình cho thấy binh sĩ di chuyển qua khói bụi.',
            'Các khung hình được kiểm tra chưa đủ để khẳng định điều đó.',
            'Kịch bản không khẳng định ai đã chết.',
            'Theo transcript, ông già Noel nhận tiền.',
            'Đoạn ASR chưa được xác minh nên không thể kết luận.',
            'ChatGPT đã xem những ảnh này ở bước G04.',
            'Một Q05 sẽ kiểm tra nguồn chứng cứ cho cảnh quay.',
            'Trong những hình ảnh liên tiếp, nhân vật cầm súng.',
            'Như đã được xác minh từ tệp lời thoại, Billy tức giận.',
        ]
        for example in examples:
            with self.subTest(example=example):
                self.assertFalse(p.audit_narration(example)['passed'])

    def test_safe_storytelling_with_no_workflow_terms(self):
        p = policy_module()
        samples = [
            'Chris đứng giữa sân tuyết, đối mặt kẻ đang chĩa súng vào ông.',
            'Billy tức giận khi Christine giành chiến thắng trong cuộc thi khoa học.',
            'Ruth cố động viên Chris vượt qua giai đoạn nhà xưởng gặp khó khăn.',
            'Đối thủ của Chris bị thương nhưng vẫn gắng đứng dậy.',
            'Những lời đe dọa của Billy khiến Christine sợ hãi.',
            'Mặc dù cố giấu nỗi sợ, cậu vẫn không dám rời mắt khỏi ông.',
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertTrue(p.audit_narration(sample)['passed'])

    def test_case_insensitive_and_line_positions(self):
        p = policy_module()
        audit = p.audit_narration('Chris bước vào phòng.\nTHEO TRANSCRIPT, Billy xuất hiện.')
        self.assertFalse(audit['passed'])
        self.assertEqual(audit['issues'][0]['line'], 2)
        self.assertEqual(audit['issues'][0]['category'], 'technical_source')

    def test_gate_requires_both_review_and_tts_to_be_clean(self):
        p = policy_module()
        script = 'Chris và Ruth quyết định giữ lại nhà xưởng.'
        self.assertEqual(p.q05_narrative_gate(script, script)['status'], 'PASS')
        self.assertEqual(p.q05_narrative_gate(script, 'Theo bản dịch, họ giữ xưởng.')['status'], 'BLOCKED')
        self.assertEqual(p.q05_narrative_gate('Theo ASR, Chris ở nhà.', 'Theo ASR, Chris ở nhà.')['status'], 'BLOCKED')

    def test_gate_rejects_text_divergence_even_if_both_clean(self):
        p = policy_module()
        self.assertEqual(p.q05_narrative_gate('Billy đi về nhà.', 'Billy trở về nhà.')['status'], 'BLOCKED')
        self.assertEqual(p.q05_narrative_gate('', '')['status'], 'BLOCKED')

    def test_metadata_is_not_scanned_as_public_narration(self):
        p = policy_module()
        clean = 'Billy tức giận khi thua cuộc thi.'
        notes = {'transcript_sha256': 'a'*64, 'source_flags': ['ASR_WARNING'], 'evidence_status':'QUALIFIED'}
        self.assertTrue(p.q05_narrative_gate(clean, clean, evidence_map=notes)['status']=='PASS')

    def test_plugin_contract_prioritizes_six_steps_and_human_gate(self):
        entry = (ROOT / 'SKILL.md').read_text('utf-8')
        rule = (ROOT / 'references/G05_NARRATIVE_ONLY_V1317.md').read_text('utf-8')
        self.assertIn('G05_NARRATIVE_ONLY_V1317.md', entry)
        self.assertIn('G05.REVIEW.FULL', rule)
        self.assertIn('G05_SCRIPT', rule)
        self.assertIn('Q05', rule)
        self.assertIn('sáu bước', rule)
        self.assertIn('review_evidence_map.json', rule)
        self.assertIn('review_ke_chuyen.txt', rule)
        self.assertIn('review_loi_binh_tts.txt', rule)

if __name__ == '__main__':
    unittest.main(verbosity=2)
