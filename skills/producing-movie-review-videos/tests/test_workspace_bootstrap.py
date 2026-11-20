# -*- coding: utf-8 -*-
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def r(s):return (ROOT/s).read_text(encoding='utf-8').casefold()
class WorkspaceBootstrapContract(unittest.TestCase):
    def test_workspace_structure(self):
        s=r('references/WORKSPACE_BOOTSTRAP.md')
        for k in ('analysis/','review/','beats/','voice/','shots/','timeline/','music/','assets/','out/','qc/','logs/','temp/','cache/','models/','tools/','.venv/','npm-cache/','node_modules/'):
            self.assertIn(k,s)
    def test_scaffold_does_not_install_or_copy(self):
        s=r('references/WORKSPACE_BOOTSTRAP.md')
        for k in ('không phải g01','không yêu cầu phê duyệt cài đặt','không cần chép/di chuyển runtime','chỉ đọc/chưa thay đổi dữ liệu','không ghi đè'):
            self.assertIn(k,s)
    def test_old_workspace_readonly(self):
        s=r('references/WORKSPACE_REUSE_POLICY.md')
        self.assertIn('không hardlink/symlink/copy tự động',s)
        self.assertIn('read-only',s)
if __name__=='__main__':unittest.main(verbosity=2)
