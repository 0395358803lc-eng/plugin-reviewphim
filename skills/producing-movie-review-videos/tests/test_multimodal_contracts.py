# -*- coding: utf-8 -*-
"""Fifteen approved scenario contracts (T01-T15) for documentation-driven REVIEW_PHIM 1.2.0.

These are *static governance/contract checks*, not a claim that film analysis,
remote visual understanding or render has been executed on a real movie.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class MultimodalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = read("SKILL.md").lower()
        cls.flow = read("references/WORKFLOW.md").lower()
        cls.understanding = read("references/FILM_UNDERSTANDING.md").lower()
        cls.story = read("references/REVIEW_STORYTELLING.md").lower()
        cls.schema = read("references/EVIDENCE_SCHEMA.md")
        cls.matching = read("references/SCENE_MATCHING.md").lower()
        cls.qc = read("references/ACCEPTANCE_QC.md").lower()
        cls.session = read("references/SESSION_ORCHESTRATION.md").lower()
        cls.workspace = read("references/WORKSPACE_BOOTSTRAP.md").lower()

    def test_T01_silent_event_is_indexed_and_reviewed(self):
        self.assertIn("cảnh không lời", self.understanding)
        self.assertIn("visual_only_verified", self.schema.lower())
        self.assertIn("g04", self.story)

    def test_T02_wrong_actor_does_not_receive_verification(self):
        self.assertIn("không coi lời thoại", self.understanding)
        self.assertIn("rejected", self.matching)

    def test_T03_two_distinct_orders_are_required(self):
        self.assertIn("on_screen_order", self.schema)
        self.assertIn("chronological_events", self.schema)
        self.assertIn("on_screen_order", self.story)

    def test_T04_frame_alone_cannot_prove_motion(self):
        self.assertIn("một frame", self.understanding)
        self.assertIn("chuỗi", self.understanding)
        self.assertIn("motion_clip", self.schema)

    def test_T05_optional_local_vision_and_real_image_read(self):
        self.assertIn("không mặc định cài", self.understanding)
        self.assertIn("chatgpt", self.understanding)
        self.assertIn("không giả", self.understanding)

    def test_T06_asr_out_of_duration_is_flagged(self):
        self.assertIn("vượt duration", self.flow)
        self.assertIn("asr_flags", self.schema)

    def test_T07_external_fact_must_be_verified(self):
        self.assertIn("external_fact", self.story)
        self.assertIn("nguồn", self.story)
        self.assertIn("external_source", self.schema)

    def test_T08_beat_actor_mismatch_rejected(self):
        self.assertIn("sai nhân vật", self.matching)
        self.assertIn("rejected", self.matching)

    def test_T09_approval_and_gate_enforced(self):
        self.assertIn("g05 vẫn cần phê duyệt riêng", self.session)
        self.assertIn("film_understanding_ready", self.session)
        self.assertIn("không tự", self.session)

    def test_T10_workspace_boundaries_and_caches(self):
        self.assertIn("review_phim_workspace", self.workspace)
        for key in ("pip_cache_dir", "playwright_browsers_path", "hf_home"):
            self.assertIn(key, self.session)
        self.assertIn("ổ c:", self.session)

    def test_T11_resume_without_overwrite(self):
        self.assertIn("không ghi đè", self.workspace)
        self.assertIn("checkpoint", self.understanding)

    def test_T12_no_default_brand_voice_or_length(self):
        self.assertIn("không mặc định thời lượng", self.entry)
        self.assertIn("không tự dùng logo tua phim có gu", self.session)
        self.assertIn("1.00x", self.flow)

    def test_T13_batched_frame_coverage_and_checkpoint(self):
        self.assertIn("batch", self.understanding)
        self.assertIn("checkpoint", self.understanding)
        self.assertIn("bao phủ", self.understanding)

    def test_T14_disconnect_not_faked_and_resumable(self):
        self.assertIn("mất kết nối", self.session)
        self.assertIn("không tuyên bố", self.session)

    def test_T15_core_unverified_blocks_review(self):
        self.assertIn("blocked", self.understanding)
        self.assertIn("không đề xuất chạy g05", self.session)

    def test_six_story_steps_in_order(self):
        sequence = (
            "chọn mở đầu tạo tò mò", "giới thiệu nhân vật và hoàn cảnh",
            "kể sự kiện bằng hành động và nguyên nhân",
            "đẩy xung đột, diễn giải cảm xúc có căn cứ",
            "tạo câu hỏi và chuyển tiếp sang biến cố kế tiếp",
            "tập trung cao trào và giải quyết câu chuyện"
        )
        positions = [self.story.index(text) for text in sequence]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("bối cảnh → hành động → nguyên nhân/động cơ", self.story)

    def test_15_stage_headers_and_qc_types(self):
        phases = re.findall(r"^## Giai đoạn (\d\d)\b", read("references/WORKFLOW.md"), re.M)
        self.assertEqual(phases, [f"{i:02d}" for i in range(1, 16)])
        for token in ("film_understanding_ready", "review_story_ready", "đạt kỹ thuật", "đạt nội dung"):
            self.assertIn(token, self.qc)

    def test_schema_examples_are_json_and_use_real_fields(self):
        snippets = re.findall(r"```json\s*(\{.*?\})\s*```", self.schema, flags=re.S)
        self.assertGreaterEqual(len(snippets), 3)
        d = [json.loads(s) for s in snippets]
        self.assertIn("scene_id", d[0]); self.assertIn("frames", d[0])
        self.assertIn("event_id", d[1]); self.assertIn("evidence", d[1])
        self.assertIn("review_text_range", d[2]); self.assertIn("claim_type", d[2])

    def test_dependent_paths_and_references_exist(self):
        refs = re.findall(r"\]\((references/[^)]+|templates/[^)]+)\)", read("SKILL.md"))
        self.assertGreaterEqual(len(refs), 7)
        for f in refs:
            self.assertTrue((ROOT/f).is_file(), f)


if __name__ == "__main__":
    unittest.main(verbosity=2)
