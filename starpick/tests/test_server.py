"""服务端 E2E：起真实 HTTP 服务（离线引擎），走 HTTP 调一遍完整流水线。"""

import json
import threading
import unittest
import urllib.error
import urllib.request

from starpick.server import Config, make_server


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = Config()
        cfg.offline = True
        cls.server = make_server(cfg, port=0)  # 端口 0 = 随机空闲端口
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_index_serves_demo_page(self):
        with urllib.request.urlopen(f"{self.base}/", timeout=10) as resp:
            html = resp.read().decode("utf-8")
        self.assertEqual(resp.status, 200)
        self.assertIn("StarPick", html)
        self.assertIn("api/analyze", html)

    def test_analyze_runs_full_pipeline_over_http(self):
        req = urllib.request.Request(f"{self.base}/api/analyze", data=b"{}", method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(resp.status, 200)
        self.assertEqual(payload["strategy"]["transferability"], 86)
        self.assertEqual(payload["skeleton"]["hook"]["type"], "反常识宣言")
        self.assertIn("### 分镜表", payload["transplant_md"])
        self.assertIn("金样回放", payload["engine"])

    def test_unknown_path_404(self):
        try:
            urllib.request.urlopen(f"{self.base}/nope", timeout=10)
            self.fail("应返回 404")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)


if __name__ == "__main__":
    unittest.main()
