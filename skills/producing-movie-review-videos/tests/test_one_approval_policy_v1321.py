from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT.parents[1]
POLICY = ROOT / 'references' / 'ONE_APPROVAL_START_POLICY_V1321.md'
MAIN = ROOT / 'SKILL.md'
NEW_SKILL = PKG / 'skills' / 'one-click-review-execution' / 'SKILL.md'


def test_one_approval_is_mandatory_in_main_skill():
    m=MAIN.read_text('utf-8')
    assert 'ONE_APPROVAL_START_POLICY_V1321' in m
    assert 'PHÊ DUYỆT VÀ CHẠY GÓI' in m
    assert 'G05_SCRIPT' in m and 'G11B_THUMBNAIL' in m


def test_policy_keeps_human_gates():
    p=POLICY.read_text('utf-8')
    for gate in ['G05_SCRIPT','G07_VOICE','G10_PILOT','G11A_METADATA','G11B_THUMBNAIL','G15_DELETE']:
        assert gate in p
    for token in ['plan_hash','WORK_PACKAGE_ID','APPROVE_PACKAGE','RUNNING','work_package.lock','source SHA']:
        assert token in p
    assert 'không tự chạy nền' in p.lower()


def test_portable_skill_is_discoverable():
    s=NEW_SKILL.read_text('utf-8')
    assert s.startswith('---\nname: one-click-review-execution\n')
    assert 'description:' in s and 'ONE_APPROVAL_START_POLICY_V1321' in s


def test_version_and_default_prompt_compatibility():
    a=json.loads((PKG / 'plugin.json').read_text('utf-8'))
    b=json.loads((PKG / '.codex-plugin' / 'plugin.json').read_text('utf-8'))
    assert a['version'] == b['version'] and tuple(map(int,a['version'].split('.'))) >= (1, 3, 21)
    assert a['name'] == b['name'] == 'review-phim'
    assert a['extensions']['com.openai']['apps'] == './.app.json'
    assert a['extensions']['com.openai']['interface']['defaultPrompt'] == b['interface']['defaultPrompt']
    assert len(a['extensions']['com.openai']['interface']['defaultPrompt']) == 9
