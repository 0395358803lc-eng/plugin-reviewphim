# -*- coding: utf-8 -*-
"""V1.3.7 source-level contracts. These tests do not imply a video was analyzed."""
import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PLUGIN_SKILLS = BASE.parent

class EditorialSkillIntegration(unittest.TestCase):
    def test_skills_discoverable(self):
        for name in ('analyze-video-editing','editing-montage','find-broll'):
            with self.subTest(name=name):
                content=(PLUGIN_SKILLS/name/'SKILL.md').read_text('utf-8')
                self.assertTrue(content.startswith('---\nname: '+name+'\n'))
                self.assertIn('REVIEW_PHIM',content)
                self.assertIn('NEEDS_FIX',content)
                self.assertIn('NOT_VERIFIED',content)

    def test_dispatcher_preserves_approvals(self):
        s=(BASE/'SKILL.md').read_text('utf-8')
        for name in ('analyze-video-editing','editing-montage','find-broll'):
            self.assertIn(name,s)
        for contract in ('GPU_FIRST_APPROVAL','MICROTASK_ACCEPTANCE_REPAIR',
                         'MICROTASK_ORCHESTRATION','INSTALLATION_CATALOG',
                         'EDITORIAL_SKILLS_INTEGRATION'):
            self.assertIn(contract,s)

    def test_install_scope(self):
        s=(BASE/'references/EDITORIAL_SKILLS_INTEGRATION.md').read_text('utf-8')
        self.assertIn('Không thêm ID bắt buộc',s)
        for identifier in ('A01','A03','A08','A06','O01','O02','O03'):
            self.assertIn(identifier,s)
        self.assertIn('Không tự tải',s)
        self.assertIn('G14',s)

    def test_no_external_auto_install(self):
        p=BASE/'references/EDITORIAL_SKILLS_INTEGRATION.md'
        s=p.read_text('utf-8')
        self.assertIn('không được tự cài/tự chạy', (BASE/'SKILL.md').read_text('utf-8'))
        self.assertIn('không dùng `GEMINI_API_KEY`',s)

if __name__=='__main__': unittest.main(verbosity=2)
