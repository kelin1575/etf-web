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

function PctCell({ v }: { v: number | null }) {
  if (v == null) return <td className="px-3 py-2 text-gray-600">—</td>;
  const color = v > 0 ? "text-red-400" : v < 0 ? "text-blue-400" : "text-gray-400";
  return <td className={`px-3 py-2 text-right font-mono ${color}`}>{v > 0 ? "+" : ""}{v.toFixed(1)}%</td>;
}

function NumCell({ v, unit = "" }: { v: number | null; unit?: string }) {
  if (v == null) return <td className="px-3 py-2 text-gray-600">—</td>;
  return <td className="px-3 py-2 text-right font-mono text-gray-300">{v.toFixed(1)}{unit}</td>;
}

function SortHeader({ label, sortKey, current, asc, onClick }: {
  label: string; sortKey: SortKey; current: SortKey; asc: boolean; onClick: (k: SortKey) => void;
}) {
  const active = current === sortKey;
  return (
    <th
      className="px-3 py-2 text-right text-xs text-gray-400 cursor-pointer hover:text-white select-none whitespace-nowrap"
      onClick={() => onClick(sortKey)}
    >
      {label} {active ? (asc ? "▲" : "▼") : "↕"}
    </th>
  );
}

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
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs text-gray-500">{filtered.length}개</span>
      </div>

      {/* 테이블 */}
      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-900 sticky top-0">
            <tr>
              <th className="px-3 py-2 text-left text-xs text-gray-400 w-8">#</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400 min-w-[160px]">종목명</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400 whitespace-nowrap">분류</th>
              <SortHeader label="현재가"    sortKey="price_last"  current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="1M수익"    sortKey="mom_1m"      current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="3M수익"    sortKey="mom_3m"      current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="변동성"    sortKey="vol_20d"     current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="샤프"      sortKey="sharpe"      current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="MDD"       sortKey="mdd"         current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="RSI"       sortKey="rsi"         current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="분배수익률" sortKey="dist_yield"  current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="거래대금억" sortKey="vol_avg_억"  current={sortKey} asc={asc} onClick={handleSort} />
              <SortHeader label="AUM억"     sortKey="aum_억"      current={sortKey} asc={asc} onClick={handleSort} />
              <th className="px-3 py-2 text-xs text-gray-400">차트</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {filtered.map((etf, i) => (
              <tr key={etf.ticker} className="hover:bg-gray-800/40 transition-colors">
                <td className="px-3 py-2 text-gray-600 text-xs">{i + 1}</td>
                <td className="px-3 py-2">
                  <Link href={`/etf/${etf.ticker}`} className="hover:text-blue-400 transition-colors">
                    <div className="etf-name">{etf.name}</div>
                    <div className="etf-ticker">{etf.ticker}</div>
                  </Link>
                </td>
                <td className="px-3 py-2 whitespace-nowrap">
                  <span className={`text-xs font-medium ${CAT_COLOR[etf.category] ?? "text-gray-400"}`}>
                    {etf.category}
                  </span>
                </td>
                <td className="px-3 py-2 text-right font-mono text-white text-xs">
                  {etf.price_last.toLocaleString()}
                </td>
                <PctCell v={etf.mom_1m} />
                <PctCell v={etf.mom_3m} />
                <NumCell v={etf.vol_20d} unit="%" />
                <NumCell v={etf.sharpe} />
                <PctCell v={etf.mdd} />
                <td className="px-3 py-2 text-right font-mono text-xs">
                  <span className={etf.rsi != null && etf.rsi > 70 ? "text-red-400" : etf.rsi != null && etf.rsi < 30 ? "text-blue-400" : "text-gray-300"}>
                    {etf.rsi?.toFixed(0) ?? "—"}
                  </span>
                </td>
                <td className="px-3 py-2 text-right font-mono text-gray-300 text-xs">
                  {etf.dist_yield > 0 ? `${etf.dist_yield.toFixed(2)}%` : "—"}
                </td>
                <NumCell v={etf.vol_avg_억} />
                <NumCell v={etf.aum_억} />
                <td className="px-3 py-2 text-center">
                  <Link
                    href={`/etf/${etf.ticker}`}
                    className="text-xs text-gray-500 hover:text-blue-400 transition-colors"
                  >
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
