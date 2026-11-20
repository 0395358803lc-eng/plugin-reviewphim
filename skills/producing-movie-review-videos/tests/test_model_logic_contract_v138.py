from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=(ROOT/'references/WORKFLOW.md').read_text(encoding='utf-8')
POLICY=(ROOT/'references/MODEL_ROLE_POLICY.md').read_text(encoding='utf-8')
SKILL=(ROOT/'SKILL.md').read_text(encoding='utf-8')

def test_g03_only_chatgpt_direct_translation():
    section=WORKFLOW.split('## Giai đoạn 03')[1].split('## Giai đoạn 04')[0]
    assert 'Có thể dùng AI local hỗ trợ' not in section
    assert 'ChatGPT trực tiếp' in section
    assert 'không dùng model dịch' in section
    assert 'MODEL_ROLE_POLICY.md' in SKILL

def test_optional_model_selection_is_fully_specified_before_install():
    for tag in ['O01','O02','model_id','revision','sha256','quantization','backend','VRAM','JOB_DIR','approval_id']:
        assert tag in POLICY
    assert 'không tự lựa chọn' in POLICY.lower()
    assert 'model_approved' in POLICY
    assert 'MODEL_ROLE_POLICY.md' in SKILL

def test_g04_g08_require_direct_verified_evidence():
    for tag in ['G04','G08','CANDIDATE','VERIFIED_VISUAL','motion_verification','inspected_by_chatgpt','evidence_refs']:
        assert tag in POLICY
    assert 'không tự động' in POLICY
    assert 'SHOT_SELECTION_READY' in POLICY
    assert 'FILM_UNDERSTANDING_READY' in POLICY
