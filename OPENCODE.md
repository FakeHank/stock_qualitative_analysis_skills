# 用 OpenCode + stock-qualitative-analysis 做股票定性分析（小白版）

这份文档假设你**不会写代码**。你只需要：
- 会在电脑里创建文件夹、拖拽文件

---

## 1) OpenCode 是什么？
OpenCode 是一个“在终端里聊天、让它帮你做事”的 AI 工具。它可以加载 Skill（技能包），按 Skill 的规则一步步帮你完成任务。

- 官网：`https://opencode.ai`
- OpenCode 文档：`https://opencode.ai/docs`
- Skills 文档：`https://opencode.ai/docs/skills/`

---

## 2) 安装 OpenCode（推荐方式）

### macOS / Linux
1. 打开“终端（Terminal）”
2. 复制粘贴下面这一行并回车：

```bash
curl -fsSL https://opencode.ai/install | bash
```

3. 安装好后，输入下面命令检查是否成功：

```bash
opencode --help
```

如果你看到帮助信息，说明安装成功。

### Windows（简单说明）
OpenCode 支持 Windows。你可以参考官方文档的安装方式：
- `https://opencode.ai/docs/#install`

---

## 3) 准备一个“股票分析项目文件夹”（不需要写代码）
建议你为每次分析创建一个独立文件夹，方便保存：原始财报、缓存、输出报告。

### 推荐目录结构
以 macOS 为例（放在“文稿/Documents”里）：

1. 打开 Finder
2. 进入 `Documents`
3. 新建一个文件夹，比如：`invest-playground`
4. 再在里面新建一个文件夹，比如：`v0.1`

最后你会得到：

```text
~/Documents/invest-playground/v0.1/
```

然后在这个文件夹里再建 3 个子文件夹（在 Finder 里右键“新建文件夹”即可）：

```text
sources/   # 你手动下载的财报/PDF/HTML
cache/     # 工具生成的清单、分段等中间文件
output/    # 最终报告
```

---

## 4) 把这个 Skill 放到 `.opencode/skill`（最关键的一步）
OpenCode 会自动扫描并加载你项目里的 Skill。你要做的是把本 Skill 放到项目目录的：

```text
.opencode/skill/stock-qualitative-analysis/
```

### 4.1 在你的项目里创建 Skill 目录（用 Finder）
在 Finder 里进入你的项目目录：

`~/Documents/invest-playground/v0.1/`

然后按下面结构创建文件夹（大小写要一致）：

```text
.opencode/
  skill/
    stock-qualitative-analysis/
```

提示：如果你看不到以“.”开头的 `.opencode` 文件夹，这是正常的（macOS 默认隐藏点开头文件夹）。你可以：
- 在 Finder 里按 `Command + Shift + .` 显示隐藏文件

### 4.2 把 Skill 文件复制进去（用 Finder）
你需要把本仓库里的 `skills/stock-qualitative-analysis/` 文件夹里的所有内容复制到：

`~/Documents/invest-playground/v0.1/.opencode/skill/stock-qualitative-analysis/`

复制完成后，在目标文件夹里确认能看到：
- `SKILL.md`
- `assets/`
- `references/`
- `scripts/`

只要 `SKILL.md` 在正确位置，OpenCode 就能识别这个 Skill。

---

## 5) 启动 OpenCode
打开“终端（Terminal）”，输入：

```bash
opencode
```

然后在 OpenCode 里切换到你的分析项目目录（如果你不熟悉命令行，可以先用 Finder 打开 `~/Documents/invest-playground/v0.1/`，再把这个路径复制出来粘贴到终端里）。

第一次使用建议在 OpenCode 里输入：
- `/init`（让 OpenCode 认识你的项目）
- `/connect`（选择模型/登录/配置 Key。按 OpenCode 的提示操作即可）

---

## 6) 怎么用这个 Skill（不会写代码也能用）
你只要在 OpenCode 对话里，像给助理下任务一样描述：

### 中文示例
```text
用 stock-qualitative-analysis 帮我做 AAPL 的定性分析。
如果 sources/ 里已经有财报，优先使用本地文件；不够再抓取 SEC。
按 assets/report-template.md 的结构逐章写入 output/aapl_report.md。
每条事实都要给出处；没有证据就用【占位符】说明缺什么。
```

### English example
```text
Use stock-qualitative-analysis to produce a qualitative report for AAPL.
Prefer local filings in sources/ if available; otherwise fetch SEC filings.
Write the report section-by-section into output/aapl_report.md following assets/report-template.md.
Cite sources for every factual claim; if missing evidence, use explicit placeholders.
```

重要规则：
- 你用英文问，它就用英文写报告。
- 本地 PDF / SEC 抓取都是可选的；你不准备也可以，Agent 会尝试自己抓取。

---

## 7) 常见问题（非常实用）
### 7.1 抓取被 SSL/Cloudflare 挡住了
这种情况很常见，和你电脑/网络环境有关。

解决办法：
- 直接手动下载财报文件（PDF/HTML/XBRL），放进 `sources/`
- 让 Agent 只用本地文件继续完成分析

### 7.2 Skill 没被识别
通常原因是目录或文件名不对。
请确认：
- 路径是：`.opencode/skill/stock-qualitative-analysis/SKILL.md`
- 目录名是：`stock-qualitative-analysis`
- 文件名是大写：`SKILL.md`
