#!/usr/bin/env python3

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def run_sec_fetch(
    fetch_script: Path,
    out_dir: Path,
    ticker: str,
    forms: List[str],
    start: str,
    end: str | None,
) -> None:
    cmd = [
        str(fetch_script),
        "--ticker",
        ticker,
        "--form",
        *forms,
        "--start",
        start,
        "--out",
        str(out_dir),
    ]
    if end:
        cmd.extend(["--end", end])
    subprocess.run(cmd, check=False)


def collect_sec_dirs(out_dir: Path) -> List[Dict[str, str]]:
    sources: List[Dict[str, str]] = []
    for path in out_dir.glob("**/meta.json"):
        sources.append({"type": "sec-edgar", "path": str(path.resolve())})
    return sources


def collect_pdfs(folder: Path) -> List[Dict[str, str]]:
    sources = []
    for path in sorted(folder.glob("*.pdf")):
        sources.append({"type": "local-pdf", "path": str(path.resolve())})
    return sources


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build a unified source manifest for qualitative analysis."
    )
    ap.add_argument("--ticker", help="SEC ticker for EDGAR fetch")
    ap.add_argument(
        "--forms", nargs="+", default=["10-K", "10-Q"], help="SEC form types"
    )
    ap.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", help="End date YYYY-MM-DD")
    ap.add_argument(
        "--sec-out", default="./cache/sec_edgar", help="Output dir for SEC downloads"
    )
    ap.add_argument("--local-pdf", help="Folder containing local PDF filings")
    ap.add_argument(
        "--out", default="./cache/source_manifest.json", help="Manifest output path"
    )
    args = ap.parse_args()

    sec_sources: List[Dict[str, str]] = []
    if args.ticker:
        fetch_script = Path(__file__).parent / "fetch_sec_edgar.py"
        out_dir = Path(args.sec_out).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        run_sec_fetch(
            fetch_script, out_dir, args.ticker, args.forms, args.start, args.end
        )
        sec_sources = collect_sec_dirs(out_dir)

    local_sources: List[Dict[str, str]] = []
    if args.local_pdf:
        local_sources = collect_pdfs(Path(args.local_pdf).expanduser().resolve())

    manifest = {
        "as_of": datetime.utcnow().isoformat() + "Z",
        "sources": sec_sources + local_sources,
    }

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
