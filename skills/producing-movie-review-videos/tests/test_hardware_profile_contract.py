# -*- coding: utf-8 -*-
"""P00-5: hardware first, then scoped previous-workspace inventory."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def r(x): return (ROOT/x).read_text(encoding='utf-8').casefold()
class HardwareProfileContract(unittest.TestCase):
    def test_order(self):
        s=r('SKILL.md'); sess=r('references/SESSION_ORCHESTRATION.md')
        self.assertLess(s.index('chọn thư mục chứa logo'),s.index('kiểm tra phần cứng máy chủ'))
        self.assertLess(s.index('kiểm tra phần cứng máy chủ'),s.index('trình danh mục cài đặt chuẩn'))
        self.assertLess(sess.index('5. **kiểm tra phần cứng'),sess.index('6. **trình danh sách cài đặt'))
    def test_fields_and_scoped_inventory(self):
        h=r('references/HARDWARE_PROFILE.md')
        for k in ('cpu','ram','gpu','vram','windows','disk','deviceid','unknown','chỉ đọc','re​view_phim_workspace'.replace('\u200b',''),'batch','threads'):
            self.assertIn(k,h)
    def test_11_ids_unchanged(self):
        c=r('references/INSTALLATION_CATALOG.md')
        for id in [f'a{i:02d}' for i in range(1,9)]+[f'o{i:02d}' for i in range(1,4)]:self.assertIn('| '+id+' |',c)
    def test_no_unapproved_execution(self):
        h=r('references/HARDWARE_PROFILE.md')
        self.assertIn('không chạy',h)
        self.assertIn('smoke test riêng',h)
    def test_job_brief_order(self):
        a=r('templates/JOB_BRIEF.md')
        self.assertLess(a.index('p01-hw'),a.index('p02'))
if __name__=='__main__':unittest.main(verbosity=2)
