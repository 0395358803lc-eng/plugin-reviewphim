import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SKILL=Path(__file__).resolve().parents[1]

def test_manifests_keep_identity_app_and_version():
    root=json.loads((ROOT/'plugin.json').read_text(encoding='utf-8'))
    legacy=json.loads((ROOT/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    assert root['name']==legacy['name']=='review-phim'
    assert root['version']==legacy['version']=='1.3.26'
    assert root['extensions']['com.openai']['apps']==legacy['apps']=='./.app.json'
    assert root['extensions']['com.openai']['interface']==legacy['interface']
    assert len(root['extensions']['com.openai']['interface']['defaultPrompt'])==9
    assert root['$schema']=='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'

def test_new_stage_policy_referenced_by_main_skill():
    s=(SKILL/'SKILL.md').read_text(encoding='utf-8')
    for name in ['YOUTUBE_METADATA_POLICY_V1319.md','THUMBNAIL_INTRO_POLICY_V1319.md','INTRO_CARD_INTEGRATION_V1319.md']:
        assert name in s and (SKILL/'references'/name).is_file()
    for name in ['G05_WEB_STORY_CROSSCHECK_V1318','G05_NARRATIVE_ONLY_V1317','SIMPLE_G02_TEXT_QC_V1316','ATOMIC_STAGES_V1315','WORKFLOW_CONSISTENCY_V1312']:
        assert name in s
