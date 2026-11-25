#!/usr/bin/env python3
"""국내 상장 ETF 중 전일 거래량 기준 이상 종목을 수집해 data/etf_latest.json 으로 저장.
Source: Naver Finance (finance.naver.com, fchart.stock.naver.com, m.stock.naver.com)
Usage: python3 fetch_etf.py [--min-volume 500000]
"""
import json, sys, os, time, argparse, datetime as dt, urllib.request
from concurrent.futures import ThreadPoolExecutor

KST = dt.timezone(dt.timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (etf-report)"}
HERE = os.path.dirname(os.path.abspath(__file__))
TAB = {1: "국내 시장지수", 2: "국내 업종/테마", 3: "국내 파생", 4: "해외 주식",
       5: "원자재", 6: "채권", 7: "기타"}

def get(url, enc="utf-8", tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return r.read().decode(enc, "replace")
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))

def prev_day_bar(code, now):
    """fchart 일봉에서 '완결된 직전 거래일' 봉을 반환 (date, close, volume)."""
    txt = get(f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count=4&requestType=0", "euc-kr")
    rows = [l.split('data="')[1].split('"')[0].split("|") for l in txt.splitlines() if 'data="' in l]
    if not rows:
        return None
    today = now.strftime("%Y%m%d")
    # 장중/장마감 직후(16시 이전)엔 오늘 봉이 미완결 → 직전 봉 사용
    if rows[-1][0] == today and now.hour < 16:
        rows = rows[:-1]
    if not rows:
        return None
    d, o, h, l, c, v = rows[-1]
    return {"date": d, "close": float(c), "volume": int(float(v))}

def detail(code):
    d = json.loads(get(f"https://m.stock.naver.com/api/stock/{code}/etfAnalysis"))
    perf = {p["periodTypeCode"]: p["value"] for p in (d.get("returnPerformanceList") or [])}
    div = d.get("dividend") or {}
    top = [f'{a["itemName"]} {a["etfWeight"]}' for a in (d.get("etfTop10MajorConstituentAssets") or [])[:5]]
    return {
        "issuer": (d.get("issuerName") or "").replace("(ETF)", ""),
        "baseIndex": d.get("etfBaseIndex"),
        "listedDate": d.get("listedDate"),
        "fee": d.get("totalFee"),
        "trackingError": d.get("chaseErrorRate"),
        "taxType": d.get("taxationTypeCode"),
        "aum": float(d.get("marketValueRaw") or 0) / 1e8,  # 억원
        "r1w": perf.get("W1"), "r1m": perf.get("M1"), "r3m": perf.get("M3"), "r6m": perf.get("M6"),
        "rytd": perf.get("YTD"), "r1y": perf.get("Y1"), "r3y": perf.get("Y3"), "r5y": perf.get("Y5"),
        "perfDate": d.get("returnPerformanceReferenceDate"),
        "divYield": div.get("dividendYieldTtm"), "divPerShare": div.get("dividendPerShareTtm"),
        "divCount": div.get("dividendCountThisYear"), "divMonths": div.get("dividendMonthThisYear"),
        "top5": top,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-volume", type=int, default=500_000)
    a = ap.parse_args()
    now = dt.datetime.now(KST)
    lst = json.loads(get("https://finance.naver.com/api/sise/etfItemList.nhn?etfType=0", "euc-kr"))["result"]["etfItemList"]
    print(f"전체 ETF {len(lst)}개", file=sys.stderr)
    with ThreadPoolExecutor(8) as ex:
        bars = list(ex.map(lambda e: (e, safe(prev_day_bar, e["itemcode"], now)), lst))
    picked = [(e, b) for e, b in bars if b and b["volume"] >= a.min_volume]
    # 기준일: 가장 많이 나온 봉 날짜 (거래정지 종목 제외)
    dates = [b["date"] for _, b in bars if b]
    base = max(set(dates), key=dates.count)
    picked = [(e, b) for e, b in picked if b["date"] == base]
    print(f"기준일 {base}, 거래량 {a.min_volume:,}주 이상 {len(picked)}개", file=sys.stderr)
    with ThreadPoolExecutor(6) as ex:
        dets = list(ex.map(lambda p: safe(detail, p[0]["itemcode"]), picked))
    out = []
    for (e, b), d in zip(picked, dets):
        name = e["itemname"]
        lev = any(k in name for k in ["레버리지", "2X", "인버스", "선물인버스"])
        out.append({"code": e["itemcode"], "name": name, "category": TAB.get(e["etfTabCode"], "기타"),
                    "leveraged": lev, "close": b["close"], "volume": b["volume"],
                    "tradeValue": round(b["close"] * b["volume"] / 1e8, 1), **(d or {})})
    out.sort(key=lambda x: -x["volume"])
    res = {"baseDate": base, "generatedAt": now.isoformat(timespec="minutes"), "minVolume": a.min_volume,
           "totalEtfs": len(lst), "count": len(out), "items": out}
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    for fn in ("etf_latest.json", f"etf_{base}.json"):
        with open(os.path.join(HERE, "data", fn), "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    print(os.path.join(HERE, "data", "etf_latest.json"))

def safe(fn, *args):
    try:
        return fn(*args)
    except Exception as ex:
        print(f"WARN {fn.__name__}{args[:1]}: {ex}", file=sys.stderr)
        return None

if __name__ == "__main__":
    main()
