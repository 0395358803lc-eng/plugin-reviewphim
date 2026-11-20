# -*- coding: utf-8 -*-
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class TestApprovalTranslationAudio(unittest.TestCase):
 def test_direct_translation_and_batch_authority(self):
  doc=(R/'references/APPROVAL_TRANSLATION_AUDIO.md').read_text('utf-8')
  for s in ('WORK_PACKAGE_ID','SMART_BATCH_APPROVAL.md','ChatGPT','40 segment','1.000 từ','không xin duyệt cho B002'):
   self.assertIn(s,doc)
 def test_audio_qc_require_upload(self):
  doc=(R/'references/APPROVAL_TRANSLATION_AUDIO.md').read_text('utf-8')
  for s in ('audio_manifest.json','WAITING_FOR_AUDIO_UPLOAD','CHƯA CÓ LINK TẢI TRỰC TIẾP','người dùng upload','HEARD_VERIFIED'):
   self.assertIn(s,doc)
 def test_no_fake_buttons_or_links(self):
  doc=(R/'references/APPROVAL_TRANSLATION_AUDIO.md').read_text('utf-8')
  self.assertIn('không bịa nút',doc)
  self.assertIn('không dùng link',doc)
if __name__=='__main__': unittest.main()
