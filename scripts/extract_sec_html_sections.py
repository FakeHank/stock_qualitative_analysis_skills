#!/usr/bin/env python3

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple

ITEM_ALIASES = {
    "1": ["item 1", "item i"],
    "1a": ["item 1a", "item ia"],
    "1b": ["item 1b", "item ib"],
    "2": ["item 2", "item ii"],
    "3": ["item 3", "item iii"],
    "4": ["item 4", "item iv"],
    "5": ["item 5", "item v"],
    "6": ["item 6", "item vi"],
    "7": ["item 7", "item vii"],
    "7a": ["item 7a", "item viia"],
    "8": ["item 8", "item viii"],
    "9": ["item 9", "item ix"],
    "9a": ["item 9a", "item ixa"],
    "9b": ["item 9b", "item ixb"],
    "10": ["item 10", "item x"],
    "11": ["item 11", "item xi"],
    "12": ["item 12", "item xii"],
    "13": ["item 13", "item xiii"],
    "14": ["item 14", "item xiv"],
    "15": ["item 15", "item xv"],
}

ITEM_ORDER = [
    "1",
    "1a",
    "1b",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "7a",
    "8",
    "9",
    "9a",
    "9b",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_html(raw_html: str) -> str:
    raw_html = re.sub(
        r"<script[^>]*>[\s\S]*?</script>", " ", raw_html, flags=re.IGNORECASE
    )
    raw_html = re.sub(
        r"<style[^>]*>[\s\S]*?</style>", " ", raw_html, flags=re.IGNORECASE
    )
    raw_html = re.sub(
        r"<ix:header[\s\S]*?</ix:header>", " ", raw_html, flags=re.IGNORECASE
    )
    raw_html = re.sub(
        r"<ix:hidden[\s\S]*?</ix:hidden>", " ", raw_html, flags=re.IGNORECASE
    )
    raw_html = re.sub(r"<[^>]+>", " ", raw_html)
    return normalize_whitespace(raw_html)


def build_item_regex(item_id: str) -> re.Pattern:
    aliases = ITEM_ALIASES.get(item_id.lower(), [f"item {item_id}"])
    pattern = r"\b(" + "|".join(re.escape(a) for a in aliases) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


def find_item_positions(text: str, item_ids: List[str]) -> Dict[str, List[int]]:
    positions: Dict[str, List[int]] = {item_id: [] for item_id in item_ids}
    for item_id in item_ids:
        regex = build_item_regex(item_id)
        positions[item_id] = [m.start() for m in regex.finditer(text)]
    return positions


def select_first_positions(positions: Dict[str, List[int]]) -> Dict[str, int]:
    selected: Dict[str, int] = {}
    for item_id, hits in positions.items():
        if hits:
            selected[item_id] = hits[0]
    return selected


def compute_ranges(
    selected: Dict[str, int], item_ids: List[str], text_len: int
) -> List[Tuple[str, int, int]]:
    ordered = [item_id for item_id in ITEM_ORDER if item_id in item_ids]
    ranges: List[Tuple[str, int, int]] = []
    for idx, item_id in enumerate(ordered):
        if item_id not in selected:
            continue
        start = selected[item_id]
        end = text_len
        for next_id in ordered[idx + 1 :]:
            if next_id in selected and selected[next_id] > start:
                end = selected[next_id]
                break
        ranges.append((item_id, start, end))
    return ranges


def extract_sections(text: str, item_ids: List[str]) -> Dict[str, str]:
    positions = find_item_positions(text, item_ids)
    selected = select_first_positions(positions)
    ranges = compute_ranges(selected, item_ids, len(text))
    sections: Dict[str, str] = {}
    for item_id, start, end in ranges:
        chunk = text[start:end]
        sections[item_id] = chunk.strip()
    return sections


def resolve_item_ids(items_arg: str) -> List[str]:
    raw = [item.strip().lower() for item in items_arg.split(",") if item.strip()]
    return raw


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extract 10-K Item sections from SEC HTML."
    )
    ap.add_argument("--html", required=True, help="Path to 10-K HTML file")
    ap.add_argument(
        "--items",
        default="1,1a,7,7a,8",
        help="Comma-separated item list (default: 1,1a,7,7a,8)",
    )
    ap.add_argument("--out-dir", required=True, help="Directory to write item extracts")
    ap.add_argument(
        "--max-chars",
        type=int,
        default=200000,
        help="Max characters per extracted section",
    )
    args = ap.parse_args()

    html_path = Path(args.html).expanduser().resolve()
    if not html_path.exists():
        raise SystemExit(f"HTML file not found: {html_path}")

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_html = html_path.read_text(encoding="utf-8", errors="ignore")
    text = strip_html(raw_html)

    item_ids = resolve_item_ids(args.items)
    sections = extract_sections(text, item_ids)

    if not sections:
        raise SystemExit("No item sections found. Try different items or confirm HTML.")

    for item_id, content in sections.items():
        clipped = content[: args.max_chars]
        out_path = out_dir / f"item_{item_id}.txt"
        out_path.write_text(clipped, encoding="utf-8")
        print(f"[ok] item {item_id} -> {out_path}")


if __name__ == "__main__":
    main()
