"""
매일 자정 GitHub Actions에서 실행
pykrx로 국내 ETF 상위 100개 데이터 수집 → public/data/ JSON 저장
"""

import sys, json, warnings
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

OUT_DIR = Path(__file__).parent.parent / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# pykrx용 날짜 (YYYYMMDD), 표시용 날짜 (YYYY-MM-DD)
_now      = datetime.now()
TODAY     = _now.strftime("%Y%m%d")
TODAY_DISP = _now.strftime("%Y-%m-%d")
START_3M  = (_now - timedelta(days=95)).strftime("%Y%m%d")

# ── ETF 전체 OHLCV 캐시 (get_etf_ohlcv_by_ticker는 1번만 호출) ──
_etf_snapshot: pd.DataFrame | None = None

def _get_etf_snapshot() -> pd.DataFrame:
    global _etf_snapshot
    if _etf_snapshot is None:
        from pykrx import stock
        try:
            df = stock.get_etf_ohlcv_by_ticker(TODAY)
            _etf_snapshot = df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"  ETF 스냅샷 실패: {e}")
            _etf_snapshot = pd.DataFrame()
    return _etf_snapshot


# ── pykrx 헬퍼 ────────────────────────────────────────────────
def get_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    from pykrx import stock
    try:
        df = stock.get_market_ohlcv_by_date(start, end, ticker)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={"시가":"open","고가":"high","저가":"low",
                                 "종가":"close","거래량":"volume"})
        return df[["open","high","low","close","volume"]]
    except Exception as e:
        print(f"  OHLCV 실패 {ticker}: {e}")
        return pd.DataFrame()


def get_etf_info(ticker: str) -> dict:
    """ETF 기본 정보 (NAV, 순자산, 분배수익률) — 캐시된 스냅샷에서 조회"""
    snap = _get_etf_snapshot()
    if snap.empty or ticker not in snap.index:
        return {"nav": 0, "aum_억": 0, "dist_yield": 0}
    row = snap.loc[ticker]
    # 컬럼 이름은 pykrx 버전마다 다를 수 있음 — 유연하게 처리
    def _get(keys, default=0):
        for k in keys:
            if k in row.index:
                try:
                    return float(row[k])
                except Exception:
                    pass
        return float(default)

    nav   = _get(["기준가격", "종가", "NAV"], 0)
    aum   = _get(["순자산총액", "시가총액", "AUM"], 0)
    dist  = _get(["분배금", "분배금액"], 0)

    dist_yield = round(dist / max(nav, 1) * 100, 3) if dist > 0 else 0.0

    return {
        "nav":        nav,
        "aum_억":     round(aum / 1e8, 1),
        "dist_yield": dist_yield,
    }


def get_top100_tickers() -> list[str]:
    """거래대금 기준 상위 100개 ETF 티커"""
    from pykrx import stock
    snap = _get_etf_snapshot()
    if not snap.empty:
        for col in ["거래대금", "거래금액"]:
            if col in snap.columns:
                return list(snap.sort_values(col, ascending=False).head(100).index)
        if "거래량" in snap.columns and "기준가격" in snap.columns:
            snap = snap.copy()
            snap["_turnover"] = snap["거래량"] * snap["기준가격"]
            return list(snap.sort_values("_turnover", ascending=False).head(100).index)
        return list(snap.head(100).index)
    # fallback
    try:
        all_tickers = stock.get_market_ticker_list(TODAY, market="ETF")
        return list(all_tickers[:100])
    except Exception:
        return []


