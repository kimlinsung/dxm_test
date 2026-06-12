"""五段流水线编排：输入 → 解析 → 拆解(P1) → 注入策略(P2) → 平移(P3)。

可靠性设计（LLM 输出不可信是工程事实）：
- 容错解析：剥离代码围栏与前后闲话、提取最外层 JSON 对象、修复尾逗号；
- 带反馈重试：解析或 schema 校验失败时，把失败原因拼回 Prompt 重试（默认 2 次）；
- 每段产出过校验再进下一段，最终失败带阶段名抛 PipelineError，方便定位。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .ingest import VideoBundle
from .prompts import load_prompt, render
from .schema import SchemaError, validate_skeleton, validate_strategy, validate_transplant

_FENCE = re.compile(r"```[a-zA-Z]*")
_TRAILING_COMMA = re.compile(r",\s*([}\]])")

MAX_RETRIES = 2

_RETRY_JSON = (
    "\n\n## 你上一次的输出被系统拒绝\n原因：{reason}\n"
    "请重新输出：只输出一个合法 JSON 对象，从 {{ 开始到 }} 结束，"
    "不要代码围栏、不要任何解释文字；字符串内部不要使用未转义的英文双引号。"
)
_RETRY_MD = (
    "\n\n## 你上一次的输出被系统拒绝\n原因：{reason}\n"
    "请重新输出完整 Markdown，并确保包含全部必需章节标题。"
)


class PipelineError(RuntimeError):
    """某一阶段产出不可用。"""


@dataclass(frozen=True)
class Report:
    bundle: VideoBundle
    persona: dict
    skeleton: dict
    strategy: dict
    transplant_md: str


def _parse_json(text: str, stage: str) -> dict:
    cleaned = _FENCE.sub("", text)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise PipelineError(f"[{stage}] 输出中未找到 JSON 对象")
    blob = cleaned[start : end + 1]
    try:
        return json.loads(blob)
    except json.JSONDecodeError as exc:
        try:  # 常见小毛病自动修复：尾逗号
            return json.loads(_TRAILING_COMMA.sub(r"\1", blob))
        except json.JSONDecodeError:
            raise PipelineError(f"[{stage}] 输出不是合法 JSON: {exc}") from exc


def _json_stage(llm, prompt: str, *, stage: str, label: str, validate) -> dict:
    feedback = ""
    last: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        raw = llm.complete(prompt + feedback, stage=stage)
        try:
            return validate(_parse_json(raw, label))
        except (PipelineError, SchemaError) as exc:
            last = exc
            feedback = _RETRY_JSON.format(reason=exc)
    raise PipelineError(f"[{label}] 重试 {MAX_RETRIES} 次后仍不合规：{last}")


def _md_stage(llm, prompt: str, *, stage: str, label: str) -> str:
    feedback = ""
    last: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        raw = llm.complete(prompt + feedback, stage=stage)
        try:
            return validate_transplant(raw)
        except SchemaError as exc:
            last = exc
            feedback = _RETRY_MD.format(reason=exc)
    raise PipelineError(f"[{label}] 重试 {MAX_RETRIES} 次后仍不合规：{last}")


def run_pipeline(bundle: VideoBundle, persona: dict, llm) -> Report:
    # P1 拆解员：视频素材 → 爆款骨架卡
    p1 = render(
        load_prompt("p1_deconstructor"),
        meta_json=json.dumps(bundle.meta, ensure_ascii=False, indent=2),
        transcript=bundle.transcript,
        frames=bundle.frames,
    )
    skeleton = _json_stage(llm, p1, stage="deconstruct", label="P1", validate=validate_skeleton)

    # P2 策略师：骨架卡 × 账号人设 → 平移策略
    p2 = render(
        load_prompt("p2_strategist"),
        skeleton_json=json.dumps(skeleton, ensure_ascii=False, indent=2),
        persona_json=json.dumps(persona, ensure_ascii=False, indent=2),
    )
    strategy = _json_stage(llm, p2, stage="strategize", label="P2", validate=validate_strategy)

    # P3 编剧：骨架 + 策略 + 人设 → 可拍的平移脚本
    p3 = render(
        load_prompt("p3_screenwriter"),
        skeleton_json=json.dumps(skeleton, ensure_ascii=False, indent=2),
        strategy_json=json.dumps(strategy, ensure_ascii=False, indent=2),
        persona_json=json.dumps(persona, ensure_ascii=False, indent=2),
    )
    transplant_md = _md_stage(llm, p3, stage="transplant", label="P3")

    return Report(bundle, persona, skeleton, strategy, transplant_md)


def format_report(report: Report) -> str:
    meta = report.bundle.meta
    seg_names = " → ".join(s["name"] for s in report.skeleton["structure"])
    lines = [
        "# StarPick 摘星 · 拆解-平移报告",
        "",
        f"- 对标视频：《{meta['title']}》（{meta['platform']}，♥ {meta['likes']:,}）",
        f"- 我的账号：{report.persona['account_name']}（{report.persona['niche']}）",
        f"- 钩子：{report.skeleton['hook']['type']} ——「{report.skeleton['hook']['line']}」",
        f"- 结构：{seg_names}",
        f"- 可平移度：{report.strategy['transferability']}/100（{report.strategy['rationale']}）",
        "",
        "## 爆款骨架卡（P1）",
        "```json",
        json.dumps(report.skeleton, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 平移策略（P2）",
        "```json",
        json.dumps(report.strategy, ensure_ascii=False, indent=2),
        "```",
        "",
        report.transplant_md.strip(),
        "",
    ]
    return "\n".join(lines)
