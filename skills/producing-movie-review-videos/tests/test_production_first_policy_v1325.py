from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
PLUGIN=R.parents[1]

def read(path):return (R/path).read_text(encoding='utf-8')

def test_one_canonical_policy_and_main_routing():
    p=read('references/PRODUCTION_FIRST_AUTONOMOUS_V1325.md')
    skill=read('SKILL.md')
    assert 'PRODUCTION_FIRST_AUTONOMOUS_V1325.md' in skill
    assert 'project_flow_v1325.py' in skill
    for t in ('PRODUCTION_FIRST_V1325','FINAL_REVIEW','REVISION_REQUESTED','ACCEPTED',
              'WAITING_USER','DONE','OUTPUT_EXISTS','G15_DELETE','G11B',
              'không dùng Q01–Q15','Remote Desktop Commander','không tự chạy nền'):
        assert t.lower() in p.lower(),t

def test_legacy_documents_marked_nonblocking_for_new_mode():
    for name in ('references/FULL_WORKFLOW_INTEGRITY_V1323.md','references/G04_G05_FAST_TRACK_V1322.md',
                 'references/MICROTASK_ORCHESTRATION.md','references/MANUAL_THUMBNAIL_HANDOFF_V1324.md',
                 'references/THUMBNAIL_INTRO_POLICY_V1319.md'):
        content=read(name)
        assert 'PRODUCTION_FIRST_V1325' in content[:1150],name

def test_one_click_uses_new_hinge_progression():
    s=(PLUGIN/'skills/one-click-review-execution/SKILL.md').read_text(encoding='utf-8')
    assert 'PRODUCTION_FIRST_V1325' in s
    assert 'project_flow_v1325.py' in s
    assert 'QC=PASS' in s  # historical mode not deleted


def test_manifest_compatibility_and_no_default_prompt_loss():
    root=json.loads((PLUGIN/'plugin.json').read_text(encoding='utf-8'))
    legacy=json.loads((PLUGIN/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    assert root['version']==legacy['version']=='1.3.26'
    assert root['name']==legacy['name']=='review-phim'
    assert root['extensions']['com.openai']['apps']==legacy['apps']=='./.app.json'
    assert len(root['extensions']['com.openai']['interface']['defaultPrompt'])==9
    assert root['extensions']['com.openai']['interface']==legacy['interface']
