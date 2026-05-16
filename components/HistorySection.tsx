"use client";

import { useState } from "react";
import Link from "next/link";

interface Pick {
  rank: number;
  ticker: string;
  name: string;
  category: string;
  score: number;
  mom_3m: number | null;
  sharpe: number | null;
  mdd: number | null;
  rsi: number | null;
  vol_avg_억: number | null;
  dist_yield: number | null;
  reason: string;
}

interface HistoryRecord {
  date: string;
  strategy: string;
  picks: Pick[];
}

interface HistoryData {
  updated: string;
  records: HistoryRecord[];
}

const CAT_COLOR: Record<string, string> = {
  국내주식: "bg-blue-900/50 text-blue-300",
  해외주식: "bg-purple-900/50 text-purple-300",
  채권:     "bg-green-900/50 text-green-300",
  원자재:   "bg-amber-900/50 text-amber-300",
  통화:     "bg-cyan-900/50 text-cyan-300",
  부동산:   "bg-rose-900/50 text-rose-300",
  파생:     "bg-red-900/50 text-red-300",
};

const RANK_EMOJI = ["🥇", "🥈", "🥉"];

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ko-KR", { month: "long", day: "numeric", weekday: "short" });
}

export default function HistorySection({ history }: { history: HistoryData }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const records = history.records ?? [];
  const displayed = showAll ? records : records.slice(0, 10);

  if (records.length === 0) {
    return null;
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">일별 추천 기록</h2>
          <p className="text-xs text-gray-500 mt-0.5">매 영업일 자정 자동 갱신 · 최근 {records.length}일</p>
        </div>
        <span className="text-xs text-gray-600">{history.updated} 기준</span>
      </div>

      <div className="space-y-2">
        {displayed.map((record) => {
          const isOpen = expanded === record.date;
          return (
            <div
              key={record.date}
              className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden"
            >
              {/* 날짜 헤더 — 클릭으로 접기/펼치기 */}
              <button
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
                onClick={() => setExpanded(isOpen ? null : record.date)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-white">{formatDate(record.date)}</span>
                  <span className="text-xs text-gray-500">{record.date}</span>
                  {/* 미니 픽 뱃지 */}
                  <div className="flex gap-1">
                    {record.picks.slice(0, 3).map((p) => (
                      <span
                        key={p.ticker}
                        className={`text-xs px-1.5 py-0.5 rounded ${CAT_COLOR[p.category] ?? "bg-gray-700 text-gray-300"}`}
                      >
                        {p.name.length > 10 ? p.name.slice(0, 10) + "…" : p.name}
                      </span>
                    ))}
                  </div>
                </div>
                <span className="text-gray-500 text-xs">{isOpen ? "▲" : "▼"}</span>
              </button>

              {/* 상세 패널 */}
              {isOpen && (
                <div className="px-4 pb-4 border-t border-gray-800">
                  {/* 전략 코멘트 */}
                  <p className="text-xs text-gray-400 mt-3 mb-4 leading-relaxed bg-gray-800/40 rounded-lg px-3 py-2">
                    {record.strategy}
                  </p>

                  {/* Top3 카드 */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {record.picks.map((pick) => (
                      <div
                        key={pick.ticker}
                        className="bg-gray-800/60 rounded-lg p-3 border border-gray-700/50"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <span className="text-base">{RANK_EMOJI[pick.rank - 1]}</span>
                            <Link
                              href={`/etf/${pick.ticker}`}
                              className="block text-sm font-semibold text-white hover:text-blue-400 transition-colors mt-0.5"
                            >
                              {pick.name}
                            </Link>
                            <span className="text-xs text-gray-500">{pick.ticker}</span>
                          </div>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${CAT_COLOR[pick.category] ?? "bg-gray-700 text-gray-300"}`}>
                            {pick.category}
                          </span>
                        </div>

                        {/* 지표 */}
                        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs mb-2">
                          <div className="flex justify-between">
                            <span className="text-gray-500">3M수익</span>
                            <span className={pick.mom_3m != null && pick.mom_3m >= 0 ? "text-red-400" : "text-blue-400"}>
                              {pick.mom_3m != null ? `${pick.mom_3m > 0 ? "+" : ""}${pick.mom_3m.toFixed(1)}%` : "—"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">샤프</span>
                            <span className="text-gray-300">{pick.sharpe?.toFixed(2) ?? "—"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">RSI</span>
                            <span className={
                              pick.rsi != null && pick.rsi > 70 ? "text-red-400" :
                              pick.rsi != null && pick.rsi < 30 ? "text-blue-400" : "text-gray-300"
                            }>{pick.rsi?.toFixed(0) ?? "—"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">MDD</span>
                            <span className="text-blue-400">{pick.mdd?.toFixed(1) ?? "—"}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">거래대금</span>
                            <span className="text-gray-300">{pick.vol_avg_억?.toFixed(0) ?? "—"}억</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">점수</span>
                            <span className="text-amber-400 font-medium">{pick.score.toFixed(1)}</span>
                          </div>
                        </div>

                        {/* 추천 사유 */}
                        <p className="text-xs text-gray-400 leading-relaxed border-t border-gray-700/50 pt-2">
                          {pick.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {records.length > 10 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-3 w-full py-2 text-xs text-gray-500 hover:text-gray-300 transition-colors border border-gray-800 rounded-lg hover:border-gray-700"
        >
          {showAll ? "접기 ▲" : `이전 기록 더 보기 (${records.length - 10}일) ▼`}
        </button>
      )}
    </section>
  );
}
