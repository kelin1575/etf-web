"use client";

import { useState, useMemo } from "react";
import Link from "next/link";

interface ETF {
  ticker: string;
  name: string;
  category: string;
  aum_억: number;
  dist_yield: number;
  price_last: number;
  mom_1m: number | null;
  mom_3m: number | null;
  vol_20d: number | null;
  sharpe: number | null;
  mdd: number | null;
  rsi: number | null;
  vol_avg_억: number | null;
}

const CATEGORIES = ["전체", "국내주식", "해외주식", "채권", "원자재", "통화", "부동산", "파생"];

const CAT_COLOR: Record<string, string> = {
  국내주식: "text-blue-400",
  해외주식: "text-purple-400",
  채권:     "text-green-400",
  원자재:   "text-amber-400",
  통화:     "text-cyan-400",
  부동산:   "text-rose-400",
  파생:     "text-red-400",
};

type SortKey = keyof ETF;

/* ── 셀 컴포넌트 ─────────────────────────────── */
function PctCell({ v }: { v: number | null }) {
  if (v == null) return <td className="px-3 py-2 cell-dash">—</td>;
  if (v > 0) return <td className="px-3 py-2 cell-pos">{`+${v.toFixed(1)}%`}</td>;
  if (v < 0) return <td className="px-3 py-2 cell-neg">{`${v.toFixed(1)}%`}</td>;
  return <td className="px-3 py-2 cell-neutral">0.0%</td>;
}

function StatCell({ v, unit = "" }: { v: number | null; unit?: string }) {
  if (v == null) return <td className="px-3 py-2 cell-dash">—</td>;
  return <td className="px-3 py-2 cell-stat">{v.toFixed(1)}{unit}</td>;
}

function RsiCell({ v }: { v: number | null }) {
  if (v == null) return <td className="px-3 py-2 cell-dash">—</td>;
  const cls = v > 70 ? "cell-pos" : v < 30 ? "cell-neg" : "cell-stat";
  return <td className={`px-3 py-2 ${cls}`}>{v.toFixed(0)}</td>;
}

function SortHeader({ label, sortKey, current, asc, onClick }: {
  label: string; sortKey: SortKey; current: SortKey; asc: boolean;
  onClick: (k: SortKey) => void;
}) {
  const active = current === sortKey;
  return (
    <th
      className={`px-3 py-2.5 text-right text-xs cursor-pointer select-none whitespace-nowrap transition-colors ${
        active ? "text-white" : "text-slate-400 hover:text-slate-200"
      }`}
      onClick={() => onClick(sortKey)}
    >
      {label} {active ? (asc ? "▲" : "▼") : "↕"}
    </th>
  );
}

/* ── 메인 컴포넌트 ───────────────────────────── */
export default function ETFTable({ etfs }: { etfs: ETF[] }) {
  const [search, setSearch]   = useState("");
  const [cat, setCat]         = useState("전체");
  const [sortKey, setSortKey] = useState<SortKey>("vol_avg_억");
  const [asc, setAsc]         = useState(false);

  const filtered = useMemo(() => {
    let list = etfs;
    if (cat !== "전체") list = list.filter(e => e.category === cat);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(e => e.name.toLowerCase().includes(q) || e.ticker.includes(q));
    }
    return [...list].sort((a, b) => {
      const av = (a[sortKey] as number | null) ?? -Infinity;
      const bv = (b[sortKey] as number | null) ?? -Infinity;
      return asc ? av - bv : bv - av;
    });
  }, [etfs, cat, search, sortKey, asc]);

  function handleSort(k: SortKey) {
    if (k === sortKey) setAsc(!asc);
    else { setSortKey(k); setAsc(false); }
  }

  return (
    <section>
      {/* 필터 바 */}
      <div className="flex flex-wrap gap-3 mb-4 items-center">
        <input
          type="text"
          placeholder="ETF 이름 또는 코드 검색..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-500 w-56"
        />
        <div className="flex gap-1 flex-wrap">
          {CATEGORIES.map(c => (
            <button
              key={c}
              onClick={() => setCat(c)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                cat === c
                  ? "bg-white text-gray-900"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs text-gray-400">{filtered.length}개</span>
      </div>

      {/* 테이블 */}
      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-900 sticky top-0 border-b border-gray-700">
            <tr>
              <th className="px-3 py-2.5 text-left text-xs text-slate-400 w-8">#</th>
              <th className="px-3 py-2.5 text-left text-xs text-slate-400 min-w-[160px]">종목명</th>
              <th className="px-3 py-2.5 text-left text-xs text-slate-400 whitespace-nowrap">분류</th>
              <SortHeader label="현재가"    sortKey="price_last"  current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="1M수익"    sortKey="mom_1m"      current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="3M수익"    sortKey="mom_3m"      current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="변동성"    sortKey="vol_20d"     current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="샤프"      sortKey="sharpe"      current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="MDD"       sortKey="mdd"         current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="RSI"       sortKey="rsi"         current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="분배율"    sortKey="dist_yield"  current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="거래대금"  sortKey="vol_avg_억"  current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="AUM억"     sortKey="aum_억"      current={sortKey} asc={asc} onClick={handleSort} />
              <th className="px-3 py-2.5 text-xs text-slate-400">차트</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((etf, i) => (
              <tr
                key={etf.ticker}
                className={`border-b border-gray-800/60 hover:bg-gray-800/50 transition-colors ${
                  i % 2 === 0 ? "bg-gray-950/40" : "bg-gray-900/20"
                }`}
              >
                <td className="px-3 py-2.5 text-slate-500 text-xs">{i + 1}</td>
                <td className="px-3 py-2.5">
                  <Link href={`/etf/${etf.ticker}`} className="hover:text-blue-400 transition-colors">
                    <div className="etf-name">{etf.name}</div>
                    <div className="etf-ticker">{etf.ticker}</div>
                  </Link>
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap">
                  <span className={`text-xs font-medium ${CAT_COLOR[etf.category] ?? "text-gray-400"}`}>
                    {etf.category}
                  </span>
                </td>

                {/* 현재가 */}
                <td className="px-3 py-2.5 cell-price">
                  {etf.price_last > 0 ? etf.price_last.toLocaleString() : "—"}
                </td>

                <PctCell v={etf.mom_1m} />
                <PctCell v={etf.mom_3m} />
                <StatCell v={etf.vol_20d} unit="%" />

                {/* 샤프 */}
                {etf.sharpe == null
                  ? <td className="px-3 py-2.5 cell-dash">—</td>
                  : <td className={`px-3 py-2.5 cell-stat ${etf.sharpe >= 1 ? "!text-emerald-400" : etf.sharpe < 0 ? "!text-red-400" : ""}`}>
                      {etf.sharpe.toFixed(2)}
                    </td>
                }

                <PctCell v={etf.mdd} />
                <RsiCell v={etf.rsi} />

                {/* 분배율 */}
                <td className="px-3 py-2.5 cell-stat">
                  {etf.dist_yield > 0 ? `${etf.dist_yield.toFixed(2)}%` : <span className="cell-dash">—</span>}
                </td>

                <StatCell v={etf.vol_avg_억} />

                {/* AUM */}
                <td className="px-3 py-2.5 cell-stat">
                  {etf.aum_억 > 0 ? etf.aum_억.toFixed(0) : <span className="cell-dash">—</span>}
                </td>

                <td className="px-3 py-2.5 text-center">
                  <Link href={`/etf/${etf.ticker}`} className="text-slate-500 hover:text-blue-400 transition-colors text-xs">
                    📈
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
