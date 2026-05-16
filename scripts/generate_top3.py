"""
매일 자정 실행: ETF 데이터 기반 AI Top3 추천 생성
public/data/top3.json 갱신 + public/data/history.json에 기록 누적
"""

import sys, json, warnings
from pathlib import Path
from datetime import datetime

import numpy as np

warnings.filterwarnings("ignore")

ROOT    = Path(__file__).parent.parent
OUT_DIR = ROOT / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")
HISTORY_MAX = 60   # 최대 60일 기록 보관


def score_etf(etf: dict) -> float:
    """
    팩터 기반 종합 점수 계산
    모멘텀(3M) 30% + 샤프 25% + 거래량 20% + 변동성 역수 15% + MDD 10%
    """
    score = 0.0

    mom = etf.get("mom_3m", 0) or 0
    score += min(max(mom, -20), 30) / 30 * 30

    sharpe = etf.get("sharpe", 0) or 0
    score += min(max(sharpe, -2), 3) / 3 * 25

    vol = etf.get("vol_avg_억", 0) or 0
    score += min(np.log1p(vol) / np.log1p(500), 1.0) * 20

    volatility = etf.get("vol_20d", 20) or 20
    score += max(0, 1 - volatility / 40) * 15

    mdd = abs(etf.get("mdd", 0) or 0)
    score += max(0, 1 - mdd / 20) * 10

    return round(score, 2)


def build_reason(etf: dict, rank: int) -> str:
    """AI 추천 사유 문장 생성"""
    name   = etf["name"]
    cat    = etf["category"]
    mom3m  = etf.get("mom_3m", 0) or 0
    sharpe = etf.get("sharpe", 0) or 0
    vol    = etf.get("vol_avg_억", 0) or 0
    mdd    = etf.get("mdd", 0) or 0
    rsi    = etf.get("rsi", 50) or 50
    dist   = etf.get("dist_yield", 0) or 0

    parts = []

    if mom3m >= 10:
        parts.append(f"최근 3개월 {mom3m:+.1f}%의 강한 상승 모멘텀")
    elif mom3m >= 3:
        parts.append(f"최근 3개월 {mom3m:+.1f}% 안정적 상승세")
    elif mom3m < 0:
        parts.append(f"단기 조정({mom3m:.1f}%) 후 반등 기대")
    else:
        parts.append(f"최근 3개월 {mom3m:+.1f}% 보합세")

    if sharpe >= 2:
        parts.append(f"샤프비율 {sharpe:.2f}로 위험 대비 수익률 우수")
    elif sharpe >= 1:
        parts.append(f"샤프비율 {sharpe:.2f}로 양호한 리스크 관리")
    elif sharpe >= 0.3:
        parts.append(f"샤프비율 {sharpe:.2f}")

    if vol >= 100:
        parts.append(f"일평균 거래대금 {vol:.0f}억원으로 유동성 풍부")
    elif vol >= 20:
        parts.append(f"일평균 거래대금 {vol:.0f}억원으로 거래 원활")

    if rsi < 35:
        parts.append(f"RSI {rsi:.0f}로 과매도 구간 — 단기 반등 가능성")
    elif rsi > 65:
        parts.append(f"RSI {rsi:.0f}로 상승 추세 유지")

    if dist >= 0.3:
        parts.append(f"분배 수익률 {dist:.2f}%로 인컴 매력")

    if abs(mdd) <= 5:
        parts.append(f"최대 낙폭 {mdd:.1f}%로 하방 리스크 제한적")

    if not parts:
        parts.append(f"{cat} 섹터 내 팩터 종합 점수 상위")

    prefix = ["★ 1순위", "★ 2순위", "★ 3순위"][rank - 1]
    return f"{prefix}: {'. '.join(parts[:3])}."


