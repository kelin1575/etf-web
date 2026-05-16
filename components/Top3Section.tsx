"use client";

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

const RANK_STYLE = [
  "border-yellow-500/60 bg-yellow-900/20",
  "border-gray-400/60 bg-gray-800/30",
  "border-orange-600/60 bg-orange-900/20",
];

const RANK_BADGE = ["🥇", "🥈", "🥉"];

const CAT_COLOR: Record<string, string> = {
  국내주식: "bg-blue-900/50 text-blue-300",
  해외주식: "bg-purple-900/50 text-purple-300",
  채권:     "bg-green-900/50 text-green-300",
  원자재:   "bg-amber-900/50 text-amber-300",
  통화:     "bg-cyan-900/50 text-cyan-300",
  부동산:   "bg-rose-900/50 text-rose-300",
  파생:     "bg-red-900/50 text-red-300",
};

function StatBadge({ label, value, unit = "" }: { label: string; value: number | null; unit?: string }) {
  if (value == null) return null;
  const isPositive = value >= 0;
  return (
    <div className="text-center">
      <div className={`text-sm font-bold ${unit === "%" && label.includes("수익") ? (isPositive ? "text-red-400" : "text-blue-400") : "text-white"}`}>
        {isPositive && unit === "%" ? "+" : ""}{value.toFixed(1)}{unit}
      </div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

export default function Top3Section({ top3 }: { top3: Top3Data }) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-white">🤖 AI 추천 Top 3</h2>
        <span className="text-xs text-gray-500">{top3.date} 기준</span>
      </div>

      {/* 전략 코멘트 */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg px-4 py-3 mb-4 text-sm text-gray-300 leading-relaxed">
        {top3.strategy}
      </div>

      {/* 카드 3개 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {top3.picks.map((pick, i) => (
          <a
            key={pick.ticker}
            href={`/etf/${pick.ticker}`}
            className={`block rounded-xl border p-4 hover:brightness-110 transition-all ${RANK_STYLE[i]}`}
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <span className="text-lg">{RANK_BADGE[i]}</span>
                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${CAT_COLOR[pick.category] ?? "bg-gray-700 text-gray-300"}`}>
                  {pick.category}
                </span>
              </div>
              <span className="text-xs text-gray-400">점수 {pick.score}</span>
            </div>

            <div className="font-bold text-white text-sm leading-tight mb-1">{pick.name}</div>
            <div className="text-xs text-gray-400 mb-3">{pick.ticker}</div>

            {/* 지표 */}
            <div className="grid grid-cols-3 gap-2 mb-3 py-2 border-t border-gray-700/50">
              <StatBadge label="3M수익" value={pick.mom_3m} unit="%" />
              <StatBadge label="샤프"   value={pick.sharpe} />
              <StatBadge label="RSI"    value={pick.rsi} />
            </div>

            {/* 추천 사유 */}
            <p className="text-xs text-gray-300 leading-relaxed">{pick.reason}</p>
          </a>
        ))}
      </div>
    </section>
  );
}
