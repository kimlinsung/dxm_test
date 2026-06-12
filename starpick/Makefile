.PHONY: demo test lint

# 离线演示：MockLLM 回放金样，零依赖零成本跑通全链路
demo:
	python3 -m starpick --offline

# 单元 + 端到端测试（stdlib unittest，无第三方依赖）
test:
	python3 -m unittest discover -s tests -v

lint:
	python3 -m compileall -q starpick tests