def calc_indicators(df: pd.DataFrame) -> dict:
    """3개월 기술적 지표 계산"""
    if df.empty or len(df) < 5:
        return {}

    close = df["close"]
    ret   = close.pct_change(fill_method=None)

    mom_1m  = round(float(close.iloc[-1] / close.iloc[-22] - 1) * 100, 2) if len(close) >= 22 else None
    mom_3m  = round(float(close.iloc[-1] / close.iloc[0]  - 1) * 100, 2)

    vol_20d = round(float(ret.tail(20).std() * (252**0.5) * 100), 2) if len(ret) >= 20 else None

    excess  = ret - 0.035 / 252
    sharpe  = round(float(excess.mean() / ret.std() * (252**0.5)), 2) if ret.std() > 0 else 0

    roll_max = close.cummax()
    mdd      = round(float(((close - roll_max) / roll_max).min() * 100), 2)

    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = round(float(100 - 100 / (1 + rs.iloc[-1])), 1) if not rs.empty else 50.0

    vol_avg = round(float((df["close"] * df["volume"]).tail(20).mean() / 1e8), 1)

    return {
        "mom_1m":     mom_1m,
        "mom_3m":     mom_3m,
        "vol_20d":    vol_20d,
        "sharpe":     sharpe,
        "mdd":        mdd,
        "rsi":        rsi,
        "vol_avg_억": vol_avg,
    }


def price_series(df: pd.DataFrame) -> list[dict]:
    """차트용 OHLCV 배열 (최근 65영업일 ≈ 3개월)"""
    if df.empty:
        return []
    tail = df.tail(65)
    return [
        {
            "date":   d.strftime("%Y-%m-%d"),
            "open":   int(row.open),
            "high":   int(row.high),
            "low":    int(row.low),
            "close":  int(row.close),
            "volume": int(row.volume),
        }
        for d, row in tail.iterrows()
    ]


# ── 카테고리 분류 ───────────────────────────────────────────────
_CAT_KEYWORDS = {
    "파생":     ["레버리지", "인버스", "2X", "곱버스"],
    "채권":     ["국채", "회사채", "채권", "Bond", "금리", "단기채", "장기채", "하이일드", "CD금리"],
    "원자재":   ["금", "원유", "WTI", "구리", "농산물", "원자재", "commodity", "Commodity"],
    "부동산":   ["리츠", "부동산", "REITs", "인프라"],
    "통화":     ["달러", "USD", "환헤지", "환노출"],
    "해외주식": ["미국", "S&P", "나스닥", "NASDAQ", "선진국", "신흥국", "중국", "일본", "베트남",
                 "인도", "유럽", "글로벌", "World", "반도체MV", "해외"],
    "국내주식": ["200", "코스피", "코스닥", "KOSPI", "KOSDAQ", "반도체", "은행", "배당", "가치",
                 "성장", "헬스", "바이오", "게임", "엔터", "화장품", "방산", "건설", "철강", "자동차"],
}

def classify(name: str) -> str:
    name_u = name.upper()
    for cat, kws in _CAT_KEYWORDS.items():
        for kw in kws:
            if kw.upper() in name_u:
                return cat
    return "국내주식"


# ── 메인 ──────────────────────────────────────────────────────
def main():
    print(f"[ETF 데이터 수집] {TODAY_DISP}")

    tickers = get_top100_tickers()
    print(f"  티커 {len(tickers)}개 확보")

    if not tickers:
        print("티커 목록 없음 — 종료")
        sys.exit(1)

    etf_list   = []
    price_data = {}

    for i, ticker in enumerate(tickers, 1):
        print(f"  [{i:3d}/{len(tickers)}] {ticker}", end=" ", flush=True)

        df = get_ohlcv(ticker, START_3M, TODAY)
        if df.empty:
            print("스킵")
            continue

        ind = calc_indicators(df)
        if not ind:
            print("지표없음")
            continue

        info = get_etf_info(ticker)

        try:
            from pykrx import stock
            name = stock.get_market_ticker_name(ticker)
        except Exception:
            name = ticker

        price_last = int(df["close"].iloc[-1])
        # NAV가 0이면 price_last로 대체
        if info["nav"] == 0:
            info["nav"] = price_last

        etf_list.append({
            "ticker":      ticker,
            "name":        name,
            "category":    classify(name),
            "aum_억":      info["aum_억"],
            "dist_yield":  info["dist_yield"],
            "nav":         info["nav"],
            "price_last":  price_last,
            **ind,
            "updated":     TODAY_DISP,
        })

        price_data[ticker] = price_series(df)
        print(f"✓  {name[:18]}")

    print(f"\n  수집 완료: {len(etf_list)}개")

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
