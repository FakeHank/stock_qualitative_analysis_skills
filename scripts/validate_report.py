#!/usr/bin/env python3

import argparse
from pathlib import Path

REQUIRED_HEADINGS = [
    "## 投资要点概览",
    "## 公司介绍与沿革",
    "## 员工结构与组织能力",
    "## 管理层与核心团队",
    "## 子公司、分公司与关联公司",
    "## 股权结构与cap table",
    "## 股东回报",
    "## 产品与服务",
    "## 收入结构与商业模式",
    "## 财务表现与盈利能力",
    "## 所属行业分类与相关产业政策",
    "## 供应商与渠道生态",
    "## 用户与客户发展",
    "## 经营理念与战略",
    "## 未来产品规划与商业规划",
    "## 竞争对手与同业对比分析",
    "## 会计政策与关键科目口径",
    "## 税收政策与政府优惠政策",
    "## 重大诉讼与法律程序",
    "## 风险分析",
    "## 来源清单",
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Check required headings in report.")
    ap.add_argument("--file", required=True, help="Report markdown file")
    args = ap.parse_args()

    content = Path(args.file).read_text(encoding="utf-8")
    missing = [h for h in REQUIRED_HEADINGS if h not in content]
    if missing:
        print("Missing headings:")
        for h in missing:
            print(f"- {h}")
        raise SystemExit(1)
    print("Structure OK")


if __name__ == "__main__":
    main()
