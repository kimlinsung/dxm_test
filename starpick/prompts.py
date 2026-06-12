"""Prompt 模板加载与渲染。

模板放在 prompts/*.md，占位符使用 {{name}}。
渲染后若仍残留未填充的占位符立即报错——Prompt 与代码同样需要被测试约束。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_DIR = ROOT / "prompts"

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


class PromptError(ValueError):
    """模板缺失或占位符未填充。"""


def load_prompt(name: str) -> str:
    path = PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise PromptError(f"模板不存在: {path}")
    return path.read_text(encoding="utf-8")


def render(template: str, **variables: str) -> str:
    def _sub(match: re.Match) -> str:
        key = match.group(1)
        if key not in variables:
            raise PromptError(f"占位符 {{{{{key}}}}} 未提供取值")
        return str(variables[key])

    rendered = _PLACEHOLDER.sub(_sub, template)
    leftover = _PLACEHOLDER.findall(rendered)
    if leftover:
        raise PromptError(f"渲染后仍残留占位符: {leftover}")
    return rendered
