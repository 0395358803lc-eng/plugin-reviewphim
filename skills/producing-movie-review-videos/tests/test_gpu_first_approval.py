# -*- coding: utf-8 -*-
"""REVIEW_PHIM 1.3.6 GPU-first approval contract (static regression guards)."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return (ROOT / path).read_text(encoding='utf-8')
class GPUFirstApproval(unittest.TestCase):
    def test_entrypoint_requires_gpu_contract(self):
        entry = read('SKILL.md')
        self.assertIn('GPU_FIRST_APPROVAL.md', entry)
        self.assertIn('GPU-FIRST', entry)
        self.assertIn('ưu tiên', entry.lower())
    def test_contract_well_formed(self):
        s = read('references/GPU_FIRST_APPROVAL.md')
        for token in ('GPU-FIRST', 'GPU_READY', 'GPU_NEEDS_SETUP', 'GPU_UNSUPPORTED',
                      'GPU_NOT_VERIFIED', 'GPU_APPROVAL', 'CPU_FALLBACK_APPROVAL',
                      'deviceId', 'JOB_DIR', 'acceptance_criteria', 'QC_STATUS'):
            self.assertIn(token, s, token)
    def test_mandatory_proactive_approval(self):
        s = read('references/GPU_FIRST_APPROVAL.md').lower()
        for token in ('mặc định', 'chủ động', 'nút phê duyệt', 'trước khi',
                      'không tự', 'không được', 'không tự động cài', 'g01–g15'):
            self.assertIn(token, s, token)
    def test_gpu_classes_and_special_cases(self):
        s = read('references/GPU_FIRST_APPROVAL.md').lower()
        for token in ('a01', 'a04', 'a05', 'o01', 'o02', 'o03',
                      'g02', 'g04', 'g08', 'g11', 'nvenc', 'int8_float16', 'cuda',
                      'cublas64_12.dll', 'cudnn', 'vram', 'cpu'):
            self.assertIn(token, s, token)
    def test_separate_approval_and_cpu_fallback(self):
        s = read('references/GPU_FIRST_APPROVAL.md')
        self.assertIn('GPU_NEEDS_SETUP → GPU_APPROVAL', s)
        self.assertIn('GPU_CANDIDATE → GPU_SMOKE → GPU_READY', s)
        self.assertIn('CPU_FALLBACK_APPROVAL', s)
        self.assertIn('Không được biến', s)
    def test_no_silent_system_changes(self):
        s = read('references/GPU_FIRST_APPROVAL.md').lower()
        for token in ('driver', 'path hệ thống', 'registry', 'hash', 'sha-256',
                      'ghi đè', 'quyền riêng', 'chỉ đọc', 'runtime'):
            self.assertIn(token, s, token)
    def test_rtx4060_missing_cublas_must_propose_gpu_before_a05(self):
        s = read('references/GPU_FIRST_APPROVAL.md')
        case = s.split('## 6. Ví dụ kiểm tra bắt buộc')[1]
        self.assertIn('cublas64_12.dll', case)
        self.assertIn('GPU_STATUS=GPU_NEEDS_SETUP', case)
        self.assertIn('Phê duyệt P00-06.A04.GPU.PLAN', case)
        self.assertIn('thay vì nút A05', case)
        self.assertIn('Không tự cài GPU runtime', case)
    def test_cpu_only_and_user_refusal_routes_exist(self):
        s = read('references/GPU_FIRST_APPROVAL.md')
        self.assertIn('tác vụ CPU thuần', s)
        self.assertIn('đã từ chối GPU', s)
        self.assertIn('không phát sinh nút GPU giả', s)
    def test_gpu_and_task_qc_are_independent(self):
        s = read('references/GPU_FIRST_APPROVAL.md')
        self.assertIn('Tách `QC_STATUS`', s)
        self.assertIn('GPU_STATUS', s)
        self.assertIn('cpu_smoke', s)
        self.assertIn('gpu_smoke', s)
        self.assertIn('next_action=GPU_APPROVAL', s)
if __name__ == '__main__': unittest.main(verbosity=2)
