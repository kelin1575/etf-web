import { promises as fs } from "fs";
import path from "path";
import Link from "next/link";
import CandleChart from "@/components/CandleChart";
import { notFound } from "next/navigation";

async function getEtfData(ticker: string) {
  const dataDir = path.join(process.cwd(), "public", "data");
  try {
    const [summaryRaw, pricesRaw] = await Promise.all([
      fs.readFile(path.join(dataDir, "etf_summary.json"), "utf-8"),
      fs.readFile(path.join(dataDir, "prices.json"), "utf-8"),
    ]);
    const summary = JSON.parse(summaryRaw);
    const prices  = JSON.parse(pricesRaw);
    const etf     = summary.etfs.find((e: { ticker: string }) => e.ticker === ticker);
    return { etf: etf ?? null, bars: prices.data?.[ticker] ?? [] };
  } catch {
    return { etf: null, bars: [] };
  }
}

function StatCard({ label, value, unit = "", color = "text-white" }: {
  label: string; value: string | number | null; unit?: string; color?: string;
}) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-3 text-center">
      <div className={`text-lg font-bold ${color}`}>
        {value != null ? `${value}${unit}` : "—"}
      </div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
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

export const revalidate = 3600;

export default async function ETFDetailPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const { etf, bars } = await getEtfData(ticker);

  if (!etf) return notFound();

  const mom1mColor  = (etf.mom_1m  ?? 0) >= 0 ? "text-red-400" : "text-blue-400";
  const mom3mColor  = (etf.mom_3m  ?? 0) >= 0 ? "text-red-400" : "text-blue-400";
  const rsiColor    = etf.rsi > 70 ? "text-red-400" : etf.rsi < 30 ? "text-blue-400" : "text-white";

  return (
    <div className="space-y-6">
      {/* 뒤로 가기 */}
      <Link href="/" className="text-sm text-gray-400 hover:text-white transition-colors">
        ← 전체 목록
      </Link>

      {/* 헤더 */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">{etf.name}</h1>
            <span className={`text-xs px-2 py-1 rounded-full ${CAT_COLOR[etf.category] ?? "bg-gray-700 text-gray-300"}`}>
              {etf.category}
            </span>
          </div>
          <p className="text-gray-400 text-sm">{ticker} · 기준일 {etf.updated}</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-white">{etf.price_last?.toLocaleString()}원</div>
          <div className={`text-sm font-medium ${mom1mColor}`}>
            1개월 {(etf.mom_1m ?? 0) >= 0 ? "+" : ""}{(etf.mom_1m ?? 0).toFixed(2)}%
          </div>
        </div>
      </div>

      {/* 지표 카드 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <StatCard label="1M 수익률" value={etf.mom_1m?.toFixed(1) ?? null} unit="%" color={mom1mColor} />
        <StatCard label="3M 수익률" value={etf.mom_3m?.toFixed(1) ?? null} unit="%" color={mom3mColor} />
        <StatCard label="변동성(연)" value={etf.vol_20d?.toFixed(1) ?? null} unit="%" />
        <StatCard label="샤프비율"  value={etf.sharpe?.toFixed(2) ?? null} />
        <StatCard label="MDD"       value={etf.mdd?.toFixed(1) ?? null} unit="%" color="text-blue-400" />
        <StatCard label="RSI(14)"   value={etf.rsi?.toFixed(0) ?? null} color={rsiColor} />
        <StatCard label="분배수익률" value={etf.dist_yield > 0 ? etf.dist_yield.toFixed(2) : null} unit="%" color="text-green-400" />
        <StatCard label="거래대금"  value={etf.vol_avg_억?.toFixed(0) ?? null} unit="억" />
      </div>

      {/* 캔들 차트 */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h2 className="text-sm font-semibold text-gray-300 mb-3">
          3개월 가격 흐름 (빨강 상승 · 파랑 하락)
        </h2>
        <CandleChart ticker={ticker} bars={bars} />
      </div>

      {/* 기본 정보 */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h2 className="text-sm font-semibold text-gray-300 mb-3">기본 정보</h2>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-3 text-sm">
          {[
            ["티커", ticker],
            ["분류", etf.category],
            ["순자산(AUM)", `${etf.aum_억?.toFixed(0) ?? "—"}억원`],
            ["현재가(NAV)", `${etf.nav?.toLocaleString() ?? "—"}원`],
          ].map(([k, v]) => (
            <div key={k}>
              <dt className="text-gray-500 text-xs">{k}</dt>
              <dd className="text-white font-medium mt-0.5">{v}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
