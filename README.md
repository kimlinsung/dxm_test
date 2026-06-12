# 「小满摘星计划」笔试 · 方向三 内容AI —— 提交说明

> 方案：**摘星 StarPick** —— 对标爆款「拆解 → 平移」Agent
> 申请人：金林松 ｜ 2026.06 ｜ 仓库：https://github.com/kimlinsung/dxm_test

**30 秒读完本仓库：**

- **是什么**：一页 A4 方案（PDF，链接可点）＋ 一个配上任一国产/海外 API Key 就能真跑的 MVP（`starpick/`）。
- **方案**：把博主"拆对标→平移成自己脚本"这个已被付费验证的手工流程（闲鱼已售 90+）产品化，3 分钟出可拍脚本。
- **快速体验**：`cd starpick && make demo`，零依赖零 Key，30 秒离线跑通五段流水线。
- **真实运行**：任配 DeepSeek/通义/Kimi/OpenAI/Claude 一个 Key，`python3 -m starpick.server` 打开四页面原型 LIVE 直连流水线。
- **质量**：42 项单元/E2E 测试全绿＋GitHub Actions CI，含"复用对标台词即失败"红线回归与 LLM 输出容错重试（见 [六、测试](#六通过了哪些测试)）。
- **过程**：18 个结构化 commit 完整还原从脚手架到多供应商真跑的开发路径（见 [七、Git 历史](#七git-历史)）。
- **证据**：三平台检索＋闲鱼/淘宝在售实截（`assets/`），可点击链接清单（`starpick/evidence_links.md`）。

---

## 一、这个目录里有什么

```
dxm_test/（本仓库根）
├── 小满摘星计划_笔试_内容AI_摘星StarPick.pdf   ← 主提交物：一页 A4，资料来源与仓库链接均可点击
├── starpick_onepager.html                      ← 一页纸源文件（改字后可重渲染，命令见下）
├── assets/                                     ← 一页纸引用的图片
│   ├── douyin_search.png / xhs_search.png / kuaishou_search.png   ← 三平台站内检索实截（自摄证据）
│   └── demo_card.png / demo_result.png                            ← 产品原型界面实截
├── starpick/                                   ← 可运行的 MVP 代码（详见其 README）
└── .github/workflows/ci.yml                    ← CI：lint + 42 项测试 + 离线 demo 冒烟
```

## 二、方案一句话

创作者做内容的标准动作是“找对标 → 拆对标 → 平移成自己的脚本”，这一步今天要么手工 60–90 分钟/条，
要么花 ¥9–198 买别人拆好的（闲鱼/淘宝在售、已售 90+）。摘星用多模态模型把它产品化：
**粘贴一条爆款链接，3 分钟拿到按你的人设与产品改写好的可拍脚本**——价格 1/30，速度 20 倍。

一页纸五个区块依次对应题目的五项作答要求：①机会判断 ②用户证据 ③MVP 样例 ④商业判断 ⑤两周验证计划。

## 三、代码仓库 starpick/ —— 不是 PPT，配 Key 即真跑

### 30 秒离线复现（无需任何安装、任何 Key）

```bash
cd starpick
make demo    # MockLLM 回放金样，完整跑通五段流水线，产出 output/report.md
make test    # 42 项单元 + E2E 测试（纯标准库，零第三方依赖）
```

### 真实运行（任配一个国内可用的 Key）

```bash
export DEEPSEEK_API_KEY=sk-...        # 或 DASHSCOPE_API_KEY（通义）/ MOONSHOT_API_KEY（Kimi）
                                      # 或 OPENAI_API_KEY / ANTHROPIC_API_KEY
python3 -m starpick                   # CLI：自动探测 Key，真跑 P1→P2→P3
```

### 产品原型真跑（LIVE 模式）

```bash
python3 -m starpick.server            # 配了 Key：原型页直连真实流水线
python3 -m starpick.server --offline  # 没配 Key：金样回放
```

浏览器打开 `http://127.0.0.1:8765`——原型含**首页 / 工作台 / 历史记录 / 我的人设**四个页面；
工作台点「拆解」后顶栏出现 **LIVE · 引擎与模型** 即为真实调用，每次拆解自动进「历史记录」（localStorage）。
（直接双击 `starpick/demo/index.html` 不起服务端，也能以内置样例预览全部页面。）
若模型偶发输出不合规 JSON，流水线会自动修复并带原因重试 2 次（`pipeline.py`）。

### 仓库里还有什么

| 内容 | 位置 |
|---|---|
| P1 拆解员 / P2 策略师 / P3 编剧 完整 Prompt | `starpick/prompts/` |
| 内容样片（平移脚本：口播稿+分镜表+拍摄清单） | `starpick/fixtures/golden/p3_transplant.md` |
| 五段流水线 + 三级 schema 校验 + 多供应商客户端 | `starpick/starpick/` |
| 42 项测试（红线回归、服务端 HTTP E2E、容错重试） | `starpick/tests/` |
| GitHub Actions CI（Python 3.11/3.12 矩阵） | `.github/workflows/ci.yml` |
| 用户证据可点击链接清单（对应一页纸脚注） | `starpick/evidence_links.md` |

## 四、一页纸如何重渲染（如需改字）

编辑 `starpick_onepager.html` 后：

```bash
# PDF（超链接可点击；正文字体须用可嵌入的 Hiragino Sans GB，PingFang 会导致 PDF 文字丢失）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-pdf-header-footer --print-to-pdf="小满摘星计划_笔试_内容AI_摘星StarPick.pdf" \
  "file://$PWD/starpick_onepager.html"
```

注意：渲染必须在本目录执行（图片走 `assets/` 相对路径）。

## 五、提交前清单

1. **仓库链接**：`https://github.com/kimlinsung/dxm_test` 写进提交邮件/表单。
2. **主件**：提交 **PDF 版**（资料来源与仓库链接均可点击）。
3. **证据留底**：按 `starpick/evidence_links.md` 把各链接点开截图存档，面试追问时出示。
4. （可选）录一段 30 秒 Demo：`python3 -m starpick.server --offline` 后录屏点击全流程。

## 六、通过了哪些测试

`cd starpick && make test` —— **42 项全部通过**（纯标准库 `unittest`，零第三方依赖），按层次分为：

| 层次 | 文件 | 数量 | 覆盖什么 |
|---|---|---|---|
| Schema 校验 | `tests/test_schema.py` | 10 | 骨架卡/策略/平移脚本三级结构：必填字段、秒数合法性、可平移度 0–100、缺章节拒绝 |
| Prompt 契约 | `tests/test_prompts.py` | 6 | 三段模板可加载、占位符必须填满、输出契约（只产 JSON、固定章节、禁复用台词）被钉死在模板里 |
| 流水线编排 | `tests/test_pipeline.py` | 11 | 素材加载、三阶段按序调用、人设注入下游 Prompt、围栏/闲话/尾逗号容错解析、**坏输出→带原因重试→恢复**、重试耗尽报错带阶段名 |
| LLM 工厂 | `tests/test_llm_factory.py` | 8 | auto 按 Key 探测供应商、显式指定、缺 Key 报错给指引、`STARPICK_MODEL`/`OPENAI_BASE_URL` 覆盖生效 |
| 服务端 E2E | `tests/test_server.py` | 3 | 起真实 HTTP 服务：首页可达、`POST /api/analyze` 走通全流水线、404 兜底 |
| 全链路 E2E | `tests/test_e2e.py` | 4 | CLI 入口离线跑通出报告、离线确定性（两次结果一致）、**红线回归：平移脚本含对标台词原句即失败** |

CI（`.github/workflows/ci.yml`）在 Python 3.11/3.12 矩阵上跑 lint + 全部测试 + 离线 demo 冒烟。

## 七、Git 历史

18 个结构化 commit 完整还原开发路径（`git log --oneline --reverse`）：

1. `chore` 脚手架：Makefile / CI / gitignore
2. `feat(prompts)` P1 拆解员 / P2 策略师 / P3 编剧三段 Prompt 链
3. `feat(core)` 三级 schema 校验 + LLM 双实现（API / 离线 Mock）
4. `feat(pipeline)` 素材接入、五段编排、CLI 与金样数据
5. `test` 27 项单元与 E2E（schema / Prompt 契约 / 编排 / 红线回归）
6. `feat(demo)` 可交互原型页（内置金样）
7. `docs` README：架构、快速开始、工程决策
8. `docs` 用户证据可点击链接清单
9. `feat(llm)` 多供应商支持（DeepSeek/通义/Kimi/OpenAI 兼容/Anthropic）与 make_llm 工厂
10. `feat(server)` 本地服务端 `/api/analyze` 直连流水线
11. `feat(demo)` 原型页动态渲染：服务端 LIVE 优先、file:// 回退样例
12. `test` 工厂 8 项 + 服务端 HTTP E2E 3 项
13. `docs` README：多供应商配置与服务端用法
14. `feat(pipeline)` 容错 JSON 解析与带错误反馈的阶段重试（修复真实模型偶发不合规）
15. `feat(demo)` 多页面原型：首页 / 工作台 / 历史记录 / 我的人设
16. `docs` README：42 项测试与容错重试决策
17. `refactor(repo)` 仓库根上移为完整提交包（代码历史经 rename 保留），CI 随迁
18. `feat(evidence)` 闲鱼/淘宝在售实锤上页；修复 PDF 字体嵌入

> 阅读建议：按序号读 commit message 即可看到「先定契约（Prompt/schema/测试）→ 再扩能力（多供应商/服务端/多页面）→ 持续修真实问题（JSON 容错/字体嵌入）」的迭代节奏。

## 八、资料来源（与一页纸脚注一致）

1. [淘宝检索「对标账号拆解」](https://s.taobao.com/search?q=%E5%AF%B9%E6%A0%87%E8%B4%A6%E5%8F%B7%E6%8B%86%E8%A7%A3)——人工拆解服务在售 ¥30–200/条
2. [第一财经：可灵AI全年收入约1.4亿美元](https://www.yicai.com/news/102919501.html)
3. [即梦AI运营数据解析（2025.04 用户600万+、营收破亿）](https://zhuanlan.zhihu.com/p/1987939926201882473)
4. [Reddit r/NewTubers "viral format" 检索](https://www.reddit.com/r/NewTubers/search/?q=viral%20format)
5. [《中国网络视听发展研究报告(2025)》（新华网）](http://www.news.cn/tech/20250327/39664326a8244f9ba7489821817fcd68/c.html)——职业主播 3880 万、日产内容 1.3 亿条
6. 抖音/小红书/快手站内检索实截见 `assets/`（2026.06 自摄）
