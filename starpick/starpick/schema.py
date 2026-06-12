"""骨架卡 / 平移策略 / 平移脚本的结构校验。

零依赖手写校验：失败时抛出 SchemaError，错误信息带字段路径，
保证 LLM 输出不合约定时在流水线内第一时间暴露，而不是污染下游。
"""

from __future__ import annotations

from typing import Any

SKELETON_REQUIRED = {
    "hook": dict,
    "structure": list,
    "pacing": dict,
    "emotion_curve": list,
    "retention_devices": list,
    "cta": dict,
}

STRATEGY_REQUIRED = {
    "transferability": int,
    "rationale": str,
    "keep": list,
    "replace": list,
    "red_lines": list,
}

TRANSPLANT_REQUIRED_SECTIONS = [
    "口播脚本",
    "分镜表",
    "拍摄清单",
    "备选钩子",
    "发布建议",
]


class SchemaError(ValueError):
    """LLM 输出不符合约定结构。"""


def _require(data: dict, spec: dict[str, type], where: str) -> None:
    if not isinstance(data, dict):
        raise SchemaError(f"{where}: 期望 JSON 对象，得到 {type(data).__name__}")
    for key, typ in spec.items():
        if key not in data:
            raise SchemaError(f"{where}.{key}: 缺失必填字段")
        if not isinstance(data[key], typ):
            raise SchemaError(
                f"{where}.{key}: 期望 {typ.__name__}，得到 {type(data[key]).__name__}"
            )


def validate_skeleton(card: Any) -> dict:
    """校验 P1 拆解员产出的「爆款骨架卡」。"""
    _require(card, SKELETON_REQUIRED, "skeleton")

    hook = card["hook"]
    for key in ("type", "line", "start", "end"):
        if key not in hook:
            raise SchemaError(f"skeleton.hook.{key}: 缺失必填字段")
    if not (0 <= hook["start"] < hook["end"]):
        raise SchemaError("skeleton.hook: start/end 秒数非法")

    if not card["structure"]:
        raise SchemaError("skeleton.structure: 至少包含一个段落")
    for i, seg in enumerate(card["structure"]):
        for key in ("name", "start", "end", "purpose"):
            if key not in seg:
                raise SchemaError(f"skeleton.structure[{i}].{key}: 缺失必填字段")

    return card


def validate_strategy(strategy: Any) -> dict:
    """校验 P2 策略师产出的「平移策略」。"""
    _require(strategy, STRATEGY_REQUIRED, "strategy")

    score = strategy["transferability"]
    if not 0 <= score <= 100:
        raise SchemaError(f"strategy.transferability: 须在 0-100 之间，得到 {score}")

    for i, item in enumerate(strategy["replace"]):
        for key in ("element", "from", "to", "reason"):
            if key not in item:
                raise SchemaError(f"strategy.replace[{i}].{key}: 缺失必填字段")

    return strategy


def validate_transplant(markdown: str) -> str:
    """校验 P3 编剧产出的「平移脚本」必备章节齐全。"""
    missing = [s for s in TRANSPLANT_REQUIRED_SECTIONS if s not in markdown]
    if missing:
        raise SchemaError(f"transplant: 缺失章节 {missing}")
    return markdown
