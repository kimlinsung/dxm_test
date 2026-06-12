"""LLM 客户端：多供应商真实 API 与离线 Mock，接口一致（complete(prompt, *, stage) -> str）。

支持的供应商（任配一个 Key 即可真跑）：
  - DeepSeek          DEEPSEEK_API_KEY
  - 通义千问(百炼)     DASHSCOPE_API_KEY
  - Kimi(月之暗面)     MOONSHOT_API_KEY
  - OpenAI 及兼容网关  OPENAI_API_KEY（可配 OPENAI_BASE_URL 指向任意兼容端点）
  - Anthropic Claude  ANTHROPIC_API_KEY

模型可用 STARPICK_MODEL 统一覆盖；离线模式 MockLLM 回放 fixtures/golden 金样，
零网络、零成本、确定性，供 E2E 测试与无 Key 演示。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

GOLDEN_BY_STAGE = {
    "deconstruct": "p1_skeleton.json",
    "strategize": "p2_strategy.json",
    "transplant": "p3_transplant.md",
}

# provider -> (base_url, 默认模型, key 环境变量)
OPENAI_COMPAT_PRESETS = {
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat", "DEEPSEEK_API_KEY"),
    "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", "DASHSCOPE_API_KEY"),
    "kimi": ("https://api.moonshot.cn/v1", "moonshot-v1-32k", "MOONSHOT_API_KEY"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini", "OPENAI_API_KEY"),
}

PROVIDERS = ("auto", "anthropic", *OPENAI_COMPAT_PRESETS, "mock")


class LLMError(RuntimeError):
    """模型配置或调用失败。"""


def _post_json(url: str, payload: dict, headers: dict, stage: str) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - 网络分支
        raise LLMError(f"[{stage}] API HTTP {exc.code}: {exc.read().decode()[:300]}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - 网络分支
        raise LLMError(f"[{stage}] 网络错误: {exc.reason}") from exc


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, model: str | None = None, max_tokens: int = 4096) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise LLMError("未设置 ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("STARPICK_MODEL") or "claude-sonnet-4-6"
        self.max_tokens = max_tokens

    def complete(self, prompt: str, *, stage: str) -> str:
        body = _post_json(
            "https://api.anthropic.com/v1/messages",
            {"model": self.model, "max_tokens": self.max_tokens,
             "messages": [{"role": "user", "content": prompt}]},
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            stage,
        )
        return "".join(b.get("text", "") for b in body.get("content", []))


class OpenAICompatLLM:
    """OpenAI Chat Completions 兼容客户端：DeepSeek / 通义 / Kimi / 任意兼容网关。"""

    def __init__(self, provider: str, model: str | None = None) -> None:
        base, default_model, key_env = OPENAI_COMPAT_PRESETS[provider]
        self.name = provider
        self.api_key = os.environ.get(key_env, "")
        if not self.api_key:
            raise LLMError(f"未设置 {key_env}")
        if provider == "openai":
            base = os.environ.get("OPENAI_BASE_URL", base).rstrip("/")
        self.base_url = base
        self.model = model or os.environ.get("STARPICK_MODEL") or default_model

    def complete(self, prompt: str, *, stage: str) -> str:
        body = _post_json(
            f"{self.base_url}/chat/completions",
            {"model": self.model, "temperature": 0.3,
             "messages": [{"role": "user", "content": prompt}]},
            {"authorization": f"Bearer {self.api_key}"},
            stage,
        )
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"[{stage}] 响应结构异常: {str(body)[:300]}") from exc


class MockLLM:
    """按阶段回放金样输出；JSON 阶段刻意包上代码围栏，模拟真实模型行为。"""

    name = "mock"

    def __init__(self, golden_dir: str | Path) -> None:
        self.golden_dir = Path(golden_dir)
        self.calls: list[dict] = []

    def complete(self, prompt: str, *, stage: str) -> str:
        self.calls.append({"stage": stage, "prompt": prompt})
        if stage not in GOLDEN_BY_STAGE:
            raise LLMError(f"MockLLM 不认识的阶段: {stage}")
        text = (self.golden_dir / GOLDEN_BY_STAGE[stage]).read_text(encoding="utf-8")
        if GOLDEN_BY_STAGE[stage].endswith(".json"):
            return f"```json\n{text}\n```"
        return text


def make_llm(provider: str = "auto", *, offline: bool = False, golden_dir: str | Path | None = None):
    """按 provider/环境变量构造客户端。auto 按 Key 存在性依序探测。"""
    if offline or provider == "mock":
        if golden_dir is None:
            raise LLMError("离线模式需要 golden_dir")
        return MockLLM(golden_dir)

    if provider == "anthropic":
        return AnthropicLLM()
    if provider in OPENAI_COMPAT_PRESETS:
        return OpenAICompatLLM(provider)
    if provider != "auto":
        raise LLMError(f"未知 provider: {provider}（可选 {', '.join(PROVIDERS)}）")

    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicLLM()
    for name, (_, _, key_env) in OPENAI_COMPAT_PRESETS.items():
        if os.environ.get(key_env):
            return OpenAICompatLLM(name)
    raise LLMError(
        "未检测到任何 API Key。请设置 DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / "
        "MOONSHOT_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY 之一，"
        "或使用 --offline 离线演示。"
    )
