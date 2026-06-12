import unittest

from starpick.prompts import PromptError, load_prompt, render


class PromptTemplateTest(unittest.TestCase):
    def test_all_three_templates_load(self):
        for name in ("p1_deconstructor", "p2_strategist", "p3_screenwriter"):
            self.assertGreater(len(load_prompt(name)), 200, name)

    def test_missing_template_raises(self):
        with self.assertRaises(PromptError):
            load_prompt("p4_not_exist")

    def test_render_fills_placeholders(self):
        out = render("对标《{{title}}》的钩子是 {{hook}}", title="早八妆", hook="反常识")
        self.assertEqual(out, "对标《早八妆》的钩子是 反常识")

    def test_render_rejects_missing_variable(self):
        with self.assertRaisesRegex(PromptError, "hook"):
            render("钩子是 {{hook}}")

    def test_templates_declare_output_contract(self):
        # P1/P2 必须约定 JSON 输出，P3 必须约定章节结构——契约写进模板并被测试钉死
        self.assertIn("只输出一个 JSON 对象", load_prompt("p1_deconstructor"))
        self.assertIn("只输出一个 JSON 对象", load_prompt("p2_strategist"))
        self.assertIn("### 分镜表", load_prompt("p3_screenwriter"))

    def test_templates_forbid_copying_lines(self):
        self.assertIn("禁止复用对标视频的任何台词原句", load_prompt("p3_screenwriter"))


if __name__ == "__main__":
    unittest.main()
