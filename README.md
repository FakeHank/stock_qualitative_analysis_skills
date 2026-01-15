# Stock Qualitative Analysis Skill

[中文说明](README_zh.md)

## Overview
A skill for producing buy‑side style qualitative stock analysis reports (定性分析) from SEC filings and other public sources. It enforces strict citations, comprehensive section coverage, and explicit placeholders for missing evidence.

## Key Features
- Evidence‑first reporting with explicit citations and placeholders
- Section‑by‑section workflow aligned to `assets/report-template.md`
- English output when the user query is in English
- Modular data acquisition (SEC EDGAR + local PDFs)
- HTML 10‑K section extraction for faster analysis

## Requirements
- Python 3
- Network access for SEC EDGAR fetching (optional)

## Directory Structure
- `SKILL.md`: Skill definition and execution rules
- `assets/report-template.md`: Report template
- `references/`: Guardrails, validation checklist, goldenset
- `scripts/`: Data acquisition and extraction utilities

## Quick Start
### 0) Install the skill in your agent
Place the `stock-qualitative-analysis/` folder in the skills directory that your agent scans. For Claude Code, Codex, or OpenCode, use the tool’s configured skills path (check its docs/settings) and ensure the folder name matches `stock-qualitative-analysis`.

### 1) (Optional) Prepare sources
Local PDFs and SEC filings are both optional. If you already have files, ingest them; otherwise the Agent can fetch data during execution.

If local filings are available, prefer local PDFs first:
```
python3 scripts/ingest_local_pdfs.py --folder <local_pdf_dir> --out ./cache/source_manifest.json
```

### 2) (Optional) Fetch SEC filings
```
python3 scripts/fetch_sec_edgar.py --ticker AAPL --form 10-K 10-Q --start 2022-01-01 --out ./cache/sec_edgar
```
Then build a unified manifest:
```
python3 scripts/build_source_manifest.py --ticker AAPL --forms 10-K 10-Q --start 2022-01-01 --sec-out ./cache/sec_edgar --out ./cache/source_manifest.json
```

### 3) Extract 10‑K HTML sections
```
python3 scripts/extract_sec_html_sections.py --html <path/to/10k.htm> --items 1,1a,7,7a,8 --out-dir ./cache/sections
```

### 4) Generate the report (Agent‑driven)
The Agent reads `assets/report-template.md` and fills each section using available sources and extracted item text. See `SKILL.md` for the execution rules.

## English Output
If the user query is in English, the Agent must generate an English report while preserving the template structure. Section labels should be translated consistently (e.g., Conclusion / Details / Evidence).

## Offline Mode
If network access is blocked (SSL/Cloudflare), use local PDFs and HTML files only. The skill supports building a manifest from local files and extracting sections from local HTML.

## Troubleshooting
- **SSL/Cloudflare blocked**: Use local filings or configure `SEC_USER_AGENT` with multiple agents (comma‑separated). Example:
  `SEC_USER_AGENT="UA1,UA2" python3 scripts/fetch_sec_edgar.py ...`
- **No item sections found**: Verify the HTML file contains Item headings or try different items.

## Scripts
- `scripts/fetch_sec_edgar.py`: Download SEC iXBRL HTML and XBRL instance files
- `scripts/ingest_local_pdfs.py`: Build a manifest from local PDFs
- `scripts/build_source_manifest.py`: Merge SEC and local sources into a manifest
- `scripts/extract_sec_html_sections.py`: Extract Item sections from 10‑K HTML
- `scripts/validate_report.py`: Validate required headings in a report

## Attribution
This skill is inspired by https://github.com/noho/learning_notes. Many analysis practices, reporting structure, and workflow ideas originate from that repository. Thanks to the author for sharing the foundational notes.

## Improvements vs. `noho/learning_notes`
- Packaged as an Agent Skill with explicit execution rules in `SKILL.md`.
- Added modular scripts for SEC EDGAR fetching, local PDF ingestion, and manifest building.
- Added HTML Item section extraction to speed up analysis from large 10‑K files.
- Enforced evidence‑first reporting with placeholders and structured citation rules.
- Added offline‑first guidance and clearer troubleshooting steps.
- Added English output behavior when the user query is in English.

## Limitations
- The skill does not provide investment advice or price targets.
- Real‑time data requires user verification.
- Section filling depends on available sources; missing data is explicitly marked.

## License
Add your license terms here.
