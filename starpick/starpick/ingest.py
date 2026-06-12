"""素材接入层：把「一条视频」规整为流水线统一输入 VideoBundle。

当前实现 LocalFixtureAdapter（目录内 meta.json / transcript.txt / frames.txt）。
线上采集（抖音/小红书链接 → 拉流 → 1fps 抽帧 → Whisper 带时间戳转写）
属于第二周路线图，接口已预留：实现 SourceAdapter.load 即可接入，
流水线与 Prompt 层完全无感。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoBundle:
    meta: dict
    transcript: str
    frames: str


class IngestError(ValueError):
    """素材缺失或不完整。"""


class LocalFixtureAdapter:
    """从本地目录加载已解析素材（开发/测试/离线演示用）。"""

    REQUIRED = ("meta.json", "transcript.txt", "frames.txt")

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def load(self) -> VideoBundle:
        missing = [n for n in self.REQUIRED if not (self.directory / n).exists()]
        if missing:
            raise IngestError(f"{self.directory} 缺少素材文件: {missing}")
        meta = json.loads((self.directory / "meta.json").read_text(encoding="utf-8"))
        return VideoBundle(
            meta=meta,
            transcript=(self.directory / "transcript.txt").read_text(encoding="utf-8"),
            frames=(self.directory / "frames.txt").read_text(encoding="utf-8"),
        )


class DouyinLinkAdapter:
    """线上链接采集（W2 路线图）：浏览器插件端采集 + 用户授权上传双通道。"""

    def __init__(self, url: str) -> None:
        self.url = url

    def load(self) -> VideoBundle:
        raise NotImplementedError(
            "链接采集在两周验证计划 D8-10 实现（插件端规避反爬）；"
            "当前请使用 --fixture 指定本地素材目录。"
        )


def load_persona(path: str | Path) -> dict:
    persona = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("account_name", "niche", "audience", "selling_points", "tone", "taboo"):
        if key not in persona:
            raise IngestError(f"persona.{key}: 缺失必填字段")
    return persona
