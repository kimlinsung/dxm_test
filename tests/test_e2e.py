"""端到端测试：以 CLI 为入口，离线跑通 输入 → 拆解 → 策略 → 平移 → 报告 全链路。"""

import tempfile
import unittest
from pathlib import Path

from starpick.cli import main
from starpick.ingest import LocalFixtureAdapter, load_persona
from starpick.llm import MockLLM
from starpick.pipeline import format_report, run_pipeline

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class EndToEndTest(unittest.TestCase):
    def test_full_pipeline_matches_golden_judgments(self):
        bundle = LocalFixtureAdapter(FIXTURES / "sample_video").load()
        persona = load_persona(FIXTURES / "persona_office.json")
        report = run_pipeline(bundle, persona, MockLLM(FIXTURES / "golden"))

        self.assertEqual(report.skeleton["hook"]["type"], "反常识宣言")
        self.assertEqual(report.strategy["transferability"], 86)
        self.assertEqual(len(report.skeleton["structure"]), 5)
        self.assertIn("越懒才越高级", report.transplant_md)

    def test_pipeline_is_deterministic_offline(self):
        bundle = LocalFixtureAdapter(FIXTURES / "sample_video").load()
        persona = load_persona(FIXTURES / "persona_office.json")
        r1 = run_pipeline(bundle, persona, MockLLM(FIXTURES / "golden"))
        r2 = run_pipeline(bundle, persona, MockLLM(FIXTURES / "golden"))
        self.assertEqual(format_report(r1), format_report(r2))

    def test_cli_offline_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.md"
            exit_code = main(["--offline", "--out", str(out)])
            self.assertEqual(exit_code, 0)
            text = out.read_text(encoding="utf-8")
            self.assertIn("可平移度：86/100", text)
            self.assertIn("### 分镜表", text)

    def test_transplant_does_not_reuse_source_lines(self):
        """红线回归：平移脚本不得照抄对标台词原句。"""
        bundle = LocalFixtureAdapter(FIXTURES / "sample_video").load()
        persona = load_persona(FIXTURES / "persona_office.json")
        report = run_pipeline(bundle, persona, MockLLM(FIXTURES / "golden"))
        for line in ("越快才越好看", "评论区扣1，关注我，下周拍", "口红当腮红"):
            self.assertNotIn(line, report.transplant_md)


if __name__ == "__main__":
    unittest.main()
