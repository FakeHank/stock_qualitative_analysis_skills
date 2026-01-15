#!/usr/bin/env python3

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def collect_pdfs(folder: Path) -> List[Dict[str, str]]:
    pdfs = []
    for path in sorted(folder.glob("*.pdf")):
        pdfs.append(
            {
                "type": "local-pdf",
                "path": str(path.resolve()),
                "filename": path.name,
            }
        )
    return pdfs


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Collect local PDF filings into a manifest."
    )
    ap.add_argument("--folder", required=True, help="Folder containing PDF filings")
    ap.add_argument("--out", required=True, help="Output manifest JSON path")
    args = ap.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.exists():
        raise SystemExit(f"Folder not found: {folder}")

    sources = collect_pdfs(folder)
    manifest = {
        "as_of": datetime.utcnow().isoformat() + "Z",
        "sources": sources,
    }

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
