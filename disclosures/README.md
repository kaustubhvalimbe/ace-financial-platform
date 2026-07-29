# Portfolio Disclosure Pipeline (Stock Intelligence data)

Turns each AMC's monthly portfolio disclosure spreadsheet into `hd-data.json`,
the file `stock-intelligence.html` and `portfolio-xray.html` read.

## One-time setup

```
pip install openpyxl
```

## Every month

1. Go to **https://www.amfiindia.com/online-center/portfolio-disclosure**
   and download the monthly portfolio disclosure file for each AMC you track
   (currently: HDFC, SBI, Nippon, ICICI Pru, Kotak, Axis, Motilal Oswal,
   Edelweiss, Sundaram, UTI, ABSL, DSP, Bajaj Finserv). All AMCs publish in
   the same SEBI-mandated columns (ISIN, Name of Instrument, Industry/Rating,
   Quantity, Market Value, % to NAV), so the parser doesn't care which AMC
   a file came from beyond the filename.

2. Save each file into `disclosures/raw/<YYYY-MM>/`, named after the AMC,
   e.g.:
   ```
   disclosures/raw/2026-08/HDFC MF.xlsx
   disclosures/raw/2026-08/SBI MF.xlsx
   disclosures/raw/2026-08/ICICI Pru MF.xlsx
   ```
   (underscores also work: `HDFC_MF.xlsx`)

3. Run:
   ```
   python disclosures/build_hd_data.py 2026-08
   ```
   This backs up the current `hd-data.json` into `disclosures/`, then writes
   the new one. It prints a summary of how many holding rows it found per
   file.

4. If any stock or industry label couldn't be matched, the script writes
   `disclosures/review/2026-08-unmapped-symbols.csv` and/or
   `...-unmapped-sectors.csv`. Open these:
   - **unmapped-symbols.csv**: add the correct NSE symbol for each new stock
     name to `disclosures/lookups/stock_symbols.json` (`"Stock Name": "SYMBOL"`).
   - **unmapped-sectors.csv**: add the AMC's raw label -> your preferred
     sector name to `disclosures/lookups/sector_map.json`.
   Re-run step 3 to pick up the additions. This only happens for genuinely
   new stocks/labels — the lookups only grow, so most months need zero edits.

5. Sanity-check `hd-data.json` (stock count, a few known holdings look right),
   then deploy as usual (`deploy.sh` / `deploy.bat`).

## Files

- `build_hd_data.py` — the parser/aggregator. Auto-detects header rows and
  scheme blocks inside each AMC's file, so it tolerates the usual layout
  differences between AMCs (one sheet per scheme vs. one sheet with repeated
  "Name of the Scheme :" blocks).
- `lookups/stock_symbols.json` — stock name -> NSE symbol. Seeded from the
  ~1,640 stocks already in the current `hd-data.json`.
- `lookups/sector_map.json` — AMC industry label -> the sector name shown on
  the site. Seeded from the sectors already in use, plus common label
  variants (e.g. "Banks" -> "Banking", "Petroleum Products" -> "Oil & Gas").
- `raw/<YYYY-MM>/` — the AMC files you downloaded that month (not committed
  to keep the repo small — see `.gitignore` note below).
- `review/` — CSVs flagging anything the parser couldn't confidently map.

## Notes

- Rows are only kept if they're clearly an equity holding (ISIN starts with
  `INE` and the label isn't cash/TREPS/debt/money-market). Debt, gilt and
  liquid schemes will correctly show zero equity rows.
- If you'd rather not commit the raw monthly AMC downloads to git, add
  `disclosures/raw/` to a `.gitignore` file in the site root.
