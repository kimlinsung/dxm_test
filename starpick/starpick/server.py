"""本地服务端：让 demo 原型直连真实流水线。

    python3 -m starpick.server --offline               # 无 Key 演示（金样回放）
    DEEPSEEK_API_KEY=sk-... python3 -m starpick.server  # 真实模型

接口：
    GET  /                    原型页
    GET  /api/health          引擎信息（页面加载时探测连接状态）
    POST /api/analyze         一次性返回完整结果（兼容/测试用）
    POST /api/analyze/stream  NDJSON 流式：逐阶段推送 P1/P2/P3 真实进度与耗时
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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
    engine = ""  # 启动时探测后回填


def _engine_name(llm) -> str:
    return "offline 金样回放" if llm.name == "mock" else f"{llm.name} · {llm.model}"


def analyze(cfg: Config, on_stage=None) -> dict:
    bundle = LocalFixtureAdapter(cfg.fixture).load()
    persona = load_persona(cfg.persona)
    llm = make_llm(cfg.provider, offline=cfg.offline, golden_dir=ROOT / "fixtures" / "golden")
    report = run_pipeline(bundle, persona, llm, on_stage=on_stage)
    return {
        "engine": _engine_name(llm),
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

    def _send_json(self, code: int, obj: dict) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 (http.server 约定)
        if self.path in ("/", "/index.html"):
            self._send(200, DEMO_HTML.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/health":
            self._send_json(200, {"engine": self.cfg.engine, "offline": self.cfg.offline})
        else:
            self._send(404, b"not found", "text/plain")

    def _drain_body(self) -> None:
        """读掉请求体：不读完就关连接会触发 TCP RST，客户端读无长度的流式响应时会报 connection reset。"""
        length = int(self.headers.get("content-length") or 0)
        if length:
            self.rfile.read(length)

    def do_POST(self) -> None:  # noqa: N802
        self._drain_body()
        if self.path == "/api/analyze":
            try:
                self._send_json(200, analyze(self.cfg))
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
        elif self.path == "/api/analyze/stream":
            self._stream_analyze()
        else:
            self._send(404, b"not found", "text/plain")

    def _stream_analyze(self) -> None:
        """NDJSON 流：headers 后逐行 flush，前端边读边渲染真实阶段进度。"""
        self.send_response(200)
        self.send_header("content-type", "application/x-ndjson; charset=utf-8")
        self.send_header("cache-control", "no-cache")
        self.send_header("connection", "close")
        self.end_headers()
        t0 = time.time()

        def emit(obj: dict) -> None:
            line = json.dumps(obj, ensure_ascii=False) + "\n"
            self.wfile.write(line.encode("utf-8"))
            self.wfile.flush()

        emit({"event": "start", "engine": self.cfg.engine})
        try:
            result = analyze(
                self.cfg,
                on_stage=lambda label, phase: emit(
                    {"event": "stage", "stage": label, "phase": phase,
                     "t": round(time.time() - t0, 1)}
                ),
            )
            emit({"event": "result", "t": round(time.time() - t0, 1), "data": result})
        except Exception as exc:
            emit({"event": "error", "error": str(exc)})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[server] " + fmt % args + "\n")


def make_server(cfg: Config, port: int) -> ThreadingHTTPServer:
    if not cfg.engine:
        llm = make_llm(cfg.provider, offline=cfg.offline, golden_dir=ROOT / "fixtures" / "golden")
        cfg.engine = _engine_name(llm)
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
    server = make_server(cfg, args.port)
    print(f"StarPick 原型服务端  http://127.0.0.1:{args.port}   引擎: {cfg.engine}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
