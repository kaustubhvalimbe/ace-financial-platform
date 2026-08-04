#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==================================================================
  monthly_report.py  -  Ace Financial Services
  Monthly "Fund Movements Report" (precise, from nav.db)
==================================================================
  Reads nav.db (built by sync_navdb.py) and writes a dated,
  publish-ready HTML report into your WEBSITE folder.

  Precision:
   - categories match your Fund Discovery tool (same rules),
   - GROWTH plans only (IDCW / dividend / dead variants excluded),
   - returns from real NAV dates in your data:
        1M, 6M   = absolute
        1Y,2Y,3Y,5Y = annualised (CAGR)
   - a period shows "-" if a fund/category is too young for it.

  RUN (in the Amfi Data folder, after sync_navdb.py):
        python monthly_report.py

  Needs nav.db present. Built-in modules only.
==================================================================
"""

import os
import sqlite3
import datetime as dt
from statistics import median

DB = "nav.db"
OUTPUT_DIR = r"C:\Kv\Ace\AIS\Claude Development\AFS Website\Ver 61"

# equity sub-categories used for the leaders/laggards + commentary
EQUITY_SUBCATS = {"Multi Cap", "Flexi Cap", "Large Cap", "Large & Mid Cap", "Mid Cap",
                  "Small Cap", "Dividend Yield", "Value", "Contra", "Focused",
                  "Sectoral / Thematic", "Diversified Equity"}


# ── categorisation: ported verbatim from fund-discovery-v2.html ──
def det_cat(name):
    """Broad SEBI group: equity / debt / hybrid / elss / index / fof / solution / unknown."""
    u = name.upper()
    if "SEGREGATED" in u: return "unknown"                     # broken side-pockets
    if any(k in u for k in ("ELSS", "TAX SAVER", "TAX SAVING", "LONG TERM EQUITY")): return "elss"
    if any(k in u for k in ("RETIREMENT", "PENSION", "CHILDREN", "CHILD ", "CHILD-", "GIFT")): return "solution"
    if any(k in u for k in ("FUND OF FUND", "FUND OF FUNDS", " FOF")): return "fof"
    if (("INDEX" in u or "ETF" in u or "BEES" in u or "SENSEX" in u) and "FUND OF" not in u): return "index"
    if any(k in u for k in ("AGGRESSIVE HYBRID", "CONSERVATIVE HYBRID", "BALANCED HYBRID",
                            "BALANCED ADVANTAGE", "DYNAMIC ASSET", "MULTI ASSET", "MULTI-ASSET",
                            "EQUITY SAVINGS", "ARBITRAGE", "HYBRID", "BALANCED",
                            "EQUITY & DEBT", "EQUITY AND DEBT")): return "hybrid"
    if any(k in u for k in ("OVERNIGHT", "LIQUID", "MONEY MARKET", "ULTRA SHORT", "LOW DURATION",
                            "SHORT DURATION", "SHORT TERM", "MEDIUM TO LONG", "MEDIUM DURATION",
                            "MEDIUM TERM", "LONG DURATION", "DYNAMIC BOND", "CORPORATE BOND",
                            "CORPORATE", "CREDIT RISK", "BANKING AND PSU", "BANKING & PSU",
                            "PSU DEBT", "GILT", "G-SEC", "GSEC", "GOVERNMENT SECURIT",
                            "FLOATER", "FLOATING RATE", "DEBT", "BOND", "INCOME", "DURATION",
                            "TREASURY", "SDL", "FIXED MATURITY", "FMP",
                            "SAVINGS FUND", "SAVING FUND")): return "debt"
    if any(k in u for k in ("MULTI CAP", "MULTICAP", "FLEXI", "LARGE & MID", "LARGE AND MID",
                            "LARGE CAP", "LARGECAP", "MID CAP", "MIDCAP", "SMALL CAP", "SMALLCAP",
                            "DIVIDEND YIELD", "VALUE", "CONTRA", "FOCUSED", "SECTOR", "THEMATIC",
                            "BLUECHIP", "TOP 100", "TOP100", "EQUITY", "OPPORTUNIT",
                            "BUSINESS CYCLE", "CONSUMPTION", "INFRASTRUCTURE", "INFRA", "PHARMA",
                            "HEALTHCARE", "TECHNOLOGY", "DIGITAL", "BANKING", "FINANCIAL",
                            "FMCG", "MNC", "EMERGING", "SPECIAL SITUATION", "QUANT ",
                            "MANUFACTURING", "ESG", "TRANSPORT", "ENERGY", "METAL", "AUTO",
                            "DEFENCE", "REALTY", "REAL ESTATE", "PSU")): return "equity"
    return "unknown"


def det_nat(name):
    u = name.upper()
    if "SEGREGATED" in u: return "idcw"     # exclude broken side-pockets
    if "IDCW" in u: return "idcw"
    if "DIVIDEND" in u: return "idcw"
    if " PAYOUT" in u or "REINVESTMENT" in u: return "idcw"
    if (" DIV" in u or "-DIV" in u) and "DIVIDEND YIELD" not in u: return "idcw"
    if "WEEKLY" in u or "MONTHLY DIV" in u or "QUARTERLY DIV" in u: return "idcw"
    return "growth"


def sub_cat(name, cat):
    """Exact SEBI/AMFI sub-category, inferred from the scheme name."""
    u = name.upper()
    if cat == "elss":
        return "ELSS"
    if cat == "solution":
        if "RETIREMENT" in u or "PENSION" in u: return "Retirement"
        if "CHILD" in u or "GIFT" in u: return "Children's"
        return "Solution Oriented"
    if cat == "equity":
        if "LARGE & MID" in u or "LARGE AND MID" in u or "EMERGING BLUECHIP" in u: return "Large & Mid Cap"
        if "MULTI CAP" in u or "MULTICAP" in u: return "Multi Cap"
        if "FLEXI" in u: return "Flexi Cap"
        if "SMALL CAP" in u or "SMALLCAP" in u: return "Small Cap"
        if "MID CAP" in u or "MIDCAP" in u: return "Mid Cap"
        if "LARGE CAP" in u or "LARGECAP" in u or "BLUECHIP" in u or "TOP 100" in u or "TOP100" in u: return "Large Cap"
        if "DIVIDEND YIELD" in u: return "Dividend Yield"
        if "CONTRA" in u: return "Contra"
        if "VALUE" in u: return "Value"
        if "FOCUSED" in u: return "Focused"
        if any(k in u for k in ("SECTOR", "THEMATIC", "INFRA", "PHARMA", "HEALTHCARE", "TECH",
                                "DIGITAL", "BANKING", "FINANCIAL", "FMCG", "AUTO", "METAL",
                                "ENERGY", "POWER", "MANUFACTURING", "CONSUMPTION", "CONSUMER",
                                "MNC", "ESG", "TRANSPORT", "DEFENCE", "REALTY", "REAL ESTATE",
                                "BUSINESS CYCLE", "SPECIAL SITUATION", "OPPORTUNIT", "PSU",
                                "INTERNATIONAL", "GLOBAL", "NASDAQ", "US EQUITY")): return "Sectoral / Thematic"
        return "Diversified Equity"
    if cat == "hybrid":
        if "ARBITRAGE" in u: return "Arbitrage"
        if "BALANCED ADVANTAGE" in u or "DYNAMIC ASSET" in u or "BAF" in u: return "Balanced Advantage / DAA"
        if "AGGRESSIVE" in u: return "Aggressive Hybrid"
        if "CONSERVATIVE" in u: return "Conservative Hybrid"
        if "BALANCED HYBRID" in u: return "Balanced Hybrid"
        if "MULTI ASSET" in u or "MULTI-ASSET" in u: return "Multi Asset Allocation"
        if "EQUITY SAVINGS" in u: return "Equity Savings"
        return "Aggressive Hybrid"
    if cat == "debt":
        if "OVERNIGHT" in u: return "Overnight"
        if "LIQUID" in u: return "Liquid"
        if "MONEY MARKET" in u: return "Money Market"
        if "ULTRA SHORT" in u: return "Ultra Short Duration"
        if "LOW DURATION" in u: return "Low Duration"
        if "MEDIUM TO LONG" in u: return "Medium to Long Duration"
        if "MEDIUM DURATION" in u or "MEDIUM TERM" in u: return "Medium Duration"
        if "SHORT DURATION" in u or "SHORT TERM" in u: return "Short Duration"
        if "LONG DURATION" in u: return "Long Duration"
        if "DYNAMIC BOND" in u or ("DYNAMIC" in u and "BOND" in u): return "Dynamic Bond"
        if "CREDIT RISK" in u or "CREDIT OPPORT" in u: return "Credit Risk"
        if "CORPORATE" in u: return "Corporate Bond"
        if "BANKING AND PSU" in u or "BANKING & PSU" in u or "BANK & PSU" in u or "PSU DEBT" in u: return "Banking & PSU"
        if "GILT" in u and ("10" in u or "CONSTANT" in u): return "Gilt 10Y Constant"
        if "GILT" in u or "G-SEC" in u or "GSEC" in u or "GOVERNMENT SECURIT" in u: return "Gilt"
        if "FLOATER" in u or "FLOATING" in u: return "Floater"
        if "TREASURY" in u: return "Low Duration"
        if "FIXED MATURITY" in u or "FMP" in u: return "Fixed Maturity Plan"
        if "SAVING" in u: return "Short Duration"
        return "Debt (Other)"
    if cat == "index":
        if "GOLD" in u: return "Gold ETF/FoF"
        if "SILVER" in u: return "Silver ETF/FoF"
        if any(k in u for k in ("DEBT", "BOND", "GSEC", "G-SEC", "SDL", "LIQUID")): return "Debt Index/ETF"
        if "ETF" in u: return "ETF"
        return "Index Fund"
    if cat == "fof":
        if "GOLD" in u: return "Gold FoF"
        if "SILVER" in u: return "Silver FoF"
        if any(k in u for k in ("INTERNATIONAL", "OVERSEAS", "GLOBAL", "NASDAQ", "US ",
                                "JAPAN", "CHINA", "EUROPE", "EMERGING", "WORLD")): return "Overseas FoF"
        return "Domestic FoF"
    return "Unclassified"


# ── returns from real NAV dates (same engine as fund_returns_app) ──
PERIODS = [("1M", 30, "abs"), ("6M", 183, "abs"),
           ("1Y", 365, "cagr"), ("2Y", 730, "cagr"),
           ("3Y", 1095, "cagr"), ("5Y", 1826, "cagr")]


def fund_returns(cur, code, first_date, last_date):
    cur.execute("SELECT nav FROM nav WHERE scheme_code=? AND date=? LIMIT 1", (code, last_date))
    r = cur.fetchone()
    if not r or not r[0]:
        return None
    last_nav = r[0]
    ld = dt.date(*map(int, last_date.split("-")))
    fd = dt.date(*map(int, first_date.split("-")))
    out = {}
    for label, days, basis in PERIODS:
        target = ld - dt.timedelta(days=days)
        if fd > target:
            out[label] = None
            continue
        cur.execute("SELECT nav FROM nav WHERE scheme_code=? AND date<=? ORDER BY date DESC LIMIT 1",
                    (code, target.isoformat()))
        b = cur.fetchone()
        if not b or not b[0] or b[0] <= 0:
            out[label] = None
            continue
        base = b[0]
        if basis == "abs":
            val = (last_nav / base - 1) * 100
        else:
            yrs = days / 365.0
            val = ((last_nav / base) ** (1.0 / yrs) - 1.0) * 100
        out[label] = None if abs(val) > 900 else round(val, 2)
    return out, last_nav


def build():
    if not os.path.exists(DB):
        print("Cannot find", DB, "- run  python sync_navdb.py  first to build it.")
        return
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT MAX(date) FROM nav")
    latest = cur.fetchone()[0]
    if not latest:
        print("nav.db is empty - run sync_navdb.py.")
        return
    print("Latest date in database:", latest)
    print("Reading funds and computing returns...")

    cur.execute("SELECT scheme_code, scheme_name, first_date, last_date FROM funds")
    allfunds = cur.fetchall()
    qcur = con.cursor()

    funds = []
    for code, name, fdate, ldate in allfunds:
        if det_nat(name) != "growth":         # growth plans only
            continue
        cat = det_cat(name)
        sc = sub_cat(name, cat)
        res = fund_returns(qcur, code, fdate, ldate)
        if not res:
            continue
        rets, last_nav = res
        funds.append({"code": code, "name": name, "broad": cat, "cat": sc, "rets": rets})
    con.close()
    print("Processed {:,} growth funds.".format(len(funds)))

    # scoreboard: median per period per sub-category (>= 3 funds)
    groups = {}
    for f in funds:
        groups.setdefault(f["cat"], []).append(f)
    labels = [p[0] for p in PERIODS]
    scoreboard = []
    for cat, rows in groups.items():
        onem = [r["rets"]["1M"] for r in rows if r["rets"]["1M"] is not None]
        if len(onem) < 3:
            continue
        row = {"cat": cat, "n": len(rows)}
        for lab in labels:
            vals = [r["rets"][lab] for r in rows if r["rets"][lab] is not None]
            row[lab] = round(median(vals), 2) if vals else None
        scoreboard.append(row)
    scoreboard.sort(key=lambda x: (x["1M"] is not None, x["1M"] or -999), reverse=True)

    # leaders / laggards among equity growth funds, by 1M
    eq = [f for f in funds if f["cat"] in EQUITY_SUBCATS and f["rets"]["1M"] is not None]
    eq.sort(key=lambda x: x["rets"]["1M"], reverse=True)
    leaders = eq[:12]
    laggards = sorted(eq, key=lambda x: x["rets"]["1M"])[:12]

    ld = dt.date(*map(int, latest.split("-")))
    write_html(ld.strftime("%B %Y"), latest, scoreboard, leaders, laggards)
    build_index()


# ── HTML ─────────────────────────────────────────────────────────
def fmtpct(v):
    return "{}{:.1f}%".format("+" if v >= 0 else "", v)


def rcell(v):
    if v is None:
        return '<td class="na">-</td>'
    cls = "pos" if v >= 0 else "neg"
    return '<td class="r {}">{}{}%</td>'.format(cls, "+" if v >= 0 else "", ("%.2f" % v))


def build_commentary(month_label, scoreboard):
    eq = [s for s in scoreboard if s["cat"] in EQUITY_SUBCATS and s["1M"] is not None]
    if not eq:
        return "Category performance for {} is summarised in the tables below.".format(month_label)
    by = sorted(eq, key=lambda x: x["1M"], reverse=True)
    top, bot = by[0], by[-1]
    parts = ["Over the last month, <b>{}</b> funds led with a median return of {}, while <b>{}</b> funds trailed at {}.".format(
        top["cat"], fmtpct(top["1M"]), bot["cat"], fmtpct(bot["1M"]))]
    riskier = {"Small Cap", "Mid Cap", "Thematic/Sectoral"}
    steadier = {"Large Cap", "Bluechip", "Flexi Cap"}
    if top["cat"] in riskier and bot["cat"] in steadier:
        parts.append("Higher-risk categories running ahead of steadier large-caps means the period rewarded risk-taking.")
    elif top["cat"] in steadier and bot["cat"] in riskier:
        parts.append("Steadier large-caps ahead of the racier small- and mid-caps points to a more defensive month.")
    with5 = [s for s in eq if s.get("5Y") is not None]
    if with5:
        best5 = sorted(with5, key=lambda x: x["5Y"], reverse=True)[0]
        if best5["cat"] != top["cat"]:
            parts.append("The longer view matters more: over five years the median leader has been <b>{}</b> ({} CAGR), not this month's front-runner - one month rarely predicts the next.".format(best5["cat"], fmtpct(best5["5Y"])))
    parts.append("A single month says little on its own. The gap between categories is exactly why staying diversified across market caps - rather than chasing the latest leader - has historically served long-term investors better.")
    return " ".join(parts)


INDEX_TEMPLATE = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Monthly Fund Movements Reports | Ace Financial Services</title>
<meta name="description" content="Monthly mutual fund movement reports by Ace Financial Services - how fund categories moved each month, with the long-cycle context most reports skip. AMFI Registered MFD, Pune.">
<link rel="canonical" href="https://acefinservices.com/monthly-reports.html">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Plus Jakarta Sans','Segoe UI',sans-serif;color:#1a1240;background:#f7f6ff;line-height:1.6}
.topbar{background:#fff;border-bottom:2px solid #d4eda0;padding:9px 16px;display:flex;gap:8px;position:sticky;top:0;z-index:20}
.tb{display:inline-block;background:#f0effe;border:1.5px solid #d6d2f5;color:#3c3197;border-radius:8px;padding:6px 13px;font-size:13px;font-weight:800;text-decoration:none}
.tb:hover{background:#3c3197;color:#fff}
.hero{background:linear-gradient(135deg,#2d2478,#3c3197,#5a4fd8);padding:44px 24px;text-align:center;color:#fff}
.hero .kick{font-size:12px;color:#b8e05a;letter-spacing:2px;text-transform:uppercase;font-weight:700}
.hero h1{font-family:Georgia,serif;font-size:34px;font-weight:900;margin:8px 0}
.hero .sub{color:rgba(255,255,255,.85);font-size:14px;max-width:640px;margin:0 auto}
.wrap{max-width:820px;margin:0 auto;padding:28px 18px 50px}
.grid{display:grid;gap:14px}
.rep{display:block;background:#fff;border:1.5px solid #e4e2f0;border-left:5px solid #5a8a10;border-radius:12px;padding:16px 20px;text-decoration:none}
.rep:hover{box-shadow:0 8px 22px rgba(60,49,151,.12)}
.rep-m{font-family:Georgia,serif;font-size:19px;font-weight:800;color:#3c3197}
.rep-s{font-size:13px;color:#4b5563;margin:3px 0 6px}
.rep-go{font-size:12px;font-weight:800;color:#5a8a10}
.disc{font-size:11px;color:#9ca3af;border-left:3px solid #d97706;padding-left:12px;margin-top:28px;line-height:1.7}
</style></head><body>
<div class="topbar"><a href="index.html" class="tb">HOME</a><a href="security.html" class="tb">🔒 Security</a></div>
<div class="hero"><div class="kick">Ace Financial Services</div>
  <h1>Monthly Fund Movements Reports</h1>
  <div class="sub">Each month: how fund categories moved, the leaders and laggards, and the long-cycle context most reports skip.</div></div>
<div class="wrap"><div class="grid">
{{CARDS}}</div>
<div class="disc"><b>Disclaimer:</b> These reports are for information and education only and are not recommendations to buy or sell any scheme. One month's performance is not indicative of future returns. Mutual fund investments are subject to market risks; read all scheme related documents carefully. Ace Financial Services - AMFI Registered MFD (ARN-110832).</div>
</div></body></html>"""


