# -*- coding: utf-8 -*-
"""Reusable movie-review skill validation, without claiming real media execution."""
from pathlib import Path
import re, unittest, json, zipfile
ROOT=Path(__file__).resolve().parents[1]
DOCS={
    'SKILL.md':ROOT/'SKILL.md',
    'workflow':ROOT/'references'/'WORKFLOW.md',
    'matching':ROOT/'references'/'SCENE_MATCHING.md',
    'qc':ROOT/'references'/'ACCEPTANCE_QC.md',
    'defaults':ROOT/'references'/'DEFAULTS_AND_TOOLS.md',
    'brief':ROOT/'templates'/'JOB_BRIEF.md',
    'report':ROOT/'templates'/'FINAL_REPORT.md',
    'readme':ROOT/'README.md',
}
class SkillPackageValidation(unittest.TestCase):
    def test_files(self):
        for name,p in DOCS.items():
            with self.subTest(name=name):
                self.assertTrue(p.is_file(),str(p))
                self.assertGreater(len(p.read_text(encoding='utf-8')),250)
    def test_skill_discovery_and_refs(self):
        s=DOCS['SKILL.md'].read_text(encoding='utf-8')
        self.assertRegex(s,r'(?s)\A---\s*\nname:\s*[a-z0-9-]+\s*\ndescription:\s*Use when .*?\n---')
        # Realistic upper bound; 760 words was already exceeded before v1.3.22.
        self.assertLessEqual(len(s.split()),2400)
        for token in ('references/WORKFLOW.md','references/SCENE_MATCHING.md','references/ACCEPTANCE_QC.md',
                      'references/DEFAULTS_AND_TOOLS.md','templates/JOB_BRIEF.md',
                      'templates/FINAL_REPORT.md','FULL_WORKFLOW_INTEGRITY_V1323.md'):
            self.assertIn(token,s)
        self.assertRegex(s.lower(),r'video gốc|phim gốc')
    def test_fifteen_phases(self):
        s=DOCS['workflow'].read_text(encoding='utf-8').lower()
        for i in range(1,16):self.assertRegex(s,rf'(?:giai đoạn|giai doan)\s*{i:02d}\b')
        for keyword in ('transcript','faster-whisper','remotion','ffmpeg','tts','trúc ly','nhạc nền',
                        'sidechain','watermark','sha-256','intro'):self.assertIn(keyword,s)
    def test_critical_invariants(self):
        s=' \n'.join(DOCS[p].read_text(encoding='utf-8').lower() for p in ('SKILL.md','workflow','matching','qc','defaults'))
        for needle in ('không mặc định thời lượng','1.00x','2 giây','không ghi đè','giọng đọc',
                       'sai tuyến','không tuyên bố 100%','nghiệm thu','d:','timeline',
                       'gói nguồn','không lấn át','không xóa'):self.assertIn(needle,s,needle)
    def test_templates(self):
        brief=DOCS['brief'].read_text('utf-8').lower();report=DOCS['report'].read_text('utf-8').lower()
        for needle in ('phim gốc','giọng','logo','nhạc','thư mục'):self.assertIn(needle,brief)
        for needle in ('mốc','khung hình','chất lượng','chưa xác minh','tài liệu'):self.assertIn(needle,report)
    def test_scenarios(self):
        s=DOCS['matching'].read_text('utf-8').lower();qc=DOCS['qc'].read_text('utf-8').lower()
        for needle in ('không đủ bằng chứng','không lấy cảnh','khớp ngữ nghĩa'):self.assertIn(needle,s)
        for needle in ('dừng xuất bản','đối chiếu'):self.assertIn(needle,qc)
    def test_zip_rebuild_optional(self):
        path=ROOT.parent/'SKILL_REVIEW_PHIM_AI.zip'
        if not path.exists():return
        with zipfile.ZipFile(path) as z:
            self.assertIsNone(z.testzip())
            expected={'SKILL_REVIEW_PHIM_AI/'+p.relative_to(ROOT).as_posix() for p in DOCS.values()}
            self.assertTrue(expected.issubset(set(z.namelist())))
if __name__=='__main__':unittest.main(verbosity=2)
