from test_manual_thumbnail_handoff_v1324 import get_module,make_png,inputs


def test_production_first_manual_copy_checks_file_not_artistic_qc(tmp_path):
    m=get_module();make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    _,title,approval,_=inputs(tmp_path)
    # Production First explicitly omits image/content QC. Still requires a real
    # user placement confirmation, title binding, file format and SHA-256.
    report=m.verify_drop(tmp_path,title=title,approval=approval,visual={},
                        image_name='youtube_thumbnail.png',production_first=True)
    assert report['status']=='FILE_ACCEPTED'
    assert report['ready_for_q11b_qc'] is False
    assert report['image_sha256']
    assert report['qc_pass_claimed'] is False


def test_production_first_missing_user_confirmation_still_blocks(tmp_path):
    m=get_module();make_png(tmp_path/'assets'/'youtube_thumbnail.png')
    _,title,approval,_=inputs(tmp_path)
    report=m.verify_drop(tmp_path,title=title,approval={**approval,'user_confirmed_placement':False},
                        visual={},image_name='youtube_thumbnail.png',production_first=True)
    assert report['status']=='WAITING_FOR_HUMAN_APPROVAL'
