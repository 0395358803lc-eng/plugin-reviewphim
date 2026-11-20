# -*- coding: utf-8 -*-
"""P00-5 reused-workspace safety/approval static contract tests."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def doc(path): return (ROOT/path).read_text(encoding='utf-8')

class WorkspaceReusePolicyContract(unittest.TestCase):
    def test_entrypoint_and_order(self):
        s=doc('SKILL.md')
        self.assertIn('WORKSPACE_REUSE_POLICY.md',s)
        self.assertLess(s.index('KIỂM TRA PHẦN CỨNG MÁY CHỦ'),s.index('TRÌNH DANH MỤC CÀI ĐẶT CHUẨN'))
        self.assertIn('REVIEW_PHIM_WORKSPACE',s)
    def test_scoped_roots_and_device(self):
        p=doc('references/WORKSPACE_REUSE_POLICY.md')
        for k in ('cùng máy','deviceId','root','chỉ đọc','junction','canonical','không quét cả ổ','Program Files'):
            self.assertIn(k.casefold(),p.casefold())
    def test_all_ids_in_catalog(self):
        c=doc('references/INSTALLATION_CATALOG.md')
        for item in [f'A{i:02}' for i in range(1,9)]+[f'O{i:02}' for i in range(1,4)]:
            self.assertIn('| '+item+' |',c)
    def test_states_and_approvals(self):
        p=doc('references/WORKSPACE_REUSE_POLICY.md')
        for k in ('REUSE_READY','FOUND_NOT_VERIFIED','INCOMPATIBLE','MISSING','BLOCKED','Phê duyệt dùng lại ID','P00-06.REUSE','smoke test','phê duyệt kiểm chứng riêng'):
            self.assertIn(k,p)
    def test_safe_runtime_isolation(self):
        p=doc('references/WORKSPACE_REUSE_POLICY.md')
        for k in ('PYTHONDONTWRITEBYTECODE','cwd=JOB_DIR','PIP_CACHE_DIR','PLAYWRIGHT_BROWSERS_PATH','REUSE_SOURCE','không ghi','không trộn package'):
            self.assertIn(k.casefold(),p.casefold())
    def test_never_reuse_job_artifacts(self):
        p=doc('references/WORKSPACE_REUSE_POLICY.md')
        for k in ('transcript','checkpoint','output','không dùng lại kết quả'):
            self.assertIn(k.casefold(),p.casefold())
    def test_not_run_code_during_discovery(self):
        h=doc('references/HARDWARE_PROFILE.md')
        self.assertIn('không chạy',h.casefold())
        self.assertIn('phê duyệt smoke test riêng',h.casefold())
    def test_no_automatic_install(self):
        c=doc('references/INSTALLATION_CATALOG.md')
        self.assertIn('Chưa duyệt thì chỉ được trình kế hoạch',c)
        self.assertIn('không cài lại',c)
    def test_preexisting_workspace_unchanged(self):
        w=doc('references/WORKSPACE_BOOTSTRAP.md')
        self.assertIn('chỉ đọc',w)
        self.assertIn('Không cần chép/di chuyển runtime',w)
    def test_gpu_first_not_bypassed(self):
        s=doc('SKILL.md')
        self.assertIn('GPU_FIRST_APPROVAL.md',s)
        self.assertIn('CPU smoke không chứng minh GPU',s)
if __name__ == '__main__': unittest.main(verbosity=2)
