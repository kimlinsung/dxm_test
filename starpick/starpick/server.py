"""本地服务端：让 demo 原型直连真实流水线。

    python3 -m starpick.server --offline               # 无 Key 演示（金样回放）
    DEEPSEEK_API_KEY=sk-... python3 -m starpick.server  # 真实模型

然后浏览器打开 http://127.0.0.1:8765 ，原型页的「拆解」按钮即调用
POST /api/analyze 真正跑一遍 P1→P2→P3。
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .ingest import LocalFixtureAdapter, load_persona
from .llm import PROVIDERS, make_llm
from .pipeline import run_pipeline
from .prompts import ROOT

DEMO_HTML = ROOT / "demo" / "index.html"


class Config:
    provider = "auto"
    offline = False
    fixture = str(ROOT / "fixtures" / "sample_video")
    persona = str(ROOT / "fixtures" / "persona_office.json")


def analyze(cfg: Config) -> dict:
    bundle = LocalFixtureAdapter(cfg.fixture).load()
    persona = load_persona(cfg.persona)
    llm = make_llm(cfg.provider, offline=cfg.offline, golden_dir=ROOT / "fixtures" / "golden")
    report = run_pipeline(bundle, persona, llm)
    return {
        "engine": "offline 金样回放" if llm.name == "mock" else f"{llm.name} · {llm.model}",
        "meta": report.bundle.meta,
        "persona": report.persona,
        "skeleton": report.skeleton,
        "strategy": report.strategy,
        "transplant_md": report.transplant_md,
    }


class Handler(BaseHTTPRequestHandler):
    cfg = Config()

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (http.server 约定)
        if self.path in ("/", "/index.html"):
            self._send(200, DEMO_HTML.read_bytes(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/analyze":
            self._send(404, b"not found", "text/plain")
            return
        try:
            payload = json.dumps(analyze(self.cfg), ensure_ascii=False).encode("utf-8")
            self._send(200, payload, "application/json; charset=utf-8")
        except Exception as exc:  # 把流水线错误透传给前端展示
            err = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self._send(500, err, "application/json; charset=utf-8")

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[server] " + fmt % args + "\n")


def make_server(cfg: Config, port: int) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"cfg": cfg})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="starpick.server", description="StarPick 原型服务端")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--provider", default="auto", choices=PROVIDERS)
    parser.add_argument("--offline", action="store_true", help="金样回放，无需 Key")
    parser.add_argument("--fixture", default=Config.fixture)
    parser.add_argument("--persona", default=Config.persona)
    args = parser.parse_args(argv)

    cfg = Config()
    cfg.provider, cfg.offline = args.provider, args.offline
    cfg.fixture, cfg.persona = args.fixture, args.persona

    # 启动时先验证一次模型配置，配置错误立刻失败而不是等首个请求
    llm = make_llm(cfg.provider, offline=cfg.offline, golden_dir=ROOT / "fixtures" / "golden")
    engine = "offline 金样回放" if llm.name == "mock" else f"{llm.name} · {llm.model}"

    server = make_server(cfg, args.port)
    print(f"StarPick 原型服务端  http://127.0.0.1:{args.port}   引擎: {engine}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
