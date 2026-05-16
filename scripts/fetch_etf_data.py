"""
매일 자정 GitHub Actions에서 실행
FinanceDataReader로 국내 ETF 데이터 수집 → public/data/ JSON 저장
(pykrx는 KRX 인증 필요로 변경 — fdr은 인증 불필요)
"""

import sys, json, warnings
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import FinanceDataReader as fdr

# yfinance — 분배율/AUM 보조 데이터 (실패해도 계속 진행)
try:
    import yfinance as yf
    _HAS_YF = True
except ImportError:
    _HAS_YF = False

warnings.filterwarnings("ignore")

OUT_DIR = Path(__file__).parent.parent / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

_now = datetime.now()

def _last_weekday(d: datetime) -> datetime:
    """가장 최근 평일 반환"""
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d

# 어제까지의 마지막 평일 기준 (당일은 장이 아직 열려있을 수 있음)
_base        = _last_weekday(_now - timedelta(days=1))
TODAY        = _base.strftime("%Y%m%d")
TODAY_DISP   = _base.strftime("%Y-%m-%d")
START_3M     = (_base - timedelta(days=95)).strftime("%Y%m%d")

print(f"[ETF 데이터 수집] 기준일: {TODAY_DISP}")


# ── ETF 목록 (KRX-ETF 리스팅) ────────────────────────────────
def get_etf_listing() -> pd.DataFrame:
    """fdr에서 KRX 상장 ETF 목록 조회"""
    try:
        df = fdr.StockListing("KRX-ETF")
        if not df.empty:
            return df
    except Exception as e:
        print(f"  KRX-ETF 리스팅 실패: {e}")
    # 주요 ETF 하드코딩 fallback
    fallback = [
        ("069500","KODEX 200","국내주식"),
        ("360750","TIGER 미국S&P500","해외주식"),
        ("371460","TIGER 미국나스닥100","해외주식"),
        ("379800","KODEX 미국S&P500TR","해외주식"),
        ("381180","KODEX 미국나스닥100TR","해외주식"),
        ("102110","TIGER 200","국내주식"),
        ("114260","KODEX 국채3년","채권"),
        ("148070","KOSEF 국고채10년","채권"),
        ("214980","KODEX 단기채권PLUS","채권"),
        ("273130","KODEX 종합채권(AA-)액티브","채권"),
        ("385720","TIGER 미국채10년선물","채권"),
        ("453850","ACE 미국30년국채액티브","채권"),
        ("091160","KODEX 반도체","국내주식"),
        ("091180","KODEX 은행","국내주식"),
        ("229200","KODEX 코스닥150","국내주식"),
        ("261220","KODEX WTI원유선물(H)","원자재"),
        ("284430","KODEX 구리선물(H)","원자재"),
        ("261240","KODEX 미국반도체MV","해외주식"),
        ("360200","ACE 미국S&P500","해외주식"),
        ("133690","TIGER 미국S&P500레버리지","파생"),
        ("252670","KODEX 200선물인버스2X","파생"),
        ("122630","KODEX 레버리지","파생"),
        ("233740","KODEX 코스닥150레버리지","파생"),
        ("308620","KODEX 금선물(H)","원자재"),
        ("132030","KODEX 골드선물(H)","원자재"),
        ("448290","ACE 미국나스닥100","해외주식"),
        ("447820","ACE 미국S&P500타겟커버드콜","해외주식"),
        ("411060","ACE 미국빅테크TOP7 Plus","해외주식"),
        ("459580","KODEX 미국AI테크TOP10SOLACTIVE","해외주식"),
        ("462990","TIGER 미국AI반도체핵심공정","해외주식"),
        ("468380","TIGER AI코리아그로스액티브","국내주식"),
        ("472160","KODEX 미국30년국채+12%프리미엄","채권"),
        ("486450","ACE 엔비디아채권혼합블룸버그","해외주식"),
        ("489520","TIGER 미국나스닥100타겟커버드콜","해외주식"),
        ("494930","KODEX 미국달러SOFR금리액티브(합성)","통화"),
        ("438330","KODEX 인도Nifty50","해외주식"),
        ("441680","TIGER 인도니프티50","해외주식"),
        ("381170","TIGER 미국나스닥100TR","해외주식"),
        ("364980","TIGER 글로벌리튬&2차전지SOLACTIVE","해외주식"),
        ("395160","TIGER 차이나항셍테크","해외주식"),
        ("143460","TIGER 리츠부동산인프라","부동산"),
        ("329200","TIGER 미국MSCI리츠","부동산"),
        ("394660","KODEX 미국메타버스나스닥액티브","해외주식"),
        ("400870","KODEX K-방산","국내주식"),
        ("457690","TIGER 2차전지TOP10","국내주식"),
        ("455870","KODEX AI반도체핵심장비","국내주식"),
        ("465580","TIGER 글로벌AI액티브","해외주식"),
        ("486290","TIGER 미국배당다우존스","해외주식"),
        ("446720","KINDEX 미국S&P500","해외주식"),
        ("449450","SOL 미국S&P500","해외주식"),
    ]
    return pd.DataFrame(fallback, columns=["Symbol","Name","Sector"])