def build_strategy(top3: list[dict]) -> str:
    """전체 포트폴리오 전략 코멘트"""
    cats = [e["category"] for e in top3]
    avg_mom = sum(e.get("mom_3m", 0) or 0 for e in top3) / len(top3)

    if avg_mom >= 8:
        market_view = "현재 시장은 강한 상승 모멘텀을 유지하고 있습니다."
        strategy    = "위험자산 비중을 늘리되, 분산 유지를 권장합니다."
    elif avg_mom >= 2:
        market_view = "시장이 완만한 회복 흐름을 보이고 있습니다."
        strategy    = "우량 ETF 중심의 점진적 매수 전략이 유효합니다."
    else:
        market_view = "단기 변동성이 확대된 구간입니다."
        strategy    = "현금 비중 유지 및 분할 매수를 권장합니다."

    has_bond = "채권" in cats
    if has_bond:
        strategy += " 채권 ETF가 포함되어 안정성을 보강합니다."

    return f"{market_view} {strategy} Top3는 각 20% 이내로 분산 편입하고, 나머지는 현금 또는 채권 ETF로 보유하세요."


def update_history(top3_out: dict) -> None:
    """history.json에 오늘 추천 기록 추가 (최대 HISTORY_MAX일)"""
    history_path = OUT_DIR / "history.json"

    if history_path.exists():
        try:
            with open(history_path, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = {"records": []}
    else:
        history = {"records": []}

    records = history.get("records", [])

    # 오늘 날짜 기록이 이미 있으면 덮어쓰기
    records = [r for r in records if r.get("date") != TODAY]

    new_record = {
        "date":     TODAY,
        "strategy": top3_out["strategy"],
        "picks": [
            {
                "rank":       p["rank"],
                "ticker":     p["ticker"],
                "name":       p["name"],
                "category":   p["category"],
                "score":      p["score"],
                "mom_3m":     p.get("mom_3m"),
                "sharpe":     p.get("sharpe"),
                "mdd":        p.get("mdd"),
                "rsi":        p.get("rsi"),
                "vol_avg_억": p.get("vol_avg_억"),
                "dist_yield": p.get("dist_yield"),
                "reason":     p["reason"],
            }
            for p in top3_out["picks"]
        ],
    }

    # 최신이 앞에 오도록 삽입
    records.insert(0, new_record)
    records = records[:HISTORY_MAX]

    history_out = {"updated": TODAY, "records": records}
    history_path.write_text(
        json.dumps(history_out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[저장] {history_path}  (총 {len(records)}일 기록)")


def main():
    print(f"[Top3 생성] {TODAY}")

    summary_path = OUT_DIR / "etf_summary.json"
    if not summary_path.exists():
        print("etf_summary.json 없음 — fetch_etf_data.py 먼저 실행")
        sys.exit(1)

    with open(summary_path, encoding="utf-8") as f:
        summary = json.load(f)

    etfs = summary["etfs"]

    candidates = [
        e for e in etfs
        if e.get("category") != "파생"
        and (e.get("vol_avg_억") or 0) >= 5
        and e.get("mom_3m") is not None
    ]

    if not candidates:
        print("후보 ETF 없음")
        sys.exit(1)

    for e in candidates:
        e["_score"] = score_etf(e)
    candidates.sort(key=lambda x: x["_score"], reverse=True)

    top3_etfs = candidates[:3]

    top3_out = {
        "date":     TODAY,
        "strategy": build_strategy(top3_etfs),
        "picks": [
            {
                "rank":       i + 1,
                "ticker":     e["ticker"],
                "name":       e["name"],
                "category":   e["category"],
                "score":      e["_score"],
                "mom_3m":     e.get("mom_3m"),
                "sharpe":     e.get("sharpe"),
                "vol_avg_억": e.get("vol_avg_억"),
                "rsi":        e.get("rsi"),
                "mdd":        e.get("mdd"),
                "dist_yield": e.get("dist_yield"),
                "reason":     build_reason(e, i + 1),
            }
            for i, e in enumerate(top3_etfs)
        ],
    }

    out_path = OUT_DIR / "top3.json"
    out_path.write_text(
        json.dumps(top3_out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[저장] {out_path}")
    for p in top3_out["picks"]:
        print(f"  {p['rank']}위: {p['ticker']} {p['name']} (점수 {p['score']})")
    print(f"\n전략: {top3_out['strategy']}")

    # 히스토리 기록
    update_history(top3_out)


if __name__ == "__main__":
    main()