def build_index():
    import glob, re
    folder = OUTPUT_DIR if (OUTPUT_DIR and os.path.isdir(OUTPUT_DIR)) else "."
    files = glob.glob(os.path.join(folder, "fund-report-*.html"))
    editions = []
    for fp in files:
        fn = os.path.basename(fp)
        if "SAMPLE" in fn.upper():
            continue
        try:
            txt = open(fp, encoding="utf-8").read(3000)
        except Exception:
            txt = ""
        m = re.search(r"<!--META month=(.*?)\|top=(.*?)\|topret=(.*?)-->", txt)
        if m:
            month, top, topret = m.group(1), m.group(2), m.group(3)
        else:
            mm = re.search(r"(\d{4})-(\d{2})", fn)
            month = (dt.date(int(mm.group(1)), int(mm.group(2)), 1).strftime("%B %Y") if mm else fn)
            top, topret = "", ""
        mm = re.search(r"(\d{4})-(\d{2})", fn)
        key = mm.group(0) if mm else fn
        summary = ("{} funds led (median {})".format(top, topret) if top
                   else "Category scoreboard, leaders and laggards, with long-cycle context.")
        editions.append((key, fn, month, summary))
    editions.sort(reverse=True)
    cards = ""
    for key, fn, month, summary in editions:
        cards += ('      <a class="rep" href="{fn}"><div class="rep-m">{month}</div>'
                  '<div class="rep-s">{summary}</div><div class="rep-go">Read report &rarr;</div></a>\n'
                  ).format(fn=fn, month=month, summary=summary)
    if not cards:
        cards = '      <div style="color:#9ca3af;padding:20px">No reports yet.</div>\n'
    page = INDEX_TEMPLATE.replace("{{CARDS}}", cards)
    out = os.path.join(folder, "monthly-reports.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("Index updated:", os.path.abspath(out), "({} edition(s))".format(len(editions)))


def write_html(month_label, as_of, scoreboard, leaders, laggards):
    top_sb = next((s for s in scoreboard if s["cat"] in EQUITY_SUBCATS and s["1M"] is not None), None)
    meta = "<!--META month={}|top={}|topret={}-->".format(
        month_label, top_sb["cat"] if top_sb else "", fmtpct(top_sb["1M"]) if top_sb else "")

    def sb_rows():
        out = ""
        for s in scoreboard:
            out += "<tr><td class='l'>{}</td><td class='c'>{}</td>{}{}{}{}{}{}</tr>".format(
                s["cat"], s["n"], rcell(s["1M"]), rcell(s["6M"]), rcell(s["1Y"]),
                rcell(s["2Y"]), rcell(s["3Y"]), rcell(s["5Y"]))
        return out

    def fund_rows(rows):
        out = ""
        for r in rows:
            out += "<tr><td class='l'>{}</td><td class='c'><span class='cat'>{}</span></td>{}{}</tr>".format(
                r["name"][:52], r["cat"], rcell(r["rets"]["1M"]), rcell(r["rets"]["3Y"]))
        return out

    auto = build_commentary(month_label, scoreboard)
    html = """<!DOCTYPE html>{meta}<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Fund Movements Report - {month} | Ace Financial Services</title>
<meta name="description" content="How mutual fund categories moved in {month}, which funds led and lagged, and the long-cycle context. By Ace Financial Services, AMFI Registered MFD, Pune.">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Plus Jakarta Sans','Segoe UI',sans-serif;color:#1a1240;background:#f7f6ff;line-height:1.6}}
.topbar{{background:#fff;border-bottom:2px solid #d4eda0;padding:9px 16px;display:flex;gap:8px;position:sticky;top:0;z-index:20}}
.tb{{display:inline-block;background:#f0effe;border:1.5px solid #d6d2f5;color:#3c3197;border-radius:8px;padding:6px 13px;font-size:13px;font-weight:800;text-decoration:none}}
.tb:hover{{background:#3c3197;color:#fff}}
.hero{{background:linear-gradient(135deg,#2d2478,#3c3197,#5a4fd8);padding:38px 24px;text-align:center;color:#fff}}
.hero .kick{{font-size:12px;color:#b8e05a;letter-spacing:2px;text-transform:uppercase;font-weight:700}}
.hero h1{{font-family:Georgia,serif;font-size:32px;font-weight:900;margin:6px 0}}
.hero .sub{{color:rgba(255,255,255,.85);font-size:14px}}
.wrap{{max-width:960px;margin:0 auto;padding:26px 18px 50px}}
.commentary{{background:#f5fce8;border:1.5px solid #d4eda0;border-radius:14px;padding:18px 20px;margin:20px 0}}
.commentary h3{{font-family:Georgia,serif;color:#2d6b0e;font-size:17px;margin-bottom:6px}}
.commentary p{{color:#3d3b5c;font-size:13.5px;line-height:1.7}}
h2{{font-family:Georgia,serif;font-size:22px;color:#3c3197;margin:30px 0 6px}}
.note{{font-size:12px;color:#9ca3af;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1.5px solid #e4e2f0;border-radius:12px;overflow:hidden;font-size:12.5px}}
th,td{{padding:8px 9px;border-bottom:1px solid #f0eeff;text-align:right;white-space:nowrap}}
th{{background:#f0eeff;color:#3c3197;font-size:10.5px;text-transform:uppercase;letter-spacing:.2px}}
th.l,td.l{{text-align:left}} th.c,td.c{{text-align:center}}
td.l{{font-weight:700}} .r{{font-family:'Consolas',monospace;font-weight:600}}
.pos{{color:#5a8a10}} .neg{{color:#dc2626}} .na{{color:#d1d5db}}
.cat{{background:#f0eeff;color:#3c3197;font-size:10px;font-weight:700;padding:2px 8px;border-radius:9px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
@media(max-width:820px){{.two{{grid-template-columns:1fr}}.hero h1{{font-size:25px}}table{{font-size:11px}}}}
.disc{{font-size:11px;color:#9ca3af;border-left:3px solid #d97706;padding-left:12px;margin-top:28px;line-height:1.7}}
.foot{{margin-top:16px;font-size:12px;color:#6b7280}} .foot a{{color:#3c3197;font-weight:700;text-decoration:none}}
</style></head><body>
<div class="topbar"><a href="index.html" class="tb">HOME</a><a href="monthly-reports.html" class="tb">All Reports</a><a href="security.html" class="tb">🔒 Security</a></div>
<div class="hero">
  <div class="kick">Fund Movements Report</div>
  <h1>{month}</h1>
  <div class="sub">How fund categories moved - with the long-cycle context most reports skip - data as on {asof}</div>
</div>
<div class="wrap">
  <div class="commentary">
    <h3>This month, in brief</h3>
    <p>{auto}</p>
    <p style="margin-top:10px;font-size:11px;color:#9ca3af;font-style:italic;">Prepared automatically from published NAVs by Ace Financial Services.</p>
  </div>

  <h2>Category Scoreboard</h2>
  <div class="note">Median return per sub-category (Growth plans only). 1M &amp; 6M are absolute; 1Y and longer are annualised (CAGR). "-" means too few funds or too little history.</div>
  <table>
    <thead><tr><th class="l">Category</th><th class="c">Funds</th><th class="r">1M</th><th class="r">6M</th><th class="r">1Y</th><th class="r">2Y</th><th class="r">3Y</th><th class="r">5Y</th></tr></thead>
    <tbody>{scoreboard}</tbody>
  </table>

  <div class="two">
    <div><h2>Month's Leaders</h2><div class="note">Top equity (growth) funds, last 1 month - with 3Y context.</div>
      <table><thead><tr><th class="l">Fund</th><th class="c">Category</th><th class="r">1M</th><th class="r">3Y</th></tr></thead><tbody>{leaders}</tbody></table></div>
    <div><h2>Month's Laggards</h2><div class="note">Bottom equity (growth) funds, last 1 month.</div>
      <table><thead><tr><th class="l">Fund</th><th class="c">Category</th><th class="r">1M</th><th class="r">3Y</th></tr></thead><tbody>{laggards}</tbody></table></div>
  </div>

  <div class="disc"><b>Disclaimer:</b> For information and education only; not a recommendation to buy or sell any scheme. One month's performance is not indicative of future returns; always read the longer-period columns. Returns are computed from published AMFI NAVs (1M/6M absolute; 1Y and longer annualised). Category is inferred from the scheme name and may occasionally misclassify. Mutual fund investments are subject to market risks; read all scheme related documents carefully. Ace Financial Services - AMFI Registered MFD (ARN-110832).</div>
  <div class="foot">Prepared by <b>Kaustubh Valimbe</b> · Ace Financial Services, Pune · <a href="index.html#contact">Talk to an Expert &rarr;</a></div>
</div></body></html>""".format(meta=meta, month=month_label, asof=as_of, auto=auto,
                                 scoreboard=sb_rows(), leaders=fund_rows(leaders), laggards=fund_rows(laggards))

    ym = dt.datetime.strptime(as_of, "%Y-%m-%d").strftime("%Y-%m")
    fname = "fund-report-{}.html".format(ym)
    out = os.path.join(OUTPUT_DIR, fname) if OUTPUT_DIR and os.path.isdir(OUTPUT_DIR) else fname
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("\nDONE. Wrote:", os.path.abspath(out))
    print("It is publish-ready.")


if __name__ == "__main__":
    build()
