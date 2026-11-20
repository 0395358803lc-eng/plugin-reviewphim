# -*- coding: utf-8 -*-
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def r(s):return (ROOT/s).read_text(encoding='utf-8').casefold()
class FixedInstallationContract(unittest.TestCase):
    def test_fixed_catalog(self):
        c=r('references/INSTALLATION_CATALOG.md')
        for id in [f'a{i:02d}' for i in range(1,9)]+[f'o{i:02d}' for i in range(1,4)]:self.assertIn('| '+id+' |',c)
    def test_reuse_overrides_install_every_job(self):
        for path in ('SKILL.md','references/INSTALLATION_CATALOG.md','references/SESSION_ORCHESTRATION.md'):
            s=r(path)
            self.assertIn('reuse',s,path)
            self.assertIn('phê duyệt',s,path)
        self.assertIn('không cài lại',r('references/INSTALLATION_CATALOG.md'))
    def test_no_global_fallback(self):
        c=r('references/WORKSPACE_REUSE_POLICY.md')
        for k in ('path','program files','cùng máy','read-only','chỉ đọc','không quét cả ổ'):
            self.assertIn(k,c)
    def test_no_install_without_approval(self):
        self.assertIn('chưa duyệt thì chỉ được trình kế hoạch',r('references/INSTALLATION_CATALOG.md'))
if __name__=='__main__':unittest.main(verbosity=2)
