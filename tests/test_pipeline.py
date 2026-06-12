import unittest
from pathlib import Path

from starpick.ingest import IngestError, LocalFixtureAdapter, load_persona
from starpick.llm import MockLLM
from starpick.pipeline import PipelineError, _parse_json, format_report, run_pipeline

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


def make_inputs():
    bundle = LocalFixtureAdapter(FIXTURES / "sample_video").load()
    persona = load_persona(FIXTURES / "persona_office.json")
    return bundle, persona


class IngestTest(unittest.TestCase):
    def test_fixture_loads_all_materials(self):
        bundle, _ = make_inputs()
        self.assertEqual(bundle.meta["likes"], 124000)
        self.assertIn("[00:00-00:03]", bundle.transcript)
        self.assertIn("怼脸", bundle.frames)

    def test_missing_material_rejected(self):
        with self.assertRaisesRegex(IngestError, "缺少素材"):
            LocalFixtureAdapter(FIXTURES).load()


class PipelineUnitTest(unittest.TestCase):
    def test_stages_called_in_order(self):
        bundle, persona = make_inputs()
        llm = MockLLM(FIXTURES / "golden")
        run_pipeline(bundle, persona, llm)
        self.assertEqual(
            [c["stage"] for c in llm.calls],
            ["deconstruct", "strategize", "transplant"],
        )

    def test_persona_injected_into_downstream_prompts(self):
        bundle, persona = make_inputs()
        llm = MockLLM(FIXTURES / "golden")
        run_pipeline(bundle, persona, llm)
        p2_prompt = llm.calls[1]["prompt"]
        p3_prompt = llm.calls[2]["prompt"]
        self.assertIn("林岛的工位美妆", p2_prompt)
        self.assertIn("不碰医美/整容话题", p3_prompt)

    def test_code_fenced_json_is_parsed(self):
        parsed = _parse_json('```json\n{"a": 1}\n```', "P1")
        self.assertEqual(parsed, {"a": 1})

    def test_invalid_json_raises_with_stage_name(self):
        with self.assertRaisesRegex(PipelineError, r"\[P2\]"):
            _parse_json("这不是 JSON", "P2")

    def test_report_contains_all_sections(self):
        bundle, persona = make_inputs()
        report = run_pipeline(bundle, persona, MockLLM(FIXTURES / "golden"))
        text = format_report(report)
        for section in ("爆款骨架卡（P1）", "平移策略（P2）", "口播脚本", "分镜表", "拍摄清单"):
            self.assertIn(section, text)


if __name__ == "__main__":
    unittest.main()
