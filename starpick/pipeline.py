"""五段流水线编排：输入 → 解析 → 拆解(P1) → 注入策略(P2) → 平移(P3)。

每一段的产出都先过 schema 校验再进入下一段，
任何一段失败都会带着阶段名抛出 PipelineError，方便定位。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .ingest import VideoBundle
from .prompts import load_prompt, render
from .schema import validate_skeleton, validate_strategy, validate_transplant

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


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
    cleaned = _FENCE.sub("", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise PipelineError(f"[{stage}] 输出不是合法 JSON: {exc}") from exc


def run_pipeline(bundle: VideoBundle, persona: dict, llm) -> Report:
    # P1 拆解员：视频素材 → 爆款骨架卡
    p1 = render(
        load_prompt("p1_deconstructor"),
        meta_json=json.dumps(bundle.meta, ensure_ascii=False, indent=2),
        transcript=bundle.transcript,
        frames=bundle.frames,
    )
    skeleton = validate_skeleton(_parse_json(llm.complete(p1, stage="deconstruct"), "P1"))

    # P2 策略师：骨架卡 × 账号人设 → 平移策略
    p2 = render(
        load_prompt("p2_strategist"),
        skeleton_json=json.dumps(skeleton, ensure_ascii=False, indent=2),
        persona_json=json.dumps(persona, ensure_ascii=False, indent=2),
    )
    strategy = validate_strategy(_parse_json(llm.complete(p2, stage="strategize"), "P2"))

    # P3 编剧：骨架 + 策略 + 人设 → 可拍的平移脚本
    p3 = render(
        load_prompt("p3_screenwriter"),
        skeleton_json=json.dumps(skeleton, ensure_ascii=False, indent=2),
        strategy_json=json.dumps(strategy, ensure_ascii=False, indent=2),
        persona_json=json.dumps(persona, ensure_ascii=False, indent=2),
    )
    transplant_md = validate_transplant(llm.complete(p3, stage="transplant"))

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
