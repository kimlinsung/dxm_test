"""LLM 客户端：真实 API 与离线 Mock 双实现，接口一致。

- AnthropicLLM: 经 stdlib urllib 调用 Claude API（设 ANTHROPIC_API_KEY 后可用）。
- MockLLM:      回放 fixtures/golden 金样输出，零网络、零成本、确定性，
                供 E2E 测试与离线 Demo 复现完整链路。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"

GOLDEN_BY_STAGE = {
    "deconstruct": "p1_skeleton.json",
    "strategize": "p2_strategy.json",
    "transplant": "p3_transplant.md",
}


class LLMError(RuntimeError):
    """模型调用失败。"""


class AnthropicLLM:
    def __init__(self, model: str | None = None, max_tokens: int = 4096) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise LLMError(
                "未设置 ANTHROPIC_API_KEY。离线演示请使用 --offline（MockLLM 回放金样）。"
            )
        self.model = model or os.environ.get("STARPICK_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens

    def complete(self, prompt: str, *, stage: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - 网络分支
            raise LLMError(f"[{stage}] API HTTP {exc.code}: {exc.read().decode()[:200]}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - 网络分支
            raise LLMError(f"[{stage}] 网络错误: {exc.reason}") from exc
        return "".join(b.get("text", "") for b in body.get("content", []))


class MockLLM:
    """按阶段回放金样输出；JSON 阶段刻意包上代码围栏，模拟真实模型行为。"""

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
