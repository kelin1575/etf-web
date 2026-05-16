"use client";

import Link from "next/link";

interface Pick {
  rank: number;
  ticker: string;
  name: string;
  category: string;
  score: number;
  mom_3m: number | null;
  sharpe: number | null;
  vol_avg_억: number | null;
  rsi: number | null;
  mdd: number | null;
  dist_yield: number | null;
  reason: string;
}

interface Top3Data {
  date: string;
  strategy: string;
  picks: Pick[];
}

const RANK_BORDER = [
  "border-yellow-500/70",
  "border-slate-400/50",
  "border-orange-500/50",
];
const RANK_BG = [
  "bg-yellow-950/40",
  "bg-slate-800/40",
  "bg-orange-950/30",
];
const RANK_BADGE = ["🥇", "🥈", "🥉"];

const CAT_COLOR: Record<string, string> = {
  국내주식: "bg-blue-900/60 text-blue-200",
  해외주식: "bg-purple-900/60 text-purple-200",
  채권:     "bg-green-900/60 text-green-200",
  원자재:   "bg-amber-900/60 text-amber-200",
  통화:     "bg-cyan-900/60 text-cyan-200",
  부동산:   "bg-rose-900/60 text-rose-200",
  파생:     "bg-red-900/60 text-red-200",
};

function PctVal({ v }: { v: number | null }) {
  if (v == null) return <span className="cell-dash">—</span>;
  const cls = v > 0 ? "text-red-400" : v < 0 ? "text-blue-400" : "text-gray-300";
  return <span className={`font-bold ${cls}`}>{v > 0 ? "+" : ""}{v.toFixed(1)}%</span>;
}

export default function Top3Section({ top3 }: { top3: Top3Data }) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-white">🤖 AI 추천 Top 3</h2>
        <span className="text-xs text-slate-400">{top3.date} 기준</span>
      </div>

      {/* 전략 코멘트 */}
      <div className="bg-slate-800/70 border border-slate-600/50 rounded-xl px-4 py-3 mb-5">
        <p className="strategy-text text-sm">{top3.strategy}</p>
      </div>

      {/* 카드 3개 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {top3.picks.map((pick, i) => (
          <Link
            key={pick.ticker}
            href={`/etf/${pick.ticker}`}
            className={`block rounded-xl border-2 ${RANK_BORDER[i]} ${RANK_BG[i]} p-4 hover:brightness-110 transition-all`}
          >
            {/* 헤더 */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">{RANK_BADGE[i]}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CAT_COLOR[pick.category] ?? "bg-gray-700 text-gray-200"}`}>
                  {pick.category}
                </span>
              </div>
              <span className="pick-score text-sm">점수 {pick.score.toFixed(1)}</span>
            </div>

            {/* 종목명 */}
            <div className="mb-3">
              <div className="text-white font-bold text-base leading-tight">{pick.name}</div>
              <div className="pick-ticker-sub mt-0.5">{pick.ticker}</div>
            </div>

            {/* 핵심 지표 3개 */}
            <div className="grid grid-cols-3 gap-1 mb-3 py-2.5 border-t border-b border-white/10">
              <div className="text-center">
                <div className="text-sm font-bold"><PctVal v={pick.mom_3m} /></div>
                <div className="stat-label mt-0.5">3M수익</div>
              </div>
              <div className="text-center">
                <div className={`text-sm font-bold ${(pick.sharpe ?? 0) >= 1 ? "text-emerald-400" : (pick.sharpe ?? 0) < 0 ? "text-red-400" : "text-gray-200"}`}>
                  {pick.sharpe?.toFixed(2) ?? "—"}
                </div>
                <div className="stat-label mt-0.5">샤프</div>
              </div>
              <div className="text-center">
                <div className={`text-sm font-bold ${(pick.rsi ?? 50) > 70 ? "text-red-400" : (pick.rsi ?? 50) < 30 ? "text-blue-400" : "text-gray-200"}`}>
                  {pick.rsi?.toFixed(0) ?? "—"}
                </div>
                <div className="stat-label mt-0.5">RSI</div>
              </div>
            </div>

            {/* 부가 지표 */}
            <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs mb-3">
              <div className="flex justify-between">
                <span className="stat-label">MDD</span>
                <span className="text-blue-300 font-medium">{pick.mdd?.toFixed(1) ?? "—"}%</span>
              </div>
              <div className="flex justify-between">
                <span className="stat-label">거래대금</span>
                <span className="text-slate-200">{pick.vol_avg_억 != null ? `${pick.vol_avg_억.toFixed(0)}억` : "—"}</span>
              </div>
            </div>

            {/* 추천 사유 */}
            <p className="pick-reason text-xs border-t border-white/10 pt-2">{pick.reason}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
