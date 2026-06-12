import unittest
from pathlib import Path
from unittest.mock import patch

from starpick.llm import (
    AnthropicLLM,
    LLMError,
    MockLLM,
    OpenAICompatLLM,
    make_llm,
)

GOLDEN = Path(__file__).resolve().parent.parent / "fixtures" / "golden"

NO_KEYS = {
    "ANTHROPIC_API_KEY": "", "DEEPSEEK_API_KEY": "", "DASHSCOPE_API_KEY": "",
    "MOONSHOT_API_KEY": "", "OPENAI_API_KEY": "", "STARPICK_MODEL": "",
}


class LLMFactoryTest(unittest.TestCase):
    def test_offline_returns_mock(self):
        llm = make_llm("auto", offline=True, golden_dir=GOLDEN)
        self.assertIsInstance(llm, MockLLM)

    def test_auto_without_any_key_raises_with_guidance(self):
        with patch.dict("os.environ", NO_KEYS):
            with self.assertRaisesRegex(LLMError, "offline"):
                make_llm("auto")

    def test_auto_picks_deepseek_when_key_present(self):
        env = {**NO_KEYS, "DEEPSEEK_API_KEY": "sk-test"}
        with patch.dict("os.environ", env):
            llm = make_llm("auto")
        self.assertIsInstance(llm, OpenAICompatLLM)
        self.assertEqual(llm.name, "deepseek")
        self.assertEqual(llm.model, "deepseek-chat")

    def test_auto_prefers_anthropic_first(self):
        env = {**NO_KEYS, "ANTHROPIC_API_KEY": "sk-a", "DEEPSEEK_API_KEY": "sk-d"}
        with patch.dict("os.environ", env):
            self.assertIsInstance(make_llm("auto"), AnthropicLLM)

    def test_explicit_provider_without_key_raises(self):
        with patch.dict("os.environ", NO_KEYS):
            with self.assertRaisesRegex(LLMError, "DASHSCOPE_API_KEY"):
                make_llm("qwen")

    def test_starpick_model_overrides_default(self):
        env = {**NO_KEYS, "MOONSHOT_API_KEY": "sk-m", "STARPICK_MODEL": "moonshot-v1-128k"}
        with patch.dict("os.environ", env):
            llm = make_llm("kimi")
        self.assertEqual(llm.model, "moonshot-v1-128k")

    def test_openai_base_url_respected(self):
        env = {**NO_KEYS, "OPENAI_API_KEY": "sk-o", "OPENAI_BASE_URL": "https://my.gateway/v1/"}
        with patch.dict("os.environ", env):
            llm = make_llm("openai")
        self.assertEqual(llm.base_url, "https://my.gateway/v1")

    def test_unknown_provider_rejected(self):
        with self.assertRaisesRegex(LLMError, "未知 provider"):
            make_llm("gpt5-super")


if __name__ == "__main__":
    unittest.main()
