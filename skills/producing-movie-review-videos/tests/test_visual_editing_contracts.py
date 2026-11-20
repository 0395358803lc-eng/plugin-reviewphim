# -*- coding: utf-8 -*-
"""V01-V35: documentation-first visual-editing gates; not actual film acceptance.

These tests deliberately look for explicit contractual instructions and sample
schema integrity. They do NOT claim any G01-G15 was run on a real movie.
"""
import json
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class VisualEditingContractTests(unittest.TestCase):
    def _assert_contract(self, doc, term):
        path=ROOT/doc
        self.assertTrue(path.is_file(),str(path))
        self.assertIn(term.casefold(),path.read_text(encoding='utf-8').casefold())

    def test_V01_contract(self):
        self._assert_contract('references/WORKFLOW.md', 'visual_source_profile.json')

    def test_V02_contract(self):
        self._assert_contract('references/EVIDENCE_SCHEMA.md', 'subtitle_regions')

    def test_V03_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'dark scene')

    def test_V04_contract(self):
        self._assert_contract('references/FILM_UNDERSTANDING.md', 'shot_type')

    def test_V05_contract(self):
        self._assert_contract('references/FILM_UNDERSTANDING.md', 'motion_verification')

    def test_V06_contract(self):
        self._assert_contract('references/FILM_UNDERSTANDING.md', 'visual_shot_profile')

    def test_V07_contract(self):
        self._assert_contract('references/EVIDENCE_SCHEMA.md', 'storyline')

    def test_V08_contract(self):
        self._assert_contract('references/REVIEW_STORYTELLING.md', 'visual_intent_hints')

    def test_V09_contract(self):
        self._assert_contract('references/REVIEW_STORYTELLING.md', 'sáu bước')

    def test_V10_contract(self):
        self._assert_contract('references/EVIDENCE_SCHEMA.md', 'beat_visual_brief.json')

    def test_V11_contract(self):
        self._assert_contract('references/SCENE_MATCHING.md', 'hard reject')

    def test_V12_contract(self):
        self._assert_contract('references/SCENE_MATCHING.md', 'motion_verification')

    def test_V13_contract(self):
        self._assert_contract('references/SCENE_MATCHING.md', 'cosine')

    def test_V14_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'reuse_reason')

    def test_V15_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', '2,04')

    def test_V16_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'must_preserve_action')

    def test_V17_contract(self):
        self._assert_contract('references/EVIDENCE_SCHEMA.md', 'timeline_out_frame_exclusive')

    def test_V18_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'wav')

    def test_V19_contract(self):
        self._assert_contract('references/EVIDENCE_SCHEMA.md', 'source_duration')

    def test_V20_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'face')

    def test_V21_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'hflip')

    def test_V22_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'upscale')

    def test_V23_contract(self):
        self._assert_contract('references/WORKFLOW.md', 'brand_profile.json')

    def test_V24_contract(self):
        self._assert_contract('references/VISUAL_EDITING.md', 'branding after')

    def test_V25_contract(self):
        self._assert_contract('references/ACCEPTANCE_QC.md', 'scene detection')

    def test_V26_contract(self):
        self._assert_contract('references/ACCEPTANCE_QC.md', 'not_verified')

    def test_V27_contract(self):
        self._assert_contract('references/ACCEPTANCE_QC.md', 'blocking')

    def test_V28_contract(self):
        self._assert_contract('references/EVIDENCE_SCHEMA.md', 'optional')

    def test_V29_contract(self):
        self._assert_contract('references/SESSION_ORCHESTRATION.md', 'không ghi đè')

    def test_V30_contract(self):
        self._assert_contract('references/WORKSPACE_BOOTSTRAP.md', 'chỉ đọc')

    def test_V31_contract(self):
        self._assert_contract('references/SESSION_ORCHESTRATION.md', 'g05 vẫn cần phê duyệt riêng')

    def test_V32_contract(self):
        self._assert_contract('references/SESSION_ORCHESTRATION.md', 'phê duyệt xóa riêng')

    def test_V33_contract(self):
        self._assert_contract('references/DEFAULTS_AND_TOOLS.md', 'không mặc định')

    def test_V34_contract(self):
        self._assert_contract('references/SESSION_ORCHESTRATION.md', 'shot_selection_ready')

    def test_V35_contract(self):
        self._assert_contract('references/SCENE_MATCHING.md', 'candidate')


    def test_v13_example_json_parseable(self):
        schema=(ROOT/'references/EVIDENCE_SCHEMA.md').read_text(encoding='utf-8')
        examples=[json.loads(s) for s in re.findall(r'```json\s*(\{.*?\})\s*```',schema,re.S)]
        self.assertGreaterEqual(len(examples),8)
        self.assertEqual(examples[-1]['issue_id'],'ISSUE-0031')

    def test_g08_gate_not_auto_permission(self):
        text=(ROOT/'references/SESSION_ORCHESTRATION.md').read_text(encoding='utf-8').casefold()
        self.assertIn('shot_selection_ready',text)
        self.assertIn('g09',text)
        self.assertIn('phê duyệt riêng',text)

    def test_no_video_presets_as_defaults(self):
        entry=(ROOT/'SKILL.md').read_text(encoding='utf-8').casefold()
        for token in ('hflip=false','2,04','24 fps','8%'):
            self.assertIn(token,entry)

if __name__=='__main__':unittest.main(verbosity=2)
