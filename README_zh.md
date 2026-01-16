# 股票定性分析 Skill

## 概述
这是一个面向买方风格的股票定性分析 Skill，基于 SEC filings 与公开来源输出结构化报告。它强调严格的证据引用、完整的章节覆盖，以及对缺失信息的明确占位说明。

## 主要特性
- 证据优先：所有事实必须有来源或占位符
- 按模板逐章生成，结构与 `assets/report-template.md` 对齐
- 当用户输入为英文时，输出英文报告
- 模块化数据获取（SEC EDGAR + 本地 PDF）
- 提供 10‑K HTML 分段抽取工具，提高分析效率

## 环境要求
- Python 3
- SEC EDGAR 抓取需要网络（可选）

## 目录结构
- `SKILL.md`：Skill 定义与执行规则
- `assets/report-template.md`：报告模板
- `references/`：写作规范、校验清单、goldenset
- `scripts/`：数据获取与抽取工具

## 快速开始

如果你完全不知道 OpenCode 是什么，也不会写代码，请先看这份非程序员专属指南：[OPENCODE.md](OPENCODE.md)

### 0) 安装到 Agent
将 `stock-qualitative-analysis/` 文件夹放到你的 Agent 会扫描的 skills 目录中。Claude Code / Codex / OpenCode 请使用各自配置的 skills 路径（查看其文档或设置），并确保目录名为 `stock-qualitative-analysis`。

### 1)（可选）准备数据
本地 PDF 和 SEC filings 都是可选项。若已准备文件可先入清单；未准备也没关系，Agent 可在运行时抓取。

优先使用本地 PDF：
```
python3 scripts/ingest_local_pdfs.py --folder <local_pdf_dir> --out ./cache/source_manifest.json
```

### 2)（可选）抓取 SEC filings
```
python3 scripts/fetch_sec_edgar.py --ticker AAPL --form 10-K 10-Q --start 2022-01-01 --out ./cache/sec_edgar
```
然后生成统一清单：
```
python3 scripts/build_source_manifest.py --ticker AAPL --forms 10-K 10-Q --start 2022-01-01 --sec-out ./cache/sec_edgar --out ./cache/source_manifest.json
```

### 3) 抽取 10‑K HTML 分段
```
python3 scripts/extract_sec_html_sections.py --html <path/to/10k.htm> --items 1,1a,7,7a,8 --out-dir ./cache/sections
```

### 4) 生成报告（由 Agent 驱动）
Agent 读取 `assets/report-template.md` 并逐章填充内容与引用。执行细则见 `SKILL.md`。

## 英文输出
当用户 query 为英文时，必须输出英文报告，并保持模板结构一致（如 Conclusion / Details / Evidence）。

## 离线模式
若网络被阻断（SSL/Cloudflare），请仅使用本地 PDF/HTML，并在本地生成清单与分段文件。

## 常见问题
- **SSL/Cloudflare 阻断**：使用本地文件，或通过 `SEC_USER_AGENT` 设置多个 UA（逗号分隔）。示例：
  `SEC_USER_AGENT="UA1,UA2" python3 scripts/fetch_sec_edgar.py ...`
- **无法抽取 Item**：确认 HTML 内含 Item 标题，或更换 `--items` 参数。

## 脚本清单
- `scripts/fetch_sec_edgar.py`：下载 SEC iXBRL HTML/XBRL
- `scripts/ingest_local_pdfs.py`：本地 PDF 入清单
- `scripts/build_source_manifest.py`：合并 SEC 与本地来源
- `scripts/extract_sec_html_sections.py`：按 Item 抽取 10‑K 章节
- `scripts/validate_report.py`：校验报告结构

## 致谢
本 Skill 的灵感来源于 https://github.com/noho/learning_notes。报告结构、分析流程与实践方法大量参考该仓库，感谢作者分享。

## 相比 `noho/learning_notes` 的改进
- 以 Agent Skill 形式封装，执行规则明确
- 增加 SEC EDGAR 抓取、本地 PDF 入清单与统一 manifest
- 增加 HTML Item 分段抽取，提高分析效率
- 强化证据链规则与占位符约束
- 增加离线模式与故障排查指引
- 支持英文输出（英文 query -> 英文报告）

## 限制
- 不提供投资建议或价格预测
- 实时数据需要用户自行核实
- 报告质量依赖可用数据完整性

## License
请在此处补充开源许可条款。
