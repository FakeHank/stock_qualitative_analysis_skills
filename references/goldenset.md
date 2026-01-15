# Goldenset (format regression)

## Case A
- Company: Apple Inc.
- Ticker/Exchange: AAPL / NASDAQ
- Market: US
- Sources: SEC EDGAR (10-K/10-Q)
- Expected: full report structure exactly as `assets/report-template.md`

## Case B
- Company: Trip.com Group Limited
- Ticker/Exchange: TCOM / NASDAQ
- Market: US (China ADR)
- Sources: SEC EDGAR (20-F, 6-K) + company IR
- Expected: full report structure + VIE mentions only if cited

## Case C
- Company: Hong Kong Exchanges and Clearing Limited
- Ticker/Exchange: 0388.HK / HKEX
- Market: HK
- Sources: user-provided annual/interim reports (PDF)
- Expected: full report structure, no SEC-specific assumptions
