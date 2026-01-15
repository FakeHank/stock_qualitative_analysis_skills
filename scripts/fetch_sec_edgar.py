#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.exceptions import Timeout, SSLError, RequestException

SEC_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/"
ARCHIVES_INDEX_JSON = ARCHIVES_BASE + "index.json"
BROWSE_EDGAR_TEMPLATE = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_or_ticker}&type={form}&count=100"

DEFAULT_SLEEP_SEC = 0.2
DEFAULT_USER_AGENT = "Leo Liu leo@dayu.fund"
DEFAULT_USER_AGENTS = [
    DEFAULT_USER_AGENT,
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
DEFAULT_OUT_DIR = "./filings"
USER_AGENTS = DEFAULT_USER_AGENTS

MAX_TIMEOUT_RETRIES = 3
RETRY_BACKOFF_BASE_SEC = 0.8


def parse_date(s: str, is_end: bool = False) -> dt.date:
    s = s.strip()
    if re.match(r"^\d{4}$", s):
        year = int(s)
        return dt.date(year, 12, 31) if is_end else dt.date(year, 1, 1)
    if re.match(r"^\d{4}-\d{1,2}$", s):
        year, month = s.split("-")
        year = int(year)
        month = int(month)
        if is_end:
            if month == 12:
                next_month = dt.date(year + 1, 1, 1)
            else:
                next_month = dt.date(year, month + 1, 1)
            return next_month - dt.timedelta(days=1)
        return dt.date(year, month, 1)
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def user_agent_values(args_ua: Optional[str]) -> List[str]:
    raw = args_ua or os.environ.get("SEC_USER_AGENT") or ""
    if raw.strip():
        agents = [item.strip() for item in raw.split(",") if item.strip()]
        return agents or [DEFAULT_USER_AGENT]
    return DEFAULT_USER_AGENTS


def _sleep_backoff(attempt_idx: int) -> None:
    time.sleep(RETRY_BACKOFF_BASE_SEC * (2**attempt_idx))


def http_get_json(url: str, headers: Dict[str, str], timeout: int = 30) -> Dict:
    last_err: Optional[Exception] = None
    for attempt in range(MAX_TIMEOUT_RETRIES):
        for user_agent in USER_AGENTS:
            try:
                req_headers = dict(headers)
                req_headers["User-Agent"] = user_agent
                r = requests.get(url, headers=req_headers, timeout=timeout)
                r.raise_for_status()
                return r.json()
            except (Timeout, SSLError, RequestException) as e:
                last_err = e
                continue
        if attempt < MAX_TIMEOUT_RETRIES - 1:
            _sleep_backoff(attempt)
    raise last_err  # type: ignore[misc]


def http_head(
    url: str, headers: Dict[str, str], timeout: int = 30
) -> Optional[requests.Response]:
    for attempt in range(MAX_TIMEOUT_RETRIES):
        for user_agent in USER_AGENTS:
            try:
                req_headers = dict(headers)
                req_headers["User-Agent"] = user_agent
                r = requests.head(
                    url, headers=req_headers, timeout=timeout, allow_redirects=True
                )
                return r if r.status_code == 200 else None
            except (Timeout, SSLError, RequestException):
                continue
        if attempt < MAX_TIMEOUT_RETRIES - 1:
            _sleep_backoff(attempt)
    return None


def should_download(
    url: str, headers: Dict[str, str], out_path: Path, force_overwrite: bool
) -> bool:
    if force_overwrite:
        return True
    if not out_path.exists():
        return True
    head_resp = http_head(url, headers)
    if head_resp is None:
        return False
    last_modified = head_resp.headers.get("Last-Modified")
    if last_modified:
        try:
            remote_time = dt.datetime.strptime(
                last_modified, "%a, %d %b %Y %H:%M:%S %Z"
            )
            local_time = dt.datetime.fromtimestamp(out_path.stat().st_mtime)
            return remote_time > local_time
        except Exception:
            pass
    return True


def http_download(
    url: str, headers: Dict[str, str], out_path: Path, timeout: int = 60
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    last_err: Optional[Exception] = None
    for attempt in range(MAX_TIMEOUT_RETRIES):
        for user_agent in USER_AGENTS:
            try:
                req_headers = dict(headers)
                req_headers["User-Agent"] = user_agent
                tmp_path = out_path.with_suffix(out_path.suffix + ".part")
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                with requests.get(
                    url, headers=req_headers, timeout=timeout, stream=True
                ) as r:
                    r.raise_for_status()
                    with open(tmp_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 64):
                            if chunk:
                                f.write(chunk)
                tmp_path.replace(out_path)
                return
            except (Timeout, SSLError, RequestException) as e:
                last_err = e
                try:
                    tmp_path = out_path.with_suffix(out_path.suffix + ".part")
                    if tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass
                continue
        if attempt < MAX_TIMEOUT_RETRIES - 1:
            _sleep_backoff(attempt)
    raise last_err  # type: ignore[misc]


def ticker_to_cik(ticker: str, headers: Dict[str, str]) -> str:
    ticker = ticker.strip().upper()
    data = http_get_json(SEC_TICKER_MAP_URL, headers=headers)
    for _, row in data.items():
        if str(row.get("ticker", "")).upper() == ticker:
            cik = str(row.get("cik_str", "")).strip()
            if cik.isdigit():
                return cik
    raise SystemExit(f"Error: Cannot find CIK for ticker={ticker} from SEC ticker map.")


def cik_to_10digits(cik: str) -> str:
    c = cik.strip().lstrip("0") or "0"
    if not c.isdigit():
        raise SystemExit(f"Error: CIK must be numeric, got: {cik}")
    return c.zfill(10)


def accession_no_nodash(accession: str) -> str:
    return accession.replace("-", "").strip()


def pick_extracted_instance_xml(items: List[Dict]) -> Optional[str]:
    names = [it.get("name", "") for it in items if isinstance(it, dict)]
    for n in names:
        if n.endswith("_htm.xml"):
            return n
    for n in names:
        if n.endswith(".xml") and "htm" in n:
            return n

    def _is_linkbase_xml(name: str) -> bool:
        lower = name.lower()
        return lower.endswith(("_pre.xml", "_lab.xml", "_cal.xml", "_def.xml"))

    legacy_candidates = [
        n
        for n in names
        if n.endswith(".xml")
        and not _is_linkbase_xml(n)
        and n.lower() not in ("filingsummary.xml",)
    ]
    if not legacy_candidates:
        return None

    def _score(name: str) -> tuple:
        lower = name.lower()
        m = re.search(r"[-_]\d{8}\.xml$", lower)
        preferred = 0 if m else 1
        return (preferred, len(name))

    legacy_candidates.sort(key=_score)
    return legacy_candidates[0]


def pick_exhibit_files(items: List[Dict]) -> List[str]:
    names = [it.get("name", "") for it in items if isinstance(it, dict)]
    exhibits = []
    for n in names:
        if "dex99" in n.lower() and n.endswith(".htm"):
            exhibits.append(n)
    return sorted(exhibits)


def pick_taxonomy_files(items: List[Dict]) -> Dict[str, str]:
    names = [it.get("name", "") for it in items if isinstance(it, dict)]
    result: Dict[str, str] = {}
    for n in names:
        if n.endswith(".xsd") and not n.startswith("http"):
            result["schema"] = n
            break
    for n in names:
        if "_pre.xml" in n:
            result["presentation"] = n
            break
    for n in names:
        if "_cal.xml" in n:
            result["calculation"] = n
            break
    for n in names:
        if "_def.xml" in n:
            result["definition"] = n
            break
    for n in names:
        if "_lab.xml" in n:
            result["label"] = n
            break
    return result


def normalize_form(form: str) -> str:
    f = form.strip().upper().replace(" ", "")
    if f == "10K":
        return "10-K"
    if f == "10Q":
        return "10-Q"
    if f == "6K":
        return "6-K"
    if f == "20F":
        return "20-F"
    return f


def filter_filings(
    submissions: Dict,
    forms: List[str],
    start: dt.date,
    end: dt.date,
    headers: Dict[str, str],
    sleep_sec: float,
) -> List[Dict]:
    form_set = {normalize_form(f) for f in forms}
    out = []
    recent = submissions.get("filings", {}).get("recent", {})
    out.extend(_extract_filings_from_data(recent, form_set, start, end))
    files_list = submissions.get("filings", {}).get("files", [])
    if files_list:
        base_url = "https://data.sec.gov/submissions/"
        for file_info in files_list:
            if not isinstance(file_info, dict):
                continue
            filename = file_info.get("name", "")
            if not filename:
                continue
            file_url = base_url + filename
            try:
                time.sleep(sleep_sec)
                print(f"[info] fetching historical filings: {filename}")
                file_data = http_get_json(file_url, headers=headers)
                out.extend(_extract_filings_from_data(file_data, form_set, start, end))
            except Exception as e:
                print(f"[warn] failed to fetch {file_url}: {e}")
    return out


def _extract_filings_from_data(
    data: Dict, allowed_forms: set[str], start: dt.date, end: dt.date
) -> List[Dict]:
    form_values = data.get("form", [])
    filing_dates = data.get("filingDate", [])
    accessions = data.get("accessionNumber", [])
    primary_docs = data.get("primaryDocument", [])
    report_dates = data.get("reportDate", [])

    out = []
    n = min(len(form_values), len(filing_dates), len(accessions), len(primary_docs))
    for i in range(n):
        if normalize_form(str(form_values[i])) not in allowed_forms:
            continue
        fd = parse_date(filing_dates[i])
        if fd < start or fd > end:
            continue
        out.append(
            {
                "form": form_values[i],
                "filingDate": filing_dates[i],
                "reportDate": report_dates[i] if i < len(report_dates) else "",
                "accessionNumber": accessions[i],
                "primaryDocument": primary_docs[i],
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Download SEC iXBRL HTML and extracted XBRL XML for filings."
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ticker", help="Stock ticker, e.g., CME")
    g.add_argument("--cik", help="CIK numeric, e.g., 1156375 (leading zeros optional)")
    ap.add_argument(
        "--form", required=True, nargs="+", help="Filing type(s), e.g., 10-Q 10-K"
    )
    ap.add_argument(
        "--start", required=True, help="Start filing date (YYYY-MM-DD), inclusive"
    )
    ap.add_argument(
        "--end",
        help="End filing date (YYYY-MM-DD), inclusive. Defaults to today if not specified.",
    )
    ap.add_argument(
        "--out",
        default=DEFAULT_OUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUT_DIR})",
    )
    ap.add_argument(
        "--user-agent",
        dest="user_agent",
        default=None,
        help=(
            "SEC User-Agent. If omitted, uses env SEC_USER_AGENT, otherwise falls back to "
            f"default: {DEFAULT_USER_AGENT}"
        ),
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SEC,
        help="Sleep seconds between requests",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Force overwrite existing files. If False, check remote file status via HTTP HEAD request.",
    )
    args = ap.parse_args()

    global USER_AGENTS
    USER_AGENTS = user_agent_values(args.user_agent)
    headers = {
        "Accept-Encoding": "gzip, deflate",
    }

    start = parse_date(args.start, is_end=False)
    end = parse_date(args.end, is_end=True) if args.end else dt.date.today()
    if end < start:
        raise SystemExit("Error: --end must be >= --start")

    try:
        if args.ticker:
            cik = ticker_to_cik(args.ticker, headers=headers)
            cik_or_ticker_for_browse = args.ticker.upper()
        else:
            cik = str(args.cik).strip()
            cik_or_ticker_for_browse = cik

        cik10 = cik_to_10digits(cik)

        forms = [normalize_form(f) for f in args.form]
        allowed_forms = {"10-Q", "10-K", "6-K", "20-F"}
        bad = [f for f in forms if f not in allowed_forms]
        if bad:
            raise SystemExit(
                f"Error: unsupported --form value(s): {bad}. Allowed: {sorted(allowed_forms)}"
            )

        for ff in forms:
            browse_url = BROWSE_EDGAR_TEMPLATE.format(
                cik_or_ticker=cik_or_ticker_for_browse, form=ff
            )
            print(f"[info] browse-edgar URL ({ff}): {browse_url}")

        submissions_url = SEC_SUBMISSIONS_URL.format(cik10=cik10)
        print(f"[info] submissions JSON: {submissions_url}")
        submissions = http_get_json(submissions_url, headers=headers)
    except RequestException as e:
        print(
            "[error] Unable to fetch SEC data due to network/SSL restrictions. "
            "Provide local PDFs or configure SEC_USER_AGENT/HTTP(S)_PROXY and retry."
        )
        raise SystemExit(2) from e

    time.sleep(args.sleep)

    filings = filter_filings(
        submissions,
        forms=forms,
        start=start,
        end=end,
        headers=headers,
        sleep_sec=args.sleep,
    )
    print(f"[info] matched filings: {len(filings)}")
    if not filings:
        return

    filings = sorted(
        filings,
        key=lambda x: (
            normalize_form(str(x.get("form", ""))),
            str(x.get("filingDate", "")),
            str(x.get("accessionNumber", "")),
        ),
    )

    out_base = Path(args.out).expanduser().resolve()
    out_base.mkdir(parents=True, exist_ok=True)

    cik_int = str(int(cik))

    download_failures: List[Dict[str, str]] = []

    for f in filings:
        acc = f["accessionNumber"]
        acc_nodash = accession_no_nodash(acc)
        filing_date = f["filingDate"]
        report_date = f.get("reportDate") or ""
        primary_doc = f["primaryDocument"]

        filing_form = normalize_form(str(f.get("form") or ""))

        filing_dir_url = ARCHIVES_BASE.format(cik=cik_int, acc_nodash=acc_nodash)
        index_json_url = ARCHIVES_INDEX_JSON.format(cik=cik_int, acc_nodash=acc_nodash)

        safe_report = report_date if report_date else "NA"
        folder_name = f"{filing_form}_{filing_date}_report_{safe_report}_{acc}"
        folder_name = re.sub(r"[^\w\-.=]+", "_", folder_name)
        out_dir = (
            out_base
            / (args.ticker.upper() if args.ticker else f"CIK{cik10}")
            / folder_name
        )
        out_dir.mkdir(parents=True, exist_ok=True)

        print(
            f"\n[filing] {filing_form} | filingDate={filing_date} | reportDate={report_date} | accession={acc}"
        )
        print(f"[info] archive dir: {filing_dir_url}")

        primary_url = filing_dir_url + primary_doc
        html_out = out_dir / primary_doc
        if should_download(primary_url, headers, html_out, args.overwrite):
            try:
                http_download(primary_url, headers=headers, out_path=html_out)
                print(f"[ok] HTML: {primary_doc}")
            except Exception as e:
                print(f"[warn] failed to download HTML {primary_url}: {e}")
                download_failures.append(
                    {
                        "form": filing_form,
                        "filingDate": str(filing_date),
                        "reportDate": str(report_date),
                        "accession": str(acc),
                        "type": "HTML",
                        "name": str(primary_doc),
                        "url": str(primary_url),
                        "error": str(e),
                    }
                )
        else:
            print(f"[skip] HTML: {primary_doc}")

        time.sleep(args.sleep)

        extracted_name = None
        taxonomy_files: Dict[str, str] = {}
        exhibit_files: List[str] = []
        try:
            idx = http_get_json(index_json_url, headers=headers)
            items = idx.get("directory", {}).get("item", []) or []
            extracted_name = pick_extracted_instance_xml(items)
            taxonomy_files = pick_taxonomy_files(items)
            if filing_form == "6-K":
                exhibit_files = pick_exhibit_files(items)
        except Exception as e:
            print(f"[warn] failed to read index.json {index_json_url}: {e}")
            download_failures.append(
                {
                    "form": filing_form,
                    "filingDate": str(filing_date),
                    "reportDate": str(report_date),
                    "accession": str(acc),
                    "type": "INDEX_JSON",
                    "name": "index.json",
                    "url": str(index_json_url),
                    "error": str(e),
                }
            )

        time.sleep(args.sleep)

        if extracted_name:
            xml_url = filing_dir_url + extracted_name
            xml_out = out_dir / extracted_name
            if should_download(xml_url, headers, xml_out, args.overwrite):
                try:
                    http_download(xml_url, headers=headers, out_path=xml_out)
                    print(f"[ok] XBRL instance XML: {extracted_name}")
                except Exception as e:
                    print(f"[warn] failed to download XML {xml_url}: {e}")
                    download_failures.append(
                        {
                            "form": filing_form,
                            "filingDate": str(filing_date),
                            "reportDate": str(report_date),
                            "accession": str(acc),
                            "type": "XBRL_INSTANCE_XML",
                            "name": str(extracted_name),
                            "url": str(xml_url),
                            "error": str(e),
                        }
                    )
            else:
                print(f"[skip] XBRL instance XML: {extracted_name}")
        else:
            print("[warn] no extracted *_htm.xml found in index.json")

        for tax_type, tax_name in taxonomy_files.items():
            tax_url = filing_dir_url + tax_name
            tax_out = out_dir / tax_name
            if should_download(tax_url, headers, tax_out, args.overwrite):
                try:
                    http_download(tax_url, headers=headers, out_path=tax_out)
                    print(f"[ok] {tax_type.capitalize()} linkbase: {tax_name}")
                except Exception as e:
                    print(f"[warn] failed to download {tax_type} {tax_url}: {e}")
                    download_failures.append(
                        {
                            "form": filing_form,
                            "filingDate": str(filing_date),
                            "reportDate": str(report_date),
                            "accession": str(acc),
                            "type": f"TAXONOMY_{tax_type.upper()}",
                            "name": str(tax_name),
                            "url": str(tax_url),
                            "error": str(e),
                        }
                    )
            else:
                print(f"[skip] {tax_type.capitalize()} linkbase: {tax_name}")
            time.sleep(args.sleep)

        for exhibit_name in exhibit_files:
            exhibit_url = filing_dir_url + exhibit_name
            exhibit_out = out_dir / exhibit_name
            if should_download(exhibit_url, headers, exhibit_out, args.overwrite):
                try:
                    http_download(exhibit_url, headers=headers, out_path=exhibit_out)
                    print(f"[ok] Exhibit: {exhibit_name}")
                except Exception as e:
                    print(f"[warn] failed to download exhibit {exhibit_url}: {e}")
                    download_failures.append(
                        {
                            "form": filing_form,
                            "filingDate": str(filing_date),
                            "reportDate": str(report_date),
                            "accession": str(acc),
                            "type": "EXHIBIT",
                            "name": str(exhibit_name),
                            "url": str(exhibit_url),
                            "error": str(e),
                        }
                    )
            else:
                print(f"[skip] Exhibit: {exhibit_name}")
            time.sleep(args.sleep)

        meta = {
            "ticker": args.ticker.upper() if args.ticker else None,
            "cik": cik_int,
            "cik10": cik10,
            "form": filing_form,
            "filingDate": filing_date,
            "reportDate": report_date,
            "accessionNumber": acc,
            "archiveDir": filing_dir_url,
            "primaryDocument": primary_doc,
            "extractedInstanceXML": extracted_name,
            "taxonomyFiles": taxonomy_files,
            "exhibitFiles": exhibit_files,
            "browseEdgarURL": BROWSE_EDGAR_TEMPLATE.format(
                cik_or_ticker=cik_or_ticker_for_browse, form=filing_form
            ),
            "submissionsURL": submissions_url,
            "indexJSON": index_json_url,
            "userAgentUsed": USER_AGENTS[0] if USER_AGENTS else DEFAULT_USER_AGENT,
        }
        with open(out_dir / "meta.json", "w", encoding="utf-8") as fw:
            json.dump(meta, fw, ensure_ascii=False, indent=2)

        time.sleep(args.sleep)

    print(f"\n[done] saved to: {out_base}")

    if download_failures:
        print(f"\n[summary] failed downloads: {len(download_failures)}")
        for it in download_failures:
            print(
                "[fail] "
                + f"{it.get('form')} filingDate={it.get('filingDate')} reportDate={it.get('reportDate')} accession={it.get('accession')} "
                + f"type={it.get('type')} name={it.get('name')} url={it.get('url')} err={it.get('error')}"
            )
    else:
        print("\n[summary] all downloads succeeded")


if __name__ == "__main__":
    main()
