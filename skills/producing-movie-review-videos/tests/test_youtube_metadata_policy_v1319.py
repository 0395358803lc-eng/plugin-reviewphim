import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('yt',ROOT/'tools/youtube_metadata_policy.py')
yt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yt)


def test_title_valid_and_deduped():
    titles=['[REVIEW PHIM] Một cuộc đào thoát bất ngờ', 'Phim trinh thám: Người biến mất', 'Cái kết không ai ngờ tới']
    result=yt.validate_metadata({'candidate_titles':titles,'description':'Câu chuyện về những lựa chọn khó khăn. #reviewphim','title_selected':titles[0]})
    assert result['ready'] and result['title_sha256'] and result['issues']==[]


def test_misleading_or_missing_title_is_not_auto_selected():
    result=yt.validate_metadata({'candidate_titles':['Tiêu đề A','Tiêu đề B','Tiêu đề C'],'title_selected':'Tiêu đề D','description':'Xem video nhé'})
    assert not result['ready'] and 'TITLE_NOT_CANDIDATE' in result['issues']


def test_long_or_duplicate_titles_fail():
    result=yt.validate_metadata({'candidate_titles':['x'*101, 'Một', 'Một'],'title_selected':'Một','description':'Nội dung'})
    assert not result['ready'] and 'INVALID_CANDIDATES' in result['issues']


def test_human_approval_requires_exact_hash():
    title='[REVIEW PHIM] Cuộc hành trình'
    digest=yt.title_digest(title)
    assert yt.approved_title(title,{'gate':'G11A_METADATA','approval_ref':'user-1','title_sha256':digest})
    assert not yt.approved_title(title,{'gate':'G11A_METADATA','approval_ref':'user-1','title_sha256':'0'*64})
