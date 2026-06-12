"""命令行入口。

离线演示（无需任何 Key，回放金样跑通全链路）：
    python3 -m starpick --offline

真实调用（需 ANTHROPIC_API_KEY）：
    python3 -m starpick --fixture fixtures/sample_video --persona fixtures/persona_office.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ingest import LocalFixtureAdapter, load_persona
from .llm import AnthropicLLM, MockLLM
from .pipeline import format_report, run_pipeline
from .prompts import ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="starpick", description="对标爆款「拆解 → 平移」流水线")
    parser.add_argument("--fixture", default=str(ROOT / "fixtures" / "sample_video"),
                        help="本地素材目录（meta.json/transcript.txt/frames.txt）")
    parser.add_argument("--persona", default=str(ROOT / "fixtures" / "persona_office.json"),
                        help="账号人设 JSON")
    parser.add_argument("--offline", action="store_true",
                        help="MockLLM 回放金样，零网络零成本复现链路")
    parser.add_argument("--out", default=str(ROOT / "output" / "report.md"),
                        help="报告输出路径")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    bundle = LocalFixtureAdapter(args.fixture).load()
    persona = load_persona(args.persona)
    llm = MockLLM(ROOT / "fixtures" / "golden") if args.offline else AnthropicLLM()

    report = run_pipeline(bundle, persona, llm)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_report(report), encoding="utf-8")

    meta = report.bundle.meta
    print(f"对标视频   《{meta['title']}》  ♥ {meta['likes']:,}")
    print(f"钩子       {report.skeleton['hook']['type']}（{report.skeleton['hook']['start']}-{report.skeleton['hook']['end']}s）")
    print(f"结构       {' → '.join(s['name'] for s in report.skeleton['structure'])}")
    print(f"可平移度   {report.strategy['transferability']}/100")
    print(f"报告       {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