# ── OHLCV 수집 (FinanceDataReader) ───────────────────────────
def get_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    try:
        df = fdr.DataReader(ticker, start, end)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        # fdr 컬럼: Open, High, Low, Close, Volume
        df.columns = [c.lower() for c in df.columns]
        needed = [c for c in ["open","high","low","close","volume"] if c in df.columns]
        return df[needed].dropna(subset=["close"])
    except Exception as e:
        print(f"    OHLCV 실패 {ticker}: {e}")
        return pd.DataFrame()


# ── 기술적 지표 계산 ─────────────────────────────────────────
def calc_indicators(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 5:
        return {}

    close = df["close"].astype(float)
    ret   = close.pct_change(fill_method=None).dropna()

    mom_1m  = round(float(close.iloc[-1] / close.iloc[-22] - 1) * 100, 2) if len(close) >= 22 else None
    mom_3m  = round(float(close.iloc[-1] / close.iloc[0]  - 1) * 100, 2)
    vol_20d = round(float(ret.tail(20).std() * (252**0.5) * 100), 2) if len(ret) >= 20 else None

    excess  = ret - 0.035 / 252
    sharpe  = round(float(excess.mean() / ret.std() * (252**0.5)), 2) if ret.std() > 0 else 0.0

    roll_max = close.cummax()
    mdd      = round(float(((close - roll_max) / roll_max).min() * 100), 2)

    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = round(float(100 - 100 / (1 + rs.iloc[-1])), 1) if not rs.empty and not np.isnan(rs.iloc[-1]) else 50.0

    vol_col  = "volume" if "volume" in df.columns else None
    vol_avg  = round(float((close * df[vol_col]).tail(20).mean() / 1e8), 1) if vol_col else 0.0

    return {
        "mom_1m":     mom_1m,
        "mom_3m":     mom_3m,
        "vol_20d":    vol_20d,
        "sharpe":     sharpe,
        "mdd":        mdd,
        "rsi":        rsi,
        "vol_avg_억": vol_avg,
    }


def get_yf_meta(tickers: list[str]) -> dict[str, dict]:
    """yfinance로 분배수익률·AUM 일괄 조회 (ticker → {dist_yield, aum_억})"""
    if not _HAS_YF or not tickers:
        return {}
    yt = [f"{t}.KS" for t in tickers]
    result = {}
    try:
        data = yf.download(yt, period="1d", auto_adjust=True, progress=False)
        for t in tickers:
            ys = f"{t}.KS"
            try:
                info = yf.Ticker(ys).info
                dy   = float(info.get("dividendYield") or 0) * 100   # 소수점 → %
                aum  = float(info.get("totalAssets") or 0) / 1e8
                result[t] = {"dist_yield": round(dy, 3), "aum_억": round(aum, 1)}
            except Exception:
                result[t] = {"dist_yield": 0.0, "aum_억": 0.0}
    except Exception as e:
        print(f"  yfinance 일괄조회 실패: {e}")
    return result


def price_series(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    tail = df.tail(65)
    rows = []
    for d, row in tail.iterrows():
        rows.append({
            "date":   d.strftime("%Y-%m-%d"),
            "open":   int(row.get("open", row["close"])),
            "high":   int(row.get("high", row["close"])),
            "low":    int(row.get("low",  row["close"])),
            "close":  int(row["close"]),
            "volume": int(row.get("volume", 0)),
        })
    return rows


# ── 카테고리 분류 ──────────────────────────────────────────────
_CAT_KEYWORDS = {
    "파생":     ["레버리지", "인버스", "2X", "곱버스"],
    "채권":     ["국채", "회사채", "채권", "Bond", "금리", "단기채", "장기채", "하이일드", "CD금리", "SOFR"],
    "원자재":   ["금", "원유", "WTI", "구리", "농산물", "원자재", "골드", "Gold"],
    "부동산":   ["리츠", "부동산", "REITs", "인프라"],
    "통화":     ["달러", "USD", "환헤지", "환노출", "통화"],
    "해외주식": ["미국", "S&P", "나스닥", "NASDAQ", "선진국", "신흥국", "중국", "일본", "베트남",
                 "인도", "유럽", "글로벌", "World", "해외", "MV", "항셍"],
    "국내주식": ["200", "코스피", "코스닥", "KOSPI", "KOSDAQ", "반도체", "은행", "배당", "가치",
                 "성장", "헬스", "바이오", "게임", "엔터", "화장품", "방산", "건설", "철강", "자동차",
                 "2차전지", "AI", "K-"],
}

def classify(name: str) -> str:
    if not isinstance(name, str):
        return "국내주식"
    name_u = name.upper()
    for cat, kws in _CAT_KEYWORDS.items():
        for kw in kws:
            if kw.upper() in name_u:
                return cat
    return "국내주식"


# ── 메인 ─────────────────────────────────────────────────────
def main():
    listing = get_etf_listing()
    print(f"  ETF 목록: {len(listing)}개")

    # 컬럼 정규화
    col_map = {}
    for c in listing.columns:
        cl = c.lower()
        if cl in ("symbol","code","ticker"):
            col_map[c] = "ticker"
        elif cl in ("name","종목명","isuabbrv"):
            col_map[c] = "name"
    listing = listing.rename(columns=col_map)
    if "ticker" not in listing.columns:
        listing["ticker"] = listing.index.astype(str)
    if "name" not in listing.columns:
        listing["name"] = listing["ticker"]

    tickers = listing["ticker"].astype(str).str.zfill(6).tolist()[:100]
    name_map = dict(zip(listing["ticker"].astype(str).str.zfill(6),
                        listing["name"].astype(str)))

    # yfinance로 분배율·AUM 일괄 사전 조회
    print("  yfinance 메타데이터 조회 중...")
    yf_meta = get_yf_meta(tickers)

    etf_list   = []
    price_data = {}
    success = 0

    for i, ticker in enumerate(tickers, 1):
        name = name_map.get(ticker, ticker)
        print(f"  [{i:3d}/{len(tickers)}] {ticker} {name[:14]}", end=" ", flush=True)

        df = get_ohlcv(ticker, START_3M, TODAY)
        if df.empty or len(df) < 10:
            print("스킵")
            continue

        ind = calc_indicators(df)
        if not ind:
            print("지표없음")
            continue

        price_last = int(df["close"].iloc[-1])
        meta       = yf_meta.get(ticker, {"dist_yield": 0.0, "aum_억": 0.0})

        etf_list.append({
            "ticker":      ticker,
            "name":        name,
            "category":    classify(name),
            "aum_억":      meta["aum_억"],
            "dist_yield":  meta["dist_yield"],
            "nav":         price_last,
            "price_last":  price_last,
            **ind,
            "updated":     TODAY_DISP,
        })
        price_data[ticker] = price_series(df)
        success += 1
        print("✓")

    if not etf_list:
        print("수집된 ETF 없음 — 종료")
        sys.exit(1)

    print(f"\n  수집 완료: {success}/{len(tickers)}개")

    # 거래대금 기준 정렬 (vol_avg_억 내림차순)
    etf_list.sort(key=lambda e: e.get("vol_avg_억") or 0, reverse=True)

    summary_path = OUT_DIR / "etf_summary.json"
    summary_path.write_text(
        json.dumps({"updated": TODAY_DISP, "count": len(etf_list), "etfs": etf_list},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[저장] {summary_path}")

    prices_path = OUT_DIR / "prices.json"
    prices_path.write_text(
        json.dumps({"updated": TODAY_DISP, "data": price_data},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[저장] {prices_path}")


if __name__ == "__main__":
    main()
